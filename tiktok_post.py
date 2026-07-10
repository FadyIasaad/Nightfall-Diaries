"""
Auto-posts the most recently uploaded SHORT to TikTok via the official
Content Posting API (direct post).

Needs one GitHub Secret (skips silently if absent):
  TIKTOK_ACCESS_TOKEN   user access token with the video.publish scope

IMPORTANT: TikTok only allows PUBLIC direct posting after your developer app
passes their audit. Before the audit, posts land as private/self-only — still
useful for testing. Apply at developers.tiktok.com (Content Posting API).
If you prefer zero setup, a repost tool like Repurpose.io or Buffer can watch
the YouTube channel and cross-post automatically instead.
"""
import os
from pathlib import Path

import requests

from nd_common import (
    get_sheets_client,
    open_spreadsheet,
    get_worksheet,
    get_all_values,
    find_column,
    find_optional_column,
    get_cell,
)

API = "https://open.tiktokapis.com/v2"


def normalize_type(value):
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def find_latest_uploaded_short():
    client = get_sheets_client()
    spreadsheet = open_spreadsheet(client)
    sheet = get_worksheet(spreadsheet, "Content")
    values = get_all_values(sheet)
    if not values:
        return None
    headers = values[0]
    status_col = find_column(headers, "status")
    title_col = find_column(headers, "title")
    type_col = find_optional_column(headers, "video_type")
    path_col = find_optional_column(headers, "video_file_path")
    for row in reversed(values[1:]):
        status = (get_cell(row, status_col) or "").strip().upper()
        vtype = normalize_type(get_cell(row, type_col)) if type_col else ""
        if status == "UPLOADED" and vtype == "short":
            return {
                "title": (get_cell(row, title_col) or "").strip(),
                "video_path": (get_cell(row, path_col) or "").strip() if path_col else "",
            }
    return None


def main():
    token = os.getenv("TIKTOK_ACCESS_TOKEN", "").strip()
    if not token:
        print("TIKTOK_ACCESS_TOKEN not set. Skipping TikTok post.")
        return
    row = find_latest_uploaded_short()
    if not row or not row["video_path"]:
        print("No uploaded short with a local file found. Nothing to post.")
        return
    video_path = Path(row["video_path"])
    if not video_path.exists():
        print(f"Video file missing on disk: {video_path}. Nothing to post.")
        return
    size = video_path.stat().st_size
    try:
        init = requests.post(
            f"{API}/post/publish/video/init/",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={
                "post_info": {
                    "title": row["title"][:150],
                    "privacy_level": "SELF_ONLY",  # switch to PUBLIC_TO_EVERYONE after TikTok audits the app
                    "disable_duet": False,
                    "disable_comment": False,
                    "disable_stitch": False,
                },
                "source_info": {
                    "source": "FILE_UPLOAD",
                    "video_size": size,
                    "chunk_size": size,
                    "total_chunk_count": 1,
                },
            },
            timeout=60,
        )
        init.raise_for_status()
        data = init.json()["data"]
        upload_url = data["upload_url"]
        with open(video_path, "rb") as fh:
            up = requests.put(
                upload_url,
                headers={
                    "Content-Type": "video/mp4",
                    "Content-Range": f"bytes 0-{size - 1}/{size}",
                },
                data=fh,
                timeout=1800,
            )
        up.raise_for_status()
        print(f"TikTok upload accepted (publish_id: {data.get('publish_id')}).")
        print("Note: posts stay private until the TikTok app is audited for public posting.")
    except Exception as exc:
        print(f"TikTok post failed (non-fatal): {exc}")


if __name__ == "__main__":
    main()
