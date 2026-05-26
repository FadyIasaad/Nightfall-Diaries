import os
import json
import glob
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from tbt_common import (
    get_spreadsheet,
    get_worksheet,
    get_all_values,
    find_header_map,
    find_first_row_by_status,
    update_cell,
    append_log,
    run_with_retry,
)


GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "").strip()
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()

YOUTUBE_TOKEN_JSON = os.getenv("YOUTUBE_TOKEN_JSON", "").strip()

CONTENT_WORKSHEET_NAME = os.getenv("CONTENT_WORKSHEET_NAME", "Content").strip()
LOGS_WORKSHEET_NAME = os.getenv("LOGS_WORKSHEET_NAME", "Logs").strip()

TARGET_STATUS = os.getenv("UPLOAD_TARGET_STATUS", "VIDEO_READY").strip()
UPLOADED_STATUS = os.getenv("UPLOADED_STATUS", "UPLOADED").strip()
FAILED_STATUS = os.getenv("FAILED_UPLOAD_STATUS", "FAILED_UPLOAD").strip()

PRIVACY_STATUS = os.getenv("YOUTUBE_PRIVACY_STATUS", "private").strip()
YOUTUBE_CATEGORY_ID = os.getenv("YOUTUBE_CATEGORY_ID", "15").strip()


def require_env(name: str, value: str) -> None:
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")


def validate_env() -> None:
    require_env("GOOGLE_SHEET_ID", GOOGLE_SHEET_ID)
    require_env("GOOGLE_SERVICE_ACCOUNT_JSON", GOOGLE_SERVICE_ACCOUNT_JSON)
    require_env("YOUTUBE_TOKEN_JSON", YOUTUBE_TOKEN_JSON)


def load_youtube_credentials() -> Credentials:
    try:
        token_data = json.loads(YOUTUBE_TOKEN_JSON)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            "YOUTUBE_TOKEN_JSON is not valid JSON. "
            "Copy the full JSON exactly from PowerShell into GitHub Secret."
        ) from e

    required = ["token", "refresh_token", "token_uri", "client_id", "client_secret", "scopes"]
    missing = [key for key in required if not token_data.get(key)]

    if missing:
        raise RuntimeError(
            "YOUTUBE_TOKEN_JSON is missing required fields: " + ", ".join(missing)
        )

    creds = Credentials(
        token=token_data["token"],
        refresh_token=token_data["refresh_token"],
        token_uri=token_data["token_uri"],
        client_id=token_data["client_id"],
        client_secret=token_data["client_secret"],
        scopes=token_data["scopes"],
    )

    if not creds.valid:
        print("YouTube credentials are not valid. Refreshing access token...")
        creds.refresh(Request())

    return creds


def get_youtube_service():
    creds = load_youtube_credentials()
    return build("youtube", "v3", credentials=creds)


def find_latest_mp4() -> str:
    files = glob.glob("output/*.mp4")

    if not files:
        raise FileNotFoundError("No MP4 video found inside output folder.")

    files.sort(key=lambda path: os.path.getmtime(path), reverse=True)
    return files[0]


def resolve_video_path(video_id, row, video_file_path_col):
    video_file_path = ""

    if video_file_path_col is not None:
        video_file_path = str(row[video_file_path_col] or "").strip()

    if video_file_path:
        print(f"Using video file from sheet: {video_file_path}")
        if os.path.exists(video_file_path):
            return video_file_path

        print(f"Video path from sheet does not exist in this runner: {video_file_path}")

    expected_path = f"output/tiny_brave_tails_{video_id}.mp4"
    if os.path.exists(expected_path):
        print(f"Using expected video path: {expected_path}")
        return expected_path

    latest = find_latest_mp4()
    print(f"Using latest MP4 found: {latest}")
    return latest


def build_description(description: str) -> str:
    description = (description or "").strip()

    if "#shorts" not in description.lower():
        description += "\n\n#shorts #animalstory #emotionalstory #lifelessons #tinybravetails"

    return description.strip()


