import json
import os
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from config import DEFAULT_PRIVACY_STATUS

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def _get_youtube_client():
    """Supports both old YOUTUBE_TOKEN_JSON and new Web OAuth secrets."""
    token_json = os.environ.get("YOUTUBE_TOKEN_JSON", "").strip()
    try:
        if token_json:
            info = json.loads(token_json)
            creds = Credentials.from_authorized_user_info(info, scopes=SCOPES)
        else:
            refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN", "").strip()
            client_id = os.environ.get("YOUTUBE_CLIENT_ID", "").strip()
            client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET", "").strip()
            if not (refresh_token and client_id and client_secret):
                raise RuntimeError("Missing YouTube OAuth secrets. Add YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN.")
            creds = Credentials(
                token=None,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=client_id,
                client_secret=client_secret,
                scopes=SCOPES,
            )
        if not creds.valid:
            if creds.refresh_token:
                print("Refreshing YouTube access token...")
                creds.refresh(Request())
            else:
                raise RuntimeError("YouTube credentials are invalid and no refresh token is available.")
        return build("youtube", "v3", credentials=creds, cache_discovery=False)
    except Exception as e:
        raise RuntimeError(f"YouTube authentication failed: {e}") from e


def upload_video(video_path, story_data):
    youtube = _get_youtube_client()
    body = {
        "snippet": {
            "title": story_data["title"][:100],
            "description": story_data["description"][:5000],
            "tags": story_data.get("tags", []),
            "categoryId": "1",
        },
        "status": {
            "privacyStatus": os.getenv("YOUTUBE_PRIVACY", DEFAULT_PRIVACY_STATUS),
            "selfDeclaredMadeForKids": True,
        },
    }
    media = MediaFileUpload(str(video_path), chunksize=8 * 1024 * 1024, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Upload progress: {int(status.progress() * 100)}%")
    video_id = response.get("id")
    if not video_id:
        raise RuntimeError(f"YouTube upload did not return a video id: {response}")
    verify = youtube.videos().list(part="snippet,status", id=video_id).execute()
    if not verify.get("items"):
        raise RuntimeError(f"Video id {video_id} was returned but cannot be verified on YouTube.")
    return video_id


def add_to_playlist(video_id, category):
    youtube = _get_youtube_client()
    playlist_map = json.loads(Path("playlist_map.json").read_text(encoding="utf-8"))
    playlist_id = playlist_map.get(category)
    if not playlist_id or str(playlist_id).startswith("PASTE_"):
        print(f"No playlist ID configured for {category}. Skipping playlist insert.")
        return
    youtube.playlistItems().insert(
        part="snippet",
        body={
            "snippet": {
                "playlistId": playlist_id,
                "resourceId": {"kind": "youtube#video", "videoId": video_id},
            }
        },
    ).execute()
