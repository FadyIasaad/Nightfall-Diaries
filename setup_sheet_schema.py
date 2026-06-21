from nd_common import get_sheets_client, open_spreadsheet, get_worksheet, get_all_values, update_cell, run_with_retry

CONTENT_SHEET_NAME = "Content"
LOGS_SHEET_NAME = "Logs"

REQUIRED_HEADERS = [
    "id", "topic", "characters", "theme", "video_type", "target_minutes", "narrator_pov", "setting", "audience", "made_for_kids",
    "script", "title", "description", "status", "video_url", "created_at", "scene_prompts", "image_status", "audio_status",
    "youtube_status", "youtube_video_id", "video_file_path", "error_message", "thumbnail_path"
]

STARTER_ROWS = [
    ["ND-HOR-001", "A woman house-sitting a remote cabin notices the photos on the wall change slightly each night",
     "the house-sitter, the absent owners", "what you stop questioning becomes what controls you", "horror_story", 18,
     "an anonymous adult narrator, calm and a little tired", "a remote cabin in the woods", "general audience", "FALSE",
     "", "", "", "IDEA", "", "", "", "", "", "", "", "", "", ""],
    ["ND-CONF-001", "A woman spends a year quietly building the case that ends her husband's affair and his career in the same week",
     "the narrator, her husband, his coworker", "patience can be its own kind of justice", "confession_story", 16,
     "the woman herself, calm and exact, telling it after the fact", "a quiet suburban home", "general audience", "FALSE",
     "", "", "", "IDEA", "", "", "", "", "", "", "", "", "", ""],
    ["ND-SH-001", "A woman gets a porch-camera notification from a doorbell that was unplugged three years ago",
     "the narrator", "some things don't stop just because you disconnect them", "short", 1,
     "an anonymous adult narrator, calm and unsettled", "a quiet front porch at night", "general audience", "FALSE",
     "", "", "", "IDEA", "", "", "", "", "", "", "", "", "", ""],
]


def col_letter(n):
    """Convert a 1-indexed column number to A1 notation letters (handles columns past Z)."""
    s = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def ensure_headers(sheet):
    values = get_all_values(sheet)
    # No data rows beyond (or including) a header row means there is nothing real
    # to preserve -- this also covers sheets where Google Sheets auto-generated a
    # placeholder "Table" header row (e.g. "Column 1", "Column 2", ...): in that
    # case we overwrite it cleanly instead of appending our headers after the junk.
    has_real_data = len(values) > 1
    if not has_real_data:
        end_col = col_letter(len(REQUIRED_HEADERS))
        run_with_retry("Writing header row", lambda: sheet.update(f"A1:{end_col}1", [REQUIRED_HEADERS], value_input_option="USER_ENTERED"))
        return REQUIRED_HEADERS
    headers = values[0]
    changed = False
    for h in REQUIRED_HEADERS:
        if h not in headers:
            headers.append(h)
            changed = True
    if changed:
        end_col = col_letter(len(headers))
        run_with_retry("Updating header row", lambda: sheet.update(f"A1:{end_col}1", [headers], value_input_option="USER_ENTERED"))
    return headers


def main():
    client = get_sheets_client()
    spreadsheet = open_spreadsheet(client)
    content = get_worksheet(spreadsheet, CONTENT_SHEET_NAME)
    headers = ensure_headers(content)
    values = get_all_values(content)
    if len(values) <= 1:
        run_with_retry("Adding starter rows", lambda: content.append_rows(STARTER_ROWS, value_input_option="USER_ENTERED"))
    try:
        spreadsheet.worksheet(LOGS_SHEET_NAME)
    except Exception:
        logs = spreadsheet.add_worksheet(title=LOGS_SHEET_NAME, rows=1000, cols=4)
        logs.update("A1:D1", [["timestamp", "video_id", "action", "message"]], value_input_option="USER_ENTERED")
    print("Sheet schema ready. Next run: Seed Ideas to fill the backlog for every video type.")

if __name__ == "__main__":
    main()
