from flask import Blueprint, jsonify, request

from errors import ApiError
from services.youtube_service import execute_with_retry, service_for


playlists_bp = Blueprint("playlists", __name__)


@playlists_bp.get("")
@playlists_bp.get("/")
def list_playlists():
    youtube = service_for()
    items, token = [], None
    while True:
        response = execute_with_retry(lambda: youtube.playlists().list(part="snippet,status,contentDetails", mine=True,
                                                                       maxResults=50, pageToken=token).execute())
        items.extend({"id": item["id"], "title": item["snippet"]["title"],
                      "description": item["snippet"].get("description", ""),
                      "privacy_status": item["status"]["privacyStatus"],
                      "video_count": item.get("contentDetails", {}).get("itemCount", 0)} for item in response.get("items", []))
        token = response.get("nextPageToken")
        if not token: break
    return jsonify({"playlists": items})


@playlists_bp.post("")
@playlists_bp.post("/")
def create_playlist():
    data = request.get_json(silent=True) or {}
    title, privacy = str(data.get("title", "")).strip(), data.get("privacy_status", "private")
    if not title: raise ApiError("Playlist title is required", 422, "validation_error")
    if privacy not in {"private", "unlisted", "public"}: raise ApiError("Invalid privacy status", 422, "validation_error")
    response = execute_with_retry(lambda: service_for().playlists().insert(part="snippet,status", body={
        "snippet": {"title": title, "description": str(data.get("description", ""))},
        "status": {"privacyStatus": privacy}}).execute())
    return jsonify({"playlist": {"id": response["id"], "title": response["snippet"]["title"],
                                  "privacy_status": response["status"]["privacyStatus"]}}), 201


@playlists_bp.get("/categories")
def categories():
    region = request.args.get("region", "US")
    response = execute_with_retry(lambda: service_for().videoCategories().list(part="snippet", regionCode=region).execute())
    return jsonify({"categories": [{"id": item["id"], "title": item["snippet"]["title"]}
                                    for item in response.get("items", []) if item["snippet"].get("assignable")]})

