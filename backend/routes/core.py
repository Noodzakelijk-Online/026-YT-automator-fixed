import hashlib
import json
import mimetypes
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from dateutil.parser import isoparse
from flask import Blueprint, current_app, jsonify, request, send_file
from PIL import Image, UnidentifiedImageError
from werkzeug.utils import secure_filename

from errors import ApiError
from extensions import db
from models import BatchJob, JobLog, Thumbnail, Transcript, UploadJob, User, VideoDraft, YouTubeAccount
from services.metadata_service import generate_metadata
from services.thumbnail_service import generate_thumbnail
from services.transcription_service import TranscriptionUnavailable, transcribe_video
from services.youtube_service import service_for


api_bp = Blueprint("api", __name__)
ALLOWED_EXTENSIONS = {"mp4", "mov", "m4v", "webm", "mkv", "avi"}
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png"}
PRIVACY = {"private", "unlisted", "public"}


def user():
    value = User.query.first()
    if not value:
        value = User(display_name="Local operator")
        db.session.add(value); db.session.commit()
    return value


def draft_or_404(draft_id):
    draft = db.session.get(VideoDraft, draft_id)
    if not draft:
        raise ApiError("Draft not found", 404, "not_found")
    return draft


def file_hash(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@api_bp.get("/health")
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()})


@api_bp.get("/readiness")
def readiness():
    checks = {"database": False, "oauth_configured": bool(current_app.config["GOOGLE_CLIENT_SECRETS_FILE"]),
              "ai_configured": bool(current_app.config["OPENAI_API_KEY"]),
              "token_encryption_configured": bool(current_app.config["TOKEN_ENCRYPTION_KEY"])}
    try:
        db.session.execute(db.text("SELECT 1")); checks["database"] = True
    except Exception:
        pass
    return jsonify({"status": "ready" if checks["database"] else "not_ready", "checks": checks}), (200 if checks["database"] else 503)


@api_bp.get("/settings")
def settings():
    return readiness()


@api_bp.post("/videos/validate")
def validate_video():
    file = request.files.get("video")
    if not file or not file.filename:
        raise ApiError("A video file is required", 400, "validation_error")
    extension = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    file.seek(0, os.SEEK_END); size = file.tell(); file.seek(0)
    if extension not in ALLOWED_EXTENSIONS:
        raise ApiError("Unsupported video type", 415, "unsupported_media_type", sorted(ALLOWED_EXTENSIONS))
    if size == 0 or size > current_app.config["MAX_CONTENT_LENGTH"]:
        raise ApiError("Video is empty or exceeds the configured upload limit", 413, "file_size_invalid")
    return jsonify({"valid": True, "filename": secure_filename(file.filename), "size": size})


@api_bp.post("/drafts")
def create_draft():
    file = request.files.get("video")
    if not file or not file.filename:
        raise ApiError("A video file is required", 400, "validation_error")
    extension = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if extension not in ALLOWED_EXTENSIONS:
        raise ApiError("Unsupported video type", 415, "unsupported_media_type")
    draft_id, filename = str(uuid4()), secure_filename(file.filename)
    path = Path(current_app.config["UPLOAD_FOLDER"]) / f"{draft_id}-{filename}"
    file.save(path)
    if path.stat().st_size == 0 or path.stat().st_size > current_app.config["MAX_CONTENT_LENGTH"]:
        path.unlink(missing_ok=True)
        raise ApiError("Video is empty or too large", 413, "file_size_invalid")
    checksum = file_hash(path)
    duplicate = VideoDraft.query.filter(VideoDraft.checksum == checksum, VideoDraft.status != "cancelled").first()
    if duplicate and request.form.get("allow_duplicate") != "true":
        path.unlink(missing_ok=True)
        raise ApiError("This exact video already exists", 409, "duplicate_video", {"draft_id": duplicate.id})
    title = Path(filename).stem.replace("_", " ").replace("-", " ")[:100]
    draft = VideoDraft(id=draft_id, user_id=user().id, filename=filename, file_path=str(path), file_size=path.stat().st_size,
                       mime_type=file.mimetype or mimetypes.guess_type(filename)[0], checksum=checksum, title=title)
    db.session.add(draft); db.session.commit()
    return jsonify({"draft": draft.to_dict()}), 201


@api_bp.get("/drafts")
def list_drafts():
    return jsonify({"drafts": [value.to_dict() for value in VideoDraft.query.order_by(VideoDraft.created_at.desc()).all()]})


@api_bp.get("/drafts/<draft_id>")
def get_draft(draft_id):
    draft = draft_or_404(draft_id)
    transcript = Transcript.query.filter_by(draft_id=draft_id).first()
    thumbnails = Thumbnail.query.filter_by(draft_id=draft_id).all()
    result = draft.to_dict()
    result["transcript"] = {"text": transcript.text, "status": transcript.status, "provider": transcript.provider,
                            "error": transcript.error} if transcript else None
    result["thumbnails"] = [{"id": t.id, "source": t.source, "selected": t.selected,
                             "upload_status": t.upload_status, "error": t.error,
                             "url": f"/api/thumbnails/{t.id}/file"} for t in thumbnails]
    return jsonify({"draft": result})


