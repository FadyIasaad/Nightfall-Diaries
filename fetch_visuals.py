import os
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus

import requests
import gspread
from google.oauth2.service_account import Credentials


SHEET_ID = os.environ["GOOGLE_SHEET_ID"]
SERVICE_ACCOUNT_JSON = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]
PEXELS_API_KEY = os.environ["PEXELS_API_KEY"]
PIXABAY_API_KEY = os.environ["PIXABAY_API_KEY"]

CONTENT_SHEET_NAME = "Content"
LOGS_SHEET_NAME = "Logs"

OUTPUT_DIR = Path("output/visuals")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def get_sheets_client():
    service_account_info = json.loads(SERVICE_ACCOUNT_JSON)
    credentials = Credentials.from_service_account_info(
        service_account_info,
        scopes=SCOPES,
    )
    return gspread.authorize(credentials)


def find_column(headers, name):
    if name not in headers:
        raise ValueError(f"Missing required column: {name}")
    return headers.index(name) + 1


def get_cell(row, col):
    return row[col - 1].strip() if len(row) >= col else ""


def log(logs_sheet, video_id, action, message):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    logs_sheet.append_row(
        [now, video_id, action, message],
        value_input_option="USER_ENTERED",
    )


def clean_query(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    remove_words = {
        "emotional", "storybook", "illustration", "cinematic", "lighting",
        "vertical", "youtube", "shorts", "style", "warm", "soft",
        "detailed", "expressive", "animal", "emotion", "family", "friendly",
        "no", "text", "image", "prompt", "scene", "composition",
    }

    words = [w for w in text.split() if w not in remove_words and len(w) > 2]
    return " ".join(words[:8]).strip()


def build_queries(scene, animal, topic):
    scene_text = scene.get("text", "")
    image_prompt = scene.get("image_prompt", "")

    cleaned_prompt = clean_query(image_prompt)
    cleaned_scene = clean_query(scene_text)
    cleaned_topic = clean_query(topic)

    queries = []

    if animal and cleaned_scene:
        queries.append(f"{animal} {cleaned_scene}")

    if animal and cleaned_prompt:
        queries.append(f"{animal} {cleaned_prompt}")

    if animal and cleaned_topic:
        queries.append(f"{animal} {cleaned_topic}")

    if animal:
        queries.append(f"{animal} cute")
        queries.append(f"{animal} sad")
        queries.append(animal)

    # remove duplicates while preserving order
    final = []
    seen = set()
    for q in queries:
        q = re.sub(r"\s+", " ", q).strip()
        if q and q not in seen:
            final.append(q)
            seen.add(q)

    return final


def download_file(url, output_path):
    response = requests.get(url, timeout=45)
    response.raise_for_status()
    output_path.write_bytes(response.content)
    return output_path


def search_pexels_photo(query):
    url = "https://api.pexels.com/v1/search"
    headers = {
        "Authorization": PEXELS_API_KEY,
    }
    params = {
        "query": query,
        "orientation": "portrait",
        "per_page": 10,
    }

    response = requests.get(url, headers=headers, params=params, timeout=45)
    response.raise_for_status()

    data = response.json()
    photos = data.get("photos", [])

    if not photos:
        return None

    # Prefer portrait-ish images
    best = sorted(
        photos,
        key=lambda p: abs((p.get("width", 1) / max(p.get("height", 1), 1)) - 0.5625),
    )[0]

    src = best.get("src", {})
    return src.get("large2x") or src.get("large") or src.get("original")


def search_pixabay_image(query):
    url = "https://pixabay.com/api/"
    params = {
        "key": PIXABAY_API_KEY,
        "q": query,
        "image_type": "photo",
        "orientation": "vertical",
        "safesearch": "true",
        "per_page": 10,
    }

    response = requests.get(url, params=params, timeout=45)
    response.raise_for_status()

    data = response.json()
    hits = data.get("hits", [])

    if not hits:
        return None

    best = sorted(
        hits,
        key=lambda p: abs((p.get("imageWidth", 1) / max(p.get("imageHeight", 1), 1)) - 0.5625),
    )[0]

    return best.get("largeImageURL") or best.get("webformatURL")


def fetch_visual_for_scene(scene, animal, topic, output_path):
    queries = build_queries(scene, animal, topic)

    last_error = None

    for query in queries:
        try:
            image_url = search_pexels_photo(query)
            if image_url:
                download_file(image_url, output_path)
                return {
                    "source": "pexels",
                    "query": query,
                    "path": str(output_path),
                }
        except Exception as e:
            last_error = f"Pexels error for query '{query}': {e}"

    for query in queries:
        try:
            image_url = search_pixabay_image(query)
            if image_url:
                download_file(image_url, output_path)
                return {
                    "source": "pixabay",
                    "query": query,
                    "path": str(output_path),
                }
        except Exception as e:
            last_error = f"Pixabay error for query '{query}': {e}"

    raise ValueError(f"No visual found. Last error: {last_error}. Queries tried: {queries}")


def main():
    sheets_client = get_sheets_client()
    spreadsheet = sheets_client.open_by_key(SHEET_ID)

    content_sheet = spreadsheet.worksheet(CONTENT_SHEET_NAME)
    logs_sheet = spreadsheet.worksheet(LOGS_SHEET_NAME)

    all_values = content_sheet.get_all_values()

    if not all_values:
        raise ValueError("Content sheet is empty.")

    headers = all_values[0]

    id_col = find_column(headers, "id")
    topic_col = find_column(headers, "topic")
    animal_col = find_column(headers, "animal")
    status_col = find_column(headers, "status")
    scene_prompts_col = find_column(headers, "scene_prompts")
    image_status_col = find_column(headers, "image_status")

    target_row_number = None
    target_row = None

    for index, row in enumerate(all_values[1:], start=2):
        status = get_cell(row, status_col)
        image_status = get_cell(row, image_status_col)

        if status == "GENERATED" and image_status in ("PENDING", "", "FAILED"):
            target_row_number = index
            target_row = row
            break

    if target_row_number is None:
        log(logs_sheet, "", "FETCH_VISUALS", "No GENERATED row with pending visuals found.")
        print("No row ready for visual fetching.")
        return

    video_id = get_cell(target_row, id_col)
    topic = get_cell(target_row, topic_col)
    animal = get_cell(target_row, animal_col)
    scene_prompts_raw = get_cell(target_row, scene_prompts_col)

    if not scene_prompts_raw:
        raise ValueError(f"Missing scene_prompts in row {target_row_number}")

    scenes = json.loads(scene_prompts_raw)

    if not isinstance(scenes, list) or len(scenes) != 3:
        raise ValueError("scene_prompts must contain exactly 3 scenes.")

    video_visual_dir = OUTPUT_DIR / str(video_id)
    video_visual_dir.mkdir(parents=True, exist_ok=True)

    results = []

    try:
        for i, scene in enumerate(scenes, start=1):
            output_path = video_visual_dir / f"scene_{i}.jpg"
            result = fetch_visual_for_scene(scene, animal, topic, output_path)
            results.append(result)

        content_sheet.update_cell(target_row_number, image_status_col, "CREATED")

        log(
            logs_sheet,
            video_id,
            "FETCH_VISUALS",
            f"Fetched visuals for row {target_row_number}: {json.dumps(results)}",
        )

        print(json.dumps(results, indent=2))

    except Exception as e:
        content_sheet.update_cell(target_row_number, image_status_col, "FAILED")
        log(
            logs_sheet,
            video_id,
            "FETCH_VISUALS_FAILED",
            str(e),
        )
        raise


if __name__ == "__main__":
    main()
