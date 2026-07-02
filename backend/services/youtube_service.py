import json
import random
import time

from flask import current_app
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from extensions import db
from models import Thumbnail, YouTubeAccount
from security import decrypt_token, encrypt_token


SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]


class YouTubeError(RuntimeError):
    def __init__(self, message, recoverable=False, code="youtube_error"):
        super().__init__(message)
        self.recoverable, self.code = recoverable, code


def credentials_for(account):
    creds = Credentials.from_authorized_user_info(json.loads(decrypt_token(account.token_encrypted)), SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        account.token_encrypted = encrypt_token(creds.to_json())
        account.token_expiry = creds.expiry
        db.session.commit()
    if not creds.valid:
        raise YouTubeError("Google authorization is expired or revoked", code="reauthorization_required")
    return creds


def service_for(account=None):
    account = account or YouTubeAccount.query.filter_by(revoked_at=None).first()
    if not account:
        raise YouTubeError("Connect a YouTube account first", code="authentication_required")
    return build("youtube", "v3", credentials=credentials_for(account), cache_discovery=False)


def classify_http_error(exc):
    status = getattr(exc.resp, "status", None)
    content = exc.content.decode("utf-8", errors="replace") if getattr(exc, "content", None) else str(exc)
    if status in (429, 500, 502, 503, 504):
        return YouTubeError(content, recoverable=True, code="youtube_temporarily_unavailable")
    if status == 401:
        return YouTubeError("Google authorization is invalid or revoked", code="reauthorization_required")
    if status == 403 and "quota" in content.lower():
        return YouTubeError("YouTube API quota is exhausted", code="quota_exceeded")
    return YouTubeError(content)


def execute_with_retry(callable_, attempts=4):
    for attempt in range(attempts):
        try:
            return callable_()
        except HttpError as exc:
            error = classify_http_error(exc)
            if not error.recoverable or attempt == attempts - 1:
                raise error from exc
            time.sleep(min(2 ** attempt + random.random(), 8))


def upload_draft(draft, progress_callback=None):
    youtube = service_for()
    body = {"snippet": {"title": draft.title, "description": draft.description,
                         "tags": json.loads(draft.tags_json), "categoryId": draft.category_id},
            "status": {"privacyStatus": draft.privacy_status, "selfDeclaredMadeForKids": False}}
    media = MediaFileUpload(draft.file_path, mimetype=draft.mime_type or "video/*", chunksize=8 * 1024 * 1024, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        try:
            status, response = request.next_chunk()
        except HttpError as exc:
            raise classify_http_error(exc) from exc
        if status and progress_callback:
            progress_callback(max(1, min(99, int(status.progress() * 100))))
    video_id = response["id"]
    thumbnail = Thumbnail.query.filter_by(draft_id=draft.id, selected=True).first()
    warnings = []
    if thumbnail:
        try:
            execute_with_retry(lambda: youtube.thumbnails().set(videoId=video_id,
                media_body=MediaFileUpload(thumbnail.file_path, mimetype="image/jpeg")).execute())
            thumbnail.upload_status = "uploaded"
        except YouTubeError as exc:
            thumbnail.upload_status, thumbnail.error = "failed", str(exc)
            warnings.append(f"Thumbnail upload failed: {exc}")
    if draft.playlist_id:
        try:
            execute_with_retry(lambda: youtube.playlistItems().insert(part="snippet", body={"snippet": {
                "playlistId": draft.playlist_id, "resourceId": {"kind": "youtube#video", "videoId": video_id}}}).execute())
        except YouTubeError as exc:
            warnings.append(f"Playlist assignment failed: {exc}")
    return response, warnings


def channel_info(youtube):
    response = execute_with_retry(lambda: youtube.channels().list(part="id,snippet,statistics", mine=True).execute())
    if not response.get("items"):
        raise YouTubeError("No YouTube channel was found for this Google account")
    item = response["items"][0]
    return {"id": item["id"], "title": item["snippet"]["title"],
            "thumbnail": item["snippet"].get("thumbnails", {}).get("default", {}).get("url"),
            "statistics": item.get("statistics", {})}