@api_bp.patch("/drafts/<draft_id>")
def update_draft(draft_id):
    draft, data = draft_or_404(draft_id), (request.get_json(silent=True) or {})
    for field in ("title", "description", "category_id", "playlist_id", "privacy_status"):
        if field in data:
            setattr(draft, field, data[field] or (None if field == "playlist_id" else ""))
    if len(draft.title) > 100 or len(draft.description) > 5000:
        raise ApiError("Title or description exceeds YouTube limits", 422, "validation_error")
    if draft.privacy_status not in PRIVACY:
        raise ApiError("Privacy must be private, unlisted, or public", 422, "validation_error")
    for field in ("tags", "hashtags", "seo_keywords"):
        if field in data:
            setattr(draft, f"{field}_json", json.dumps([str(v) for v in data[field]]))
    if len(",".join(json.loads(draft.tags_json))) > 500:
        raise ApiError("Combined tags exceed 500 characters", 422, "validation_error")
    if "scheduled_at" in data:
        draft.scheduled_at = isoparse(data["scheduled_at"]).astimezone(timezone.utc) if data["scheduled_at"] else None
    draft.manually_edited = True
    db.session.commit()
    return jsonify({"draft": draft.to_dict()})


@api_bp.post("/drafts/<draft_id>/metadata/generate")
def metadata(draft_id):
    draft = draft_or_404(draft_id)
    transcript = Transcript.query.filter_by(draft_id=draft_id).first()
    data = request.get_json(silent=True) or {}
    context = data.get("context") or (transcript.text if transcript else draft.title)
    result = generate_metadata(context, data.get("prompt"))
    draft.title, draft.description = result["title"], result["description"]
    draft.tags_json, draft.hashtags_json = json.dumps(result["tags"]), json.dumps(result.get("hashtags", []))
    draft.seo_keywords_json, draft.category_id = json.dumps(result.get("seo_keywords", [])), str(result.get("category_id", "22"))
    draft.metadata_source, draft.status = result["source"], "ready"
    db.session.commit()
    return jsonify({"metadata": result, "draft": draft.to_dict()})


@api_bp.post("/drafts/<draft_id>/transcript/generate")
def generate_transcript(draft_id):
    draft = draft_or_404(draft_id)
    transcript = Transcript.query.filter_by(draft_id=draft_id).first() or Transcript(draft_id=draft_id)
    try:
        transcript.text, transcript.provider, transcript.status, transcript.error = transcribe_video(draft.file_path), "openai-whisper", "ready", None
    except TranscriptionUnavailable as exc:
        transcript.status, transcript.error = "unavailable", str(exc)
        db.session.add(transcript); db.session.commit()
        raise ApiError(str(exc), 503, "transcription_unavailable")
    db.session.add(transcript); db.session.commit()
    return jsonify({"transcript": {"text": transcript.text, "status": transcript.status, "provider": transcript.provider}})


@api_bp.put("/drafts/<draft_id>/transcript")
def update_transcript(draft_id):
    draft_or_404(draft_id); data = request.get_json(silent=True) or {}
    transcript = Transcript.query.filter_by(draft_id=draft_id).first() or Transcript(draft_id=draft_id)
    transcript.text, transcript.provider, transcript.status, transcript.error = str(data.get("text", "")), "manual", "ready", None
    db.session.add(transcript); db.session.commit()
    return jsonify({"transcript": {"text": transcript.text, "status": transcript.status, "provider": transcript.provider}})


@api_bp.post("/drafts/<draft_id>/thumbnails/generate")
def generate_thumbnails(draft_id):
    draft = draft_or_404(draft_id)
    generated = []
    for style in ("modern", "bright", "bold"):
        temp_path = generate_thumbnail(draft.file_path, draft.title, style)
        target = Path(current_app.config["GENERATED_FOLDER"]) / f"{uuid4()}.jpg"
        shutil.move(temp_path, target)
        thumbnail = Thumbnail(draft_id=draft.id, file_path=str(target), source=f"generated:{style}")
        db.session.add(thumbnail); generated.append(thumbnail)
    db.session.commit()
    return jsonify({"thumbnails": [{"id": t.id, "url": f"/api/thumbnails/{t.id}/file", "source": t.source} for t in generated]}), 201


@api_bp.post("/drafts/<draft_id>/thumbnails")
def custom_thumbnail(draft_id):
    draft_or_404(draft_id); file = request.files.get("thumbnail")
    ext = file.filename.rsplit(".", 1)[-1].lower() if file and file.filename and "." in file.filename else ""
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ApiError("Thumbnail must be JPG or PNG", 415, "unsupported_media_type")
    target = Path(current_app.config["GENERATED_FOLDER"]) / f"{uuid4()}.{ext}"; file.save(target)
    if target.stat().st_size > 2 * 1024 * 1024:
        target.unlink(missing_ok=True)
        raise ApiError("YouTube thumbnails must be 2 MB or smaller", 413, "file_size_invalid")
    try:
        with Image.open(target) as image:
            image.verify()
    except (UnidentifiedImageError, OSError):
        target.unlink(missing_ok=True)
        raise ApiError("Thumbnail content is not a valid image", 415, "unsupported_media_type")
    thumbnail = Thumbnail(draft_id=draft_id, file_path=str(target), source="custom")
    db.session.add(thumbnail); db.session.commit()
    return jsonify({"thumbnail": {"id": thumbnail.id, "url": f"/api/thumbnails/{thumbnail.id}/file"}}), 201


