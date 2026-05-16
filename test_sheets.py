import os
import json
from datetime import datetime, timezone

import gspread
from google.oauth2.service_account import Credentials


SHEET_ID = os.environ["GOOGLE_SHEET_ID"]
SERVICE_ACCOUNT_JSON = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def get_client():
    service_account_info = json.loads(SERVICE_ACCOUNT_JSON)
    credentials = Credentials.from_service_account_info(
        service_account_info,
        scopes=SCOPES,
    )
    return gspread.authorize(credentials)


def main():
    client = get_client()
    spreadsheet = client.open_by_key(SHEET_ID)

    content_sheet = spreadsheet.worksheet("Content")
    logs_sheet = spreadsheet.worksheet("Logs")

    rows = content_sheet.get_all_records()

    idea_rows = [
        row for row in rows
        if str(row.get("status", "")).strip() == "IDEA"
    ]

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    if idea_rows:
        first_idea = idea_rows[0]
        message = f"Connected successfully. Found first IDEA: {first_idea.get('topic')}"
        video_id = first_idea.get("id", "")
    else:
        message = "Connected successfully, but no IDEA rows found."
        video_id = ""

    logs_sheet.append_row(
        [now, video_id, "TEST_SHEETS_CONNECTION", message],
        value_input_option="USER_ENTERED",
    )

    print(message)


if __name__ == "__main__":
    main()
