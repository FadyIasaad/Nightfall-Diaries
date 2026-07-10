"""
Funnel short: turns scene 1 of the most recent UPLOADED long-form video into a
YouTube Short that ends on "the full story is on the channel", with the long
video's URL at the top of the description. The new row is written to the sheet
as a normal GENERATED short, so generate_video.py + upload_youtube.py handle
the rest of the pipeline unchanged.

Run via GitHub Actions workflow "07 - Funnel Short" (or locally with the same
environment variables as generate_story.py).
"""
import json
import re

from nd_common import (
    get_sheets_client,
    open_spreadsheet,
    get_worksheet,
    get_logs_worksheet,
    get_all_values,
    find_column,
    find_optional_column,
    get_cell,
    append_row,
    log,
    utc_now,
)

CONTENT_SHEET_NAME = "Content"
LONG_TYPES = {"horror_story", "confession_story"}
FUNNEL_SUFFIX = "_funnel"

# Spoken closer added as the short's final shot. Calm, on-brand, and it tells
# the viewer exactly where to go.
CLOSER_NARRATION = (
    "And that was only the beginning. The full story is on the channel — "
    "and if it keeps you up, a like and a subscribe brings you another."
)


def build_sheet_row(headers, assignments):
    row = [""] * len(headers)
    for col, value in assignments:
        if col:
            row[col - 1] = str(value)
    return row


def normalize_type(value):
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def main():
    client = get_sheets_client()
    spreadsheet = open_spreadsheet(client)
    content_sheet = get_worksheet(spreadsheet, CONTENT_SHEET_NAME)
    logs_sheet = get_logs_worksheet(spreadsheet)
    values = get_all_values(content_sheet)
    if not values:
        raise ValueError("Content sheet is empty.")
    headers = values[0]

    id_col = find_column(headers, "id")
    topic_col = find_column(headers, "topic")
    characters_col = find_column(headers, "characters")
    theme_col = find_column(headers, "theme")
    title_col = find_column(headers, "title")
    script_col = find_column(headers, "script")
    description_col = find_column(headers, "description")
    status_col = find_column(headers, "status")
    created_at_col = find_column(headers, "created_at")
    scene_prompts_col = find_column(headers, "scene_prompts")
    image_status_col = find_column(headers, "image_status")
    audio_status_col = find_column(headers, "audio_status")
    youtube_status_col = find_column(headers, "youtube_status")
    youtube_video_id_col = find_column(headers, "youtube_video_id")
    video_url_col = find_column(headers, "video_url")
    video_type_col = find_optional_column(headers, "video_type")
    target_minutes_col = find_optional_column(headers, "target_minutes")
    audience_col = find_optional_column(headers, "audience")
    made_for_kids_col = find_optional_column(headers, "made_for_kids")
    error_message_col = find_optional_column(headers, "error_message")

    existing_ids = {get_cell(row, id_col) for row in values[1:]}

    # Most recent long-form row that is UPLOADED with a real URL, newest first,
    # skipping any long video that already has a funnel short.
    source = None
    for row in reversed(values[1:]):
        status = (get_cell(row, status_col) or "").strip().upper()
        vtype = normalize_type(get_cell(row, video_type_col)) if video_type_col else ""
        url = (get_cell(row, video_url_col) or "").strip()
        row_id = (get_cell(row, id_col) or "").strip()
        if status == "UPLOADED" and vtype in LONG_TYPES and url and row_id:
            if f"{row_id}{FUNNEL_SUFFIX}" in existing_ids:
                print(f"Skipping {row_id}: funnel short already exists.")
                continue
            source = row
            break
    if source is None:
        print("No uploaded long-form video without a funnel short found. Nothing to do.")
        return

    long_id = get_cell(source, id_col).strip()
    long_title = (get_cell(source, title_col) or "").strip()
    long_url = (get_cell(source, video_url_col) or "").strip()
    payload_raw = get_cell(source, scene_prompts_col) or ""
    try:
        payload = json.loads(payload_raw)
    except Exception as exc:
        raise ValueError(f"Row {long_id}: scene_prompts is not valid JSON: {exc}")

    scenes = payload.get("scenes") or []
    if not scenes:
        raise ValueError(f"Row {long_id}: no scenes in scene_prompts.")
    scene1 = dict(scenes[0])
    shots = list(scene1.get("shots") or [])[:4]
    if not shots:
        raise ValueError(f"Row {long_id}: scene 1 has no shots.")

    # Closer shot: reuse the final shot's visual so no extra image is needed.
    closer = dict(shots[-1])
    closer["shot_number"] = len(shots) + 1
    closer["narration_en"] = CLOSER_NARRATION
    closer["subtitle_en"] = "The full story is on the channel."
    closer["emotion"] = "mystery"
    closer["camera_motion"] = "slow_zoom_out"
    shots.append(closer)
    scene1["shots"] = shots
    scene1["scene_number"] = 1

    short_payload = {
        "title": long_title[:95] or "The beginning of the story",
        "thumbnail_text": str(payload.get("thumbnail_text", "") or "").strip(),
        "description": "",
        "video_type": "short",
        "target_minutes": 1,
        "emotional_arc": payload.get("emotional_arc", ""),
        "scenes": [scene1],
    }

    description = (
        f"This is only the beginning — watch the FULL story here: {long_url}\n\n"
        "#Shorts #nightfalldiaries #scarystories"
    )
    script_text = " ".join(
        str(sh.get("narration_en", "")).strip() for sh in shots if sh.get("narration_en")
    )
    funnel_id = f"{long_id}{FUNNEL_SUFFIX}"

    new_row = build_sheet_row(headers, [
        (id_col, funnel_id),
        (topic_col, get_cell(source, topic_col)),
        (characters_col, get_cell(source, characters_col)),
        (theme_col, get_cell(source, theme_col)),
        (title_col, short_payload["title"]),
        (script_col, script_text[:45000]),
        (description_col, description),
        (scene_prompts_col, json.dumps(short_payload, ensure_ascii=False)[:45000]),
        (status_col, "GENERATED"),
        (created_at_col, utc_now()),
        (image_status_col, "PENDING"),
        (audio_status_col, "PENDING"),
        (youtube_status_col, ""),
        (youtube_video_id_col, ""),
        (video_type_col, "short"),
        (target_minutes_col, "1"),
        (audience_col, "general audience"),
        (made_for_kids_col, "FALSE"),
        (error_message_col, ""),
    ])
    append_row(content_sheet, new_row)
    log(logs_sheet, funnel_id, "FUNNEL_SHORT", f"Created funnel short from {long_id}: {long_title} -> {long_url}")
    print(f"Funnel short row created: {funnel_id} (from '{long_title}')")
    print("Next: generate_video.py renders it, upload_youtube.py publishes it.")


if __name__ == "__main__":
    main()