@api_bp.post("/drafts/<draft_id>/thumbnails/<thumbnail_id>/select")
def select_thumbnail(draft_id, thumbnail_id):
    draft_or_404(draft_id)
    thumbnail = Thumbnail.query.filter_by(id=thumbnail_id, draft_id=draft_id).first()
    if not thumbnail: raise ApiError("Thumbnail not found", 404, "not_found")
    Thumbnail.query.filter_by(draft_id=draft_id).update({"selected": False}); thumbnail.selected = True; db.session.commit()
    return jsonify({"selected": thumbnail.id})


@api_bp.get("/thumbnails/<thumbnail_id>/file")
def thumbnail_file(thumbnail_id):
    thumbnail = db.session.get(Thumbnail, thumbnail_id)
    if not thumbnail: raise ApiError("Thumbnail not found", 404, "not_found")
    return send_file(thumbnail.file_path)


def validate_ready(draft):
    if not draft.title.strip(): raise ApiError("A title is required", 422, "draft_not_ready")
    if draft.youtube_video_id: raise ApiError("Draft has already been uploaded", 409, "already_uploaded")
    active = UploadJob.query.filter(UploadJob.draft_id == draft.id, UploadJob.status.in_(["queued", "scheduled", "uploading", "retry_pending"])).first()
    if active: raise ApiError("An active upload job already exists", 409, "duplicate_job", {"job_id": active.id})


@api_bp.post("/drafts/<draft_id>/jobs")
def create_job(draft_id):
    draft, data = draft_or_404(draft_id), (request.get_json(silent=True) or {})
    validate_ready(draft)
    run_at = isoparse(data["run_at"]).astimezone(timezone.utc) if data.get("run_at") else datetime.now(timezone.utc)
    status = "scheduled" if run_at > datetime.now(timezone.utc) else "queued"
    job = UploadJob(draft_id=draft.id, run_at=run_at, status=status, max_retries=current_app.config["JOB_MAX_RETRIES"])
    draft.status, draft.scheduled_at = status, run_at if status == "scheduled" else None
    db.session.add(job); db.session.commit()
    db.session.add(JobLog(job_id=job.id, event="created", message=f"Upload job {status}")); db.session.commit()
    return jsonify({"job": job.to_dict()}), 201


@api_bp.post("/batch-jobs")
def create_batch():
    ids = (request.get_json(silent=True) or {}).get("draft_ids", [])
    if not ids: raise ApiError("draft_ids is required", 422, "validation_error")
    batch = BatchJob(user_id=user().id, total_count=len(ids)); db.session.add(batch); db.session.flush()
    jobs = []
    for draft_id in ids:
        draft = draft_or_404(draft_id); validate_ready(draft)
        job = UploadJob(draft_id=draft.id, batch_id=batch.id, max_retries=current_app.config["JOB_MAX_RETRIES"])
        draft.status = "queued"; db.session.add(job); jobs.append(job)
    db.session.commit()
    return jsonify({"batch_id": batch.id, "jobs": [job.to_dict() for job in jobs]}), 201


@api_bp.get("/jobs")
def jobs():
    return jsonify({"jobs": [job.to_dict() for job in UploadJob.query.order_by(UploadJob.created_at.desc()).all()]})


@api_bp.get("/jobs/<job_id>")
def get_job(job_id):
    job = db.session.get(UploadJob, job_id)
    if not job: raise ApiError("Job not found", 404, "not_found")
    return jsonify({"job": job.to_dict(include_logs=True)})


@api_bp.post("/jobs/<job_id>/retry")
def retry(job_id):
    job = db.session.get(UploadJob, job_id)
    if not job or job.status != "failed": raise ApiError("Only failed jobs can be retried", 409, "invalid_job_state")
    job.status, job.run_at, job.last_error = "retry_pending", datetime.now(timezone.utc), None
    draft_or_404(job.draft_id).status = "retry_pending"; db.session.commit()
    return jsonify({"job": job.to_dict()})


@api_bp.post("/jobs/<job_id>/cancel")
def cancel(job_id):
    job = db.session.get(UploadJob, job_id)
    if not job or job.status not in {"queued", "scheduled", "retry_pending"}: raise ApiError("Job cannot be cancelled", 409, "invalid_job_state")
    job.status, job.cancelled_at = "cancelled", datetime.now(timezone.utc); draft_or_404(job.draft_id).status = "cancelled"; db.session.commit()
    return jsonify({"job": job.to_dict()})


@api_bp.get("/history")
def history():
    uploaded = VideoDraft.query.filter(VideoDraft.status.in_(["uploaded", "failed"])).order_by(VideoDraft.updated_at.desc()).all()
    return jsonify({"history": [draft.to_dict() for draft in uploaded]})
