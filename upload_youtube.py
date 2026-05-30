import json
import os
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from tbt_common import (
    find_column,
    get_all_values,
    get_cell,
    get_sheets_client,
    get_worksheet,
    log,
    open_spreadsheet,
    require_env,
    update_cell,
)

CONTENT_SHEET_NAME = "Content"
LOGS_SHEET_NAME = "Logs"
OUTPUT_DIR = Path("output")
YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def get_youtube_service():
    credentials = Credentials(
        token=None,
        refresh_token=require_env("YOUTUBE_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=require_env("YOUTUBE_CLIENT_ID"),
        client_secret=require_env("YOUTUBE_CLIENT_SECRET"),
        scopes=YOUTUBE_SCOPES,
    )
    return build("youtube", "v3", credentials=credentials)


def find_video_for_id(video_id):
    safe_id = str(video_id).strip()
    candidates = list(OUTPUT_DIR.glob(f"*{safe_id}*.mp4")) if safe_id else []
    if not candidates:
        candidates = list(OUTPUT_DIR.glob("*.mp4"))
    if not candidates:
        raise FileNotFoundError("No MP4 video found inside output folder.")
    candidates.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    print(f"Using video file: {candidates[0]}")
    return candidates[0]


def upload_video_to_youtube(video_path, title, description):
    youtube = get_youtube_service()
    request_body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "categoryId": "1",
        },
        "status": {
            "privacyStatus": os.getenv("YOUTUBE_PRIVACY", "private"),
            "selfDeclaredMadeForKids": False,
        },
    }
    media = MediaFileUpload(str(video_path), resumable=True, chunksize=1024 * 1024)
    request = youtube.videos().insert(part="snippet,status", body=request_body, media_body=media)
    response = None
    while response is None:
        upload_status, response = request.next_chunk()
        if upload_status:
            print(f"Upload progress: {int(upload_status.progress() * 100)}%")
    if "id" not in response:
        raise RuntimeError(f"YouTube upload did not return a video id: {response}")
    return response["id"]


def main():
    sheets_client = get_sheets_client()
    spreadsheet = open_spreadsheet(sheets_client)
    content_sheet = get_worksheet(spreadsheet, CONTENT_SHEET_NAME)
    logs_sheet = get_worksheet(spreadsheet, LOGS_SHEET_NAME)
    values = get_all_values(content_sheet)
    if not values:
        raise ValueError("Content sheet is empty.")
    headers = values[0]
    id_col = find_column(headers, "id")
    title_col = find_column(headers, "title")
    description_col = find_column(headers, "description")
    status_col = find_column(headers, "status")
    youtube_status_col = find_column(headers, "youtube_status")
    youtube_video_id_col = find_column(headers, "youtube_video_id")
    video_url_col = find_column(headers, "video_url")

    target_row_number, target_row = None, None
    for index, row in enumerate(values[1:], start=2):
        if get_cell(row, status_col).upper() == "VIDEO_CREATED" and get_cell(row, youtube_status_col).upper() != "UPLOADED_PRIVATE":
            target_row_number, target_row = index, row
            break
    if target_row_number is None:
        log(logs_sheet, "", "UPLOAD_YOUTUBE", "No VIDEO_CREATED row waiting for upload.")
        print("No VIDEO_CREATED row waiting for upload.")
        return

    video_id = get_cell(target_row, id_col)
    title = get_cell(target_row, title_col)
    description = get_cell(target_row, description_col) or (
        "A soft emotional animal bedtime story with a tiny life lesson.\n\n"
        "#shorts #bedtimestory #animalstory #emotionalstory #tinybravetails"
    )
    if not title:
        raise ValueError(f"Missing title in row {target_row_number}")
    video_path = find_video_for_id(video_id)
    youtube_video_id = upload_video_to_youtube(video_path, title, description)
    youtube_url = f"https://youtu.be/{youtube_video_id}"
    update_cell(content_sheet, target_row_number, youtube_status_col, "UPLOADED_PRIVATE")
    update_cell(content_sheet, target_row_number, youtube_video_id_col, youtube_video_id)
    update_cell(content_sheet, target_row_number, video_url_col, youtube_url)
    update_cell(content_sheet, target_row_number, status_col, "UPLOADED")
    log(logs_sheet, video_id, "UPLOAD_YOUTUBE", f"Uploaded private video: {youtube_url}")
    print(f"Uploaded successfully: {youtube_url}")


if __name__ == "__main__":
    main()
