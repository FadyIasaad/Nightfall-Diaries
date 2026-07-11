"""
Auto-posts the most recently uploaded video to a Facebook Page.
Shorts are published as Reels (the video file itself); long-form videos are
posted as a link post pointing at YouTube.

Needs two GitHub Secrets (skips silently if absent, so the pipeline never
breaks while Facebook isn't set up yet):
  FB_PAGE_ID            the numeric Page id
  FB_PAGE_ACCESS_TOKEN  a long-lived Page access token with
                        pages_manage_posts + pages_read_engagement
"""
import os
import time
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

GRAPH = "https://graph.facebook.com/v19.0"


def normalize_type(value):
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def find_latest_uploaded_row():
    client = get_sheets_client()
    spreadsheet = open_spreadsheet(client)
    sheet = get_worksheet(spreadsheet, "Content")
    values = get_all_values(sheet)
    if not values:
        return None
    headers = values[0]
    status_col = find_column(headers, "status")
    title_col = find_column(headers, "title")
    url_col = find_column(headers, "video_url")
    type_col = find_optional_column(headers, "video_type")
    path_col = find_optional_column(headers, "video_file_path")
    for row in reversed(values[1:]):
        if (get_cell(row, status_col) or "").strip().upper() == "UPLOADED":
            return {
                "title": (get_cell(row, title_col) or "").strip(),
                "url": (get_cell(row, url_col) or "").strip(),
                "video_type": normalize_type(get_cell(row, type_col)) if type_col else "",
                "video_path": (get_cell(row, path_col) or "").strip() if path_col else "",
            }
    return None


def post_link(page_id, token, title, url):
    r = requests.post(
        f"{GRAPH}/{page_id}/feed",
        data={
            "message": (
                f"{title}\n\n"
                f"🎬 Watch the FULL video on YouTube:\n"
                f"👉 {url}"
            ),
            "link": url,
            "access_token": token,
        },
        timeout=60,
    )
    if not r.ok:
        raise RuntimeError(f"feed {r.status_code}: {r.text[:400]}")
    print(f"Facebook link post created: {r.json().get('id')}")


def post_video(page_id, token, title, url, video_path):
    """Regular Page video post — works even where the Reels API is restricted."""
    with open(video_path, "rb") as fh:
        r = requests.post(
            f"{GRAPH}/{page_id}/videos",
            data={
                "description": (
                    f"{title}\n\n"
                    f"🎬 This is just the beginning — watch the FULL story on YouTube:\n"
                    f"👉 {url}\n\n"
                    f"#shorts #horrorstories #nightfalldiaries"
                ),
                "access_token": token,
            },
            files={"source": ("video.mp4", fh, "video/mp4")},
            timeout=1800,
        )
    if not r.ok:
        raise RuntimeError(f"{r.status_code}: {r.text[:400]}")
    print(f"Facebook video post created: {r.json().get('id')}")


def post_reel(page_id, token, title, url, video_path):
    size = video_path.stat().st_size
    start = requests.post(
        f"{GRAPH}/{page_id}/video_reels",
        data={"upload_phase": "start", "access_token": token},
        timeout=60,
    )
    if not start.ok:
        raise RuntimeError(f"reel start {start.status_code}: {start.text[:400]}")
    video_id = start.json()["video_id"]
    upload_url = start.json()["upload_url"]
    with open(video_path, "rb") as fh:
        up = requests.post(
            upload_url,
            headers={
                "Authorization": f"OAuth {token}",
                "offset": "0",
                "file_size": str(size),
            },
            data=fh,
            timeout=1800,
        )
    up.raise_for_status()
    fin = requests.post(
        f"{GRAPH}/{page_id}/video_reels",
        data={
            "upload_phase": "finish",
            "video_id": video_id,
            "video_state": "PUBLISHED",
            "description": (
                f"{title}\n\n"
                f"🎬 This is just the beginning — watch the FULL story on YouTube:\n"
                f"👉 {url}\n\n"
                f"#shorts #horrorstories #nightfalldiaries"
            ),
            "access_token": token,
        },
        timeout=120,
    )
    fin.raise_for_status()
    print(f"Facebook Reel published: {video_id}")


def main():
    page_id = os.getenv("FB_PAGE_ID", "").strip()
    token = os.getenv("FB_PAGE_ACCESS_TOKEN", "").strip()
    if not page_id or not token:
        print("FB_PAGE_ID / FB_PAGE_ACCESS_TOKEN not set. Skipping Facebook post.")
        return
    # Self-diagnosis: whose token is this? If it's a USER token (a very easy
    # mistake to make in Graph Explorer), exchange it for the PAGE token —
    # posting to the page with a user token is what causes the 400s.
    try:
        me = requests.get(f"{GRAPH}/me", params={"fields": "id,name", "access_token": token}, timeout=30)
        print(f"Token identity check: {me.status_code} {me.text[:200]}")
        if me.ok and str(me.json().get("id")) != str(page_id):
            print("Token belongs to a user, not the page. Fetching managed pages...")
            acc = requests.get(f"{GRAPH}/me/accounts", params={"access_token": token}, timeout=30)
            if acc.ok:
                pages = acc.json().get("data", [])
                print(f"Managed pages: {[(p.get('id'), p.get('name')) for p in pages]}")
                if pages:
                    page = next((p for p in pages if str(p.get("id")) == str(page_id)), pages[0])
                    page_id = str(page["id"])
                    token = page["access_token"]
                    print(f"Using page '{page.get('name')}' (real id {page_id}) with its own Page token.")
                else:
                    print("No managed pages returned; continuing with original settings.")
            else:
                print(f"me/accounts failed ({acc.status_code}: {acc.text[:300]}). Continuing with original settings.")
    except Exception as exc:
        print(f"Token identity check skipped: {exc}")

    row = find_latest_uploaded_row()
    if not row or not row["url"]:
        print("No uploaded video found in the sheet. Nothing to post.")
        return
    video_path = Path(row["video_path"]) if row["video_path"] else None
    # Fallback chain: Reel -> regular video post -> link post. Something always
    # lands on the page even if the Reels API is restricted for this app.
    try:
        if row["video_type"] == "short" and video_path and video_path.exists():
            try:
                post_reel(page_id, token, row["title"], row["url"], video_path)
            except Exception as exc:
                print(f"Reel failed ({exc}); falling back to regular video post.")
                post_video(page_id, token, row["title"], row["url"], video_path)
        else:
            post_link(page_id, token, row["title"], row["url"])
    except Exception as exc:
        print(f"Facebook post failed ({exc}); last resort: link post.")
        try:
            post_link(page_id, token, row["title"], row["url"])
        except Exception as exc2:
            # Never break the pipeline over a social post.
            print(f"Facebook link post also failed (non-fatal): {exc2}")


if __name__ == "__main__":
    main()
