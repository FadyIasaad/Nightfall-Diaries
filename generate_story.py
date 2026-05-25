import os
import json
import time
import random
import re
from datetime import datetime, timezone

import gspread
from gspread.exceptions import APIError
from google.oauth2.service_account import Credentials

import google.generativeai as genai


# =========================
# CONFIG
# =========================

SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "").strip()
SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

DEFAULT_WORKSHEET_NAME = os.getenv("WORKSHEET_NAME", "Sheet1").strip()

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip()

REQUIRED_COLUMNS = [
    "id",
    "topic",
    "animal",
    "lesson",
    "script",
    "title",
    "description",
    "status",
    "video_url",
    "created_at",
]

IDEA_STATUS = "IDEA"
GENERATED_STATUS = "GENERATED"
FAILED_STATUS = "FAILED"


# =========================
# VALIDATION
# =========================

def require_env(name: str, value: str) -> None:
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")


def validate_environment() -> None:
    require_env("GOOGLE_SHEET_ID", SHEET_ID)
    require_env("GOOGLE_SERVICE_ACCOUNT_JSON", SERVICE_ACCOUNT_JSON)
    require_env("GEMINI_API_KEY", GEMINI_API_KEY)


# =========================
# RETRY HELPERS
# =========================

def is_retryable_error(error: Exception) -> bool:
    text = str(error).lower()

    retryable_signals = [
        "503",
        "500",
        "502",
        "504",
        "429",
        "timeout",
        "timed out",
        "temporarily",
        "temporary",
        "service is currently unavailable",
        "service unavailable",
        "internal error",
        "connection",
        "rate limit",
        "quota",
        "deadline exceeded",
    ]

    return any(signal in text for signal in retryable_signals)


def wait_before_retry(attempt: int, max_wait_seconds: int = 60) -> None:
    wait_seconds = min(max_wait_seconds, (2 ** attempt) + random.uniform(0, 3))
    print(f"Waiting {wait_seconds:.1f} seconds before retry...")
    time.sleep(wait_seconds)


def run_with_retry(action_name, func, max_attempts=6):
    """
    Run any temporary-failure-prone action with retries.
    Good for Google Sheets, Gemini, and network calls.
    """
    last_error = None

    for attempt in range(1, max_attempts + 1):
        try:
            print(f"{action_name}... attempt {attempt}/{max_attempts}")
            return func()

        except APIError as e:
            last_error = e

            if not is_retryable_error(e):
                print(f"Non-retryable Google API error during {action_name}: {e}")
                raise

            print(f"Temporary Google API error during {action_name}: {e}")
            wait_before_retry(attempt)

        except Exception as e:
            last_error = e

            if not is_retryable_error(e):
                print(f"Non-retryable error during {action_name}: {e}")
                raise

            print(f"Temporary error during {action_name}: {e}")
            wait_before_retry(attempt)

    raise RuntimeError(
        f"{action_name} failed after {max_attempts} attempts. Last error: {last_error}"
    )


# =========================
# GOOGLE SHEETS
# =========================

def get_gspread_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    try:
        service_account_info = json.loads(SERVICE_ACCOUNT_JSON)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            "GOOGLE_SERVICE_ACCOUNT_JSON is not valid JSON. "
            "Check your GitHub Secret and make sure you copied the full JSON."
        ) from e

    credentials = Credentials.from_service_account_info(
        service_account_info,
        scopes=scopes,
    )

    return gspread.authorize(credentials)


def open_sheet_with_retry(client, sheet_id):
    return run_with_retry(
        "Opening Google Sheet",
        lambda: client.open_by_key(sheet_id),
        max_attempts=6,
    )