def upload_video_to_youtube(video_path: str, title: str, description: str):
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file does not exist: {video_path}")

    youtube = get_youtube_service()

    title = (title or "Tiny Brave Tails").strip()[:100]
    description = build_description(description)

    request_body = {
        "snippet": {
            "title": title,
            "description": description,
            "categoryId": YOUTUBE_CATEGORY_ID,
            "tags": [
                "shorts",
                "animal story",
                "emotional story",
                "life lessons",
                "tiny brave tails",
            ],
        },
        "status": {
            "privacyStatus": PRIVACY_STATUS,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(
        video_path,
        chunksize=-1,
        resumable=True,
        mimetype="video/mp4",
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=media,
    )

    response = None

    while response is None:
        upload_status, response = run_with_retry(
            "Uploading YouTube chunk",
            lambda: request.next_chunk(),
            max_attempts=5,
        )

        if upload_status:
            print(f"Upload progress: {int(upload_status.progress() * 100)}%")

    youtube_video_id = response.get("id")

    if not youtube_video_id:
        raise RuntimeError(f"YouTube upload response missing video ID: {response}")

    print(f"YouTube upload complete. Video ID: {youtube_video_id}")
    return youtube_video_id, PRIVACY_STATUS


def main():
    validate_env()

    spreadsheet = get_spreadsheet(GOOGLE_SHEET_ID, GOOGLE_SERVICE_ACCOUNT_JSON)
    content_ws = get_worksheet(spreadsheet, CONTENT_WORKSHEET_NAME)
    logs_ws = get_worksheet(spreadsheet, LOGS_WORKSHEET_NAME)

    values = get_all_values(content_ws)

    if not values or len(values) < 2:
        raise RuntimeError("Content sheet has no data rows.")

    headers = values[0]
    header_map = find_header_map(headers)

    required_columns = ["id", "title", "description", "status"]
    missing_columns = [col for col in required_columns if col not in header_map]

    if missing_columns:
        raise RuntimeError("Missing required columns: " + ", ".join(missing_columns))

    row_number, row = find_first_row_by_status(values, header_map, TARGET_STATUS)

    if not row:
        print(f"No row with status {TARGET_STATUS}. Nothing to upload.")
        return

    id_col = header_map["id"]
    title_col = header_map["title"]
    description_col = header_map["description"]
    status_col = header_map["status"]

    video_file_path_col = header_map.get("video_file_path")
    youtube_status_col = header_map.get("youtube_status")
    youtube_video_id_col = header_map.get("youtube_video_id")
    video_url_col = header_map.get("video_url")
    error_message_col = header_map.get("error_message")

    video_id = str(row[id_col]).strip()
    title = str(row[title_col]).strip()
    description = str(row[description_col]).strip()

    try:
        video_path = resolve_video_path(video_id, row, video_file_path_col)
        youtube_video_id, privacy_status = upload_video_to_youtube(video_path, title, description)

        youtube_url = f"https://www.youtube.com/watch?v={youtube_video_id}"

        update_cell(content_ws, row_number, status_col + 1, UPLOADED_STATUS)

        if youtube_status_col is not None:
            update_cell(content_ws, row_number, youtube_status_col + 1, privacy_status)

        if youtube_video_id_col is not None:
            update_cell(content_ws, row_number, youtube_video_id_col + 1, youtube_video_id)

        if video_url_col is not None:
            update_cell(content_ws, row_number, video_url_col + 1, youtube_url)

        if error_message_col is not None:
            update_cell(content_ws, row_number, error_message_col + 1, "")

        append_log(logs_ws, ["UPLOAD_SUCCESS", video_id, youtube_url])

        print(f"Upload successful: {youtube_url}")

    except Exception as e:
        update_cell(content_ws, row_number, status_col + 1, FAILED_STATUS)

        if error_message_col is not None:
            update_cell(content_ws, row_number, error_message_col + 1, str(e)[:1000])

        append_log(logs_ws, ["UPLOAD_FAILED", video_id, str(e)[:1000]])
        raise


if __name__ == "__main__":
    main()
