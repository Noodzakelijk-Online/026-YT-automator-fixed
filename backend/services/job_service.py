import json
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from extensions import db
from models import JobLog, UploadJob, VideoDraft
from services.youtube_service import YouTubeError, upload_draft


def log(job, event, message, level="info", details=None):
    db.session.add(JobLog(job_id=job.id, event=event, message=message, level=level,
                          details_json=json.dumps(details) if details else None))
    db.session.commit()


def claim_next_job(worker_id=None):
    worker_id = worker_id or str(uuid4())
    now = datetime.now(timezone.utc)
    job = (UploadJob.query.filter(UploadJob.status.in_(["queued", "scheduled", "retry_pending"]),
                                  UploadJob.run_at <= now).order_by(UploadJob.run_at).with_for_update(skip_locked=True).first())
    if not job:
        return None
    job.status, job.locked_at, job.worker_id = "uploading", now, worker_id
    VideoDraft.query.get(job.draft_id).status = "uploading"
    db.session.commit()
    log(job, "claimed", f"Job claimed by worker {worker_id}")
    return job


def process_job(job):
    draft = VideoDraft.query.get(job.draft_id)
    def progress(value):
        job.progress = value
        db.session.commit()
    try:
        response, warnings = upload_draft(draft, progress)
        draft.youtube_video_id = response["id"]
        draft.youtube_url = f"https://www.youtube.com/watch?v={response['id']}"
        draft.upload_response_json = json.dumps(response)
        draft.status, job.status, job.progress = "uploaded", "uploaded", 100
        job.completed_at = datetime.now(timezone.utc)
        db.session.commit()
        log(job, "uploaded", "YouTube confirmed the video upload", details={"video_id": response["id"]})
        for warning in warnings:
            log(job, "post_upload_warning", warning, "warning")
    except YouTubeError as exc:
        job.retry_count += 1
        job.last_error = str(exc)
        if exc.recoverable and job.retry_count <= job.max_retries:
            job.status, draft.status = "retry_pending", "retry_pending"
            job.run_at = datetime.now(timezone.utc) + timedelta(minutes=2 ** job.retry_count)
            log(job, "retry_scheduled", str(exc), "warning")
        else:
            job.status = draft.status = "failed"
            log(job, "failed", str(exc), "error", {"code": exc.code})
        db.session.commit()
    except Exception as exc:
        job.last_error, job.status, draft.status = str(exc), "failed", "failed"
        db.session.commit()
        log(job, "failed", "Unexpected upload failure", "error", {"type": type(exc).__name__})