def get_worksheet(spreadsheet):
    """
    Try to open worksheet by name.
    If it does not exist, use first worksheet.
    """
    try:
        return run_with_retry(
            f"Opening worksheet '{DEFAULT_WORKSHEET_NAME}'",
            lambda: spreadsheet.worksheet(DEFAULT_WORKSHEET_NAME),
            max_attempts=4,
        )
    except Exception as e:
        print(f"Could not open worksheet '{DEFAULT_WORKSHEET_NAME}': {e}")
        print("Trying first worksheet instead...")
        return run_with_retry(
            "Opening first worksheet",
            lambda: spreadsheet.get_worksheet(0),
            max_attempts=4,
        )


def ensure_headers(worksheet):
    """
    Make sure the first row has all required columns.
    If the sheet is empty, create the headers.
    """
    values = run_with_retry(
        "Reading header row",
        lambda: worksheet.row_values(1),
        max_attempts=6,
    )

    if not values:
        print("Sheet has no headers. Creating required headers...")
        run_with_retry(
            "Writing header row",
            lambda: worksheet.update("A1:J1", [REQUIRED_COLUMNS]),
            max_attempts=6,
        )
        return REQUIRED_COLUMNS

    normalized_existing = [v.strip() for v in values]
    missing = [col for col in REQUIRED_COLUMNS if col not in normalized_existing]

    if missing:
        raise RuntimeError(
            "Your Google Sheet is missing required columns: "
            + ", ".join(missing)
            + "\nRequired columns are: "
            + ", ".join(REQUIRED_COLUMNS)
        )

    return normalized_existing


def get_all_records_with_retry(worksheet):
    return run_with_retry(
        "Reading worksheet records",
        lambda: worksheet.get_all_records(),
        max_attempts=6,
    )


def find_first_idea_row(records):
    """
    Returns:
    - sheet row number, because records start after header row
    - record dictionary
    """
    for index, record in enumerate(records, start=2):
        status = str(record.get("status", "")).strip().upper()
        topic = str(record.get("topic", "")).strip()

        if status == IDEA_STATUS and topic:
            return index, record

    return None, None


def get_column_map(headers):
    return {name: index + 1 for index, name in enumerate(headers)}


def update_cell(worksheet, row, col, value):
    return run_with_retry(
        f"Updating cell R{row}C{col}",
        lambda: worksheet.update_cell(row, col, value),
        max_attempts=6,
    )


