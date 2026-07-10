"""
Resets every story that was generated but never rendered/uploaded back to a
fresh IDEA, clearing the old script/scenes so the improved prompts write a
brand-new, better story from the same premise.

Resets rows with status GENERATED, and VIDEO_CREATED rows whose video file no
longer exists (GitHub runners are ephemeral, so those are stuck anyway).
Never touches UPLOADED rows.
"""
from pathlib import Path

from nd_common import (
    get_sheets_client,
    open_spreadsheet,
    get_worksheet,
    get_logs_worksheet,
    get_all_values,
    find_column,
    find_optional_column,
    get_cell,
    update_cell,
    update_optional,
    log,
)


def main():
    client = get_sheets_client()
    spreadsheet = open_spreadsheet(client)
    sheet = get_worksheet(spreadsheet, "Content")
    logs_sheet = get_logs_worksheet(spreadsheet)
    values = get_all_values(sheet)
    if not values:
        print("Content sheet is empty. Nothing to do.")
        return
    headers = values[0]
    id_col = find_column(headers, "id")
    title_col = find_column(headers, "title")
    script_col = find_column(headers, "script")
    description_col = find_column(headers, "description")
    status_col = find_column(headers, "status")
    created_at_col = find_column(headers, "created_at")
    scene_prompts_col = find_column(headers, "scene_prompts")
    image_status_col = find_column(headers, "image_status")
    audio_status_col = find_column(headers, "audio_status")
    path_col = find_optional_column(headers, "video_file_path")
    error_col = find_optional_column(headers, "error_message")

    reset_count = 0
    for row_number, row in enumerate(values[1:], start=2):
        status = (get_cell(row, status_col) or "").strip().upper()
        if status == "VIDEO_CREATED":
            video_path = (get_cell(row, path_col) or "").strip() if path_col else ""
            if video_path and Path(video_path).exists():
                continue  # a real file is waiting to upload; leave it
        elif status != "GENERATED":
            continue
        row_id = get_cell(row, id_col) or f"row{row_number}"
        update_cell(sheet, row_number, status_col, "IDEA")
        update_cell(sheet, row_number, title_col, "")
        update_cell(sheet, row_number, script_col, "")
        update_cell(sheet, row_number, description_col, "")
        update_cell(sheet, row_number, scene_prompts_col, "")
        update_cell(sheet, row_number, created_at_col, "")
        update_cell(sheet, row_number, image_status_col, "")
        update_cell(sheet, row_number, audio_status_col, "")
        update_optional(sheet, row_number, error_col, "")
        reset_count += 1
        print(f"Reset {row_id} ({status}) -> IDEA")

    log(logs_sheet, "-", "CLEANUP_STORIES", f"Reset {reset_count} stale stories back to IDEA")
    print(f"Done. {reset_count} stories reset to IDEA; they will be rewritten with the new prompts.")


if __name__ == "__main__":
    main()
