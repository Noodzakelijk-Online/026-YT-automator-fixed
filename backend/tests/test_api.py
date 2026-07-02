import io


def create_draft(client, name="lesson.mp4", content=b"video-content"):
    response = client.post("/api/drafts", data={"video": (io.BytesIO(content), name)}, content_type="multipart/form-data")
    assert response.status_code == 201
    return response.get_json()["draft"]


def test_health_and_readiness(client):
    assert client.get("/api/health").get_json()["status"] == "healthy"
    response = client.get("/api/readiness")
    assert response.status_code == 200
    assert response.get_json()["checks"]["database"] is True


def test_cors_allows_configured_origin_only(client):
    allowed = client.get("/api/health", headers={"Origin": "http://localhost"})
    assert allowed.headers["Access-Control-Allow-Origin"] == "http://localhost"

    blocked = client.get("/api/health", headers={"Origin": "https://untrusted.example"})
    assert "Access-Control-Allow-Origin" not in blocked.headers


def test_auth_status_is_truthful(client):
    assert client.get("/api/auth/status").get_json() == {"authenticated": False, "channel": None}


def test_video_validation_and_error_contract(client):
    response = client.post("/api/videos/validate", data={"video": (io.BytesIO(b"bad"), "bad.txt")}, content_type="multipart/form-data")
    assert response.status_code == 415
    assert response.get_json()["error"]["code"] == "unsupported_media_type"


def test_draft_create_update_and_duplicate_prevention(client):
    draft = create_draft(client)
    response = client.patch(f"/api/drafts/{draft['id']}", json={"title": "A useful lesson", "privacy_status": "unlisted", "tags": ["lesson"]})
    assert response.get_json()["draft"]["manually_edited"] is True
    duplicate = client.post("/api/drafts", data={"video": (io.BytesIO(b"video-content"), "copy.mp4")}, content_type="multipart/form-data")
    assert duplicate.status_code == 409
    assert duplicate.get_json()["error"]["code"] == "duplicate_video"


def test_metadata_fallback_without_ai_key(client):
    draft = create_draft(client)
    response = client.post(f"/api/drafts/{draft['id']}/metadata/generate", json={"context": "Practical Flask deployment tutorial"})
    assert response.status_code == 200
    assert response.get_json()["draft"]["metadata_source"] == "fallback"


def test_job_create_status_cancel_and_retry_rules(client):
    draft = create_draft(client)
    response = client.post(f"/api/drafts/{draft['id']}/jobs", json={})
    assert response.status_code == 201
    job = response.get_json()["job"]
    assert client.get(f"/api/jobs/{job['id']}").get_json()["job"]["status"] == "queued"
    assert client.post(f"/api/jobs/{job['id']}/cancel").get_json()["job"]["status"] == "cancelled"
    retry = client.post(f"/api/jobs/{job['id']}/retry")
    assert retry.status_code == 409


def test_youtube_upload_service_with_mock(app, mocker):
    from models import VideoDraft, User
    from extensions import db
    from services import youtube_service
    with app.app_context():
        user = User(display_name="test"); db.session.add(user); db.session.flush()
        draft = VideoDraft(user_id=user.id, filename="a.mp4", file_path=__file__, file_size=1, checksum="x", title="Title")
        db.session.add(draft); db.session.commit()
        request = mocker.Mock(); request.next_chunk.return_value = (None, {"id": "real-id"})
        videos = mocker.Mock(); videos.insert.return_value = request
        youtube = mocker.Mock(); youtube.videos.return_value = videos
        mocker.patch.object(youtube_service, "service_for", return_value=youtube)
        response, warnings = youtube_service.upload_draft(draft)
        assert response["id"] == "real-id" and warnings == []


def test_playlist_service_with_mock(client, mocker):
    fake = mocker.Mock()
    fake.playlists.return_value.list.return_value.execute.return_value = {"items": [{"id": "p1", "snippet": {"title": "Uploads"}, "status": {"privacyStatus": "private"}, "contentDetails": {"itemCount": 2}}]}
    mocker.patch("routes.playlists.service_for", return_value=fake)
    response = client.get("/api/playlists")
    assert response.status_code == 200
    assert response.get_json()["playlists"][0]["id"] == "p1"