def update_story_row(worksheet, row_number, headers, story_data):
    col = get_column_map(headers)

    updates = {
        "script": story_data.get("script", ""),
        "title": story_data.get("title", ""),
        "description": story_data.get("description", ""),
        "status": GENERATED_STATUS,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    for column_name, value in updates.items():
        if column_name in col:
            update_cell(worksheet, row_number, col[column_name], value)


def mark_row_failed(worksheet, row_number, headers, error_message):
    col = get_column_map(headers)

    if "status" in col:
        update_cell(worksheet, row_number, col["status"], FAILED_STATUS)

    if "description" in col:
        short_error = f"FAILED: {str(error_message)[:400]}"
        update_cell(worksheet, row_number, col["description"], short_error)

    if "created_at" in col:
        update_cell(
            worksheet,
            row_number,
            col["created_at"],
            datetime.now(timezone.utc).isoformat(),
        )


# =========================
# GEMINI
# =========================

def configure_gemini():
    genai.configure(api_key=GEMINI_API_KEY)


def extract_json_from_text(text):
    """
    Gemini sometimes returns JSON inside markdown fences.
    This extracts the first valid JSON object.
    """
    if not text:
        raise RuntimeError("Gemini returned empty response.")

    cleaned = text.strip()

    cleaned = re.sub(r"^```json\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^```\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if not match:
        raise RuntimeError(f"Could not find JSON object in Gemini response:\n{cleaned}")

    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON from Gemini:\n{cleaned}") from e


def build_prompt(record):
    topic = str(record.get("topic", "")).strip()
    animal = str(record.get("animal", "")).strip()
    lesson = str(record.get("lesson", "")).strip()

    return f"""
You are writing for a YouTube Shorts channel called "Tiny Brave Tails".

Channel concept:
Short emotional animal stories with simple life lessons.

Target audience:
Global English-speaking audience.
Family-friendly.
Not made only for kids.
Simple emotional English.
No violence.
No gore.
No politics.
No religion.
No copyrighted characters.
No claim that the story is true unless verified.
Make it feel cinematic and touching.

Video length:
35 to 55 seconds.

Structure:
1. First sentence must be a strong hook.
2. Introduce the animal quickly.
3. Show an emotional problem.
4. Show a brave or kind action.
5. End with one simple life lesson.

Topic:
{topic}

Animal:
{animal}

Life lesson:
{lesson}

Return JSON only.
No markdown.
No explanation.

JSON format:
{{
  "title": "A short clickable YouTube Shorts title under 70 characters",
  "script": "The full voiceover script, around 90 to 130 words",
  "description": "A short YouTube description with a clear emotional summary and hashtags"
}}
""".strip()


def validate_story_data(data):
    if not isinstance(data, dict):
        raise RuntimeError("Gemini response is not a JSON object.")

    title = str(data.get("title", "")).strip()
    script = str(data.get("script", "")).strip()
    description = str(data.get("description", "")).strip()

    if not title:
        raise RuntimeError("Gemini response missing title.")

    if not script:
        raise RuntimeError("Gemini response missing script.")

    if not description:
        raise RuntimeError("Gemini response missing description.")

    word_count = len(script.split())
    if word_count < 60:
        raise RuntimeError(f"Generated script is too short: {word_count} words.")

    if word_count > 170:
        raise RuntimeError(f"Generated script is too long: {word_count} words.")

    if "#shorts" not in description.lower():
        description += "\n\n#shorts #animalstory #emotionalstory #lifelessons #tinybravetails"

    return {
        "title": title[:95],
        "script": script,
        "description": description,
    }


def generate_story_with_gemini(record):
    configure_gemini()

    model = genai.GenerativeModel(
        GEMINI_MODEL,
        generation_config={
            "temperature": 0.9,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 1200,
        },
    )

    prompt = build_prompt(record)

    def call_gemini():
        response = model.generate_content(prompt)

        if not response:
            raise RuntimeError("No response from Gemini.")

        text = getattr(response, "text", None)

        if not text:
            try:
                text = response.candidates[0].content.parts[0].text
            except Exception as e:
                raise RuntimeError(f"Could not read Gemini response text: {response}") from e

        parsed = extract_json_from_text(text)
        return validate_story_data(parsed)

    return run_with_retry(
        "Generating story with Gemini",
        call_gemini,
        max_attempts=5,
    )


# =========================
# MAIN
# =========================

def main():
    print("Starting Tiny Brave Tails story generator...")

    validate_environment()

    client = get_gspread_client()
    spreadsheet = open_sheet_with_retry(client, SHEET_ID)
    worksheet = get_worksheet(spreadsheet)

    headers = ensure_headers(worksheet)
    records = get_all_records_with_retry(worksheet)

    row_number, record = find_first_idea_row(records)

    if not record:
        print("No rows with status IDEA found. Nothing to generate.")
        return

    print(f"Found IDEA row: {row_number}")
    print(f"Topic: {record.get('topic', '')}")
    print(f"Animal: {record.get('animal', '')}")
    print(f"Lesson: {record.get('lesson', '')}")

    try:
        story_data = generate_story_with_gemini(record)

        print("Generated title:")
        print(story_data["title"])

        print("Generated script:")
        print(story_data["script"])

        update_story_row(
            worksheet=worksheet,
            row_number=row_number,
            headers=headers,
            story_data=story_data,
        )

        print(f"Row {row_number} updated successfully with status {GENERATED_STATUS}.")

    except Exception as e:
        print(f"Generation failed for row {row_number}: {e}")
        mark_row_failed(
            worksheet=worksheet,
            row_number=row_number,
            headers=headers,
            error_message=e,
        )
        raise


if __name__ == "__main__":
    main()
