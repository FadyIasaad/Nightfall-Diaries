import json
import os
import re
from datetime import datetime, timezone

import google.generativeai as genai
import gspread
from google.oauth2.service_account import Credentials

SHEET_ID = os.environ["GOOGLE_SHEET_ID"]
SERVICE_ACCOUNT_JSON = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

CONTENT_SHEET_NAME = "Content"
LOGS_SHEET_NAME = "Logs"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

ALLOWED_VOICE_ROLES = {
    "narrator",
    "small_hero",
    "female_warm",
    "wise_elder",
    "danger",
    "ending",
}


def get_sheets_client():
    service_account_info = json.loads(SERVICE_ACCOUNT_JSON)
    credentials = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
    return gspread.authorize(credentials)


def clean_json_response(text):
    text = str(text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE).strip()
        text = re.sub(r"```$", "", text).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"No JSON object found in Gemini response: {text[:500]}")
    return text[start : end + 1]


def safe_text(value, max_len=None):
    value = re.sub(r"\s+", " ", str(value or "").strip())
    if max_len and len(value) > max_len:
        value = value[: max_len - 1].rstrip() + "…"
    return value


def normalize_voice_role(value, fallback="narrator"):
    value = safe_text(value).lower().replace(" ", "_").replace("-", "_")
    return value if value in ALLOWED_VOICE_ROLES else fallback


def generate_story_package(topic, animal, lesson):
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")

    prompt = f"""
You are the lead writer, art director, and voice director for a family-friendly YouTube Shorts channel called Tiny Brave Tails.

Create ONE cinematic, emotional, English-only animal story package for a fully automated video pipeline.

INPUT
Topic: {topic}
Animal: {animal}
Life lesson: {lesson}

NON-NEGOTIABLE RULES
- English only. Do not create Arabic subtitles or Arabic text anywhere.
- Family-friendly, warm, emotional, and safe for a general audience.
- No horror, no gore, no explicit violence, no cruelty, no disturbing imagery.
- Do not claim the story is true.
- Strong hook in scene 1.
- Fast pacing: every line must earn its place.
- Use short dramatic sentences with natural pauses using "..." or em dashes when helpful.
- Include a small amount of dialogue. Do not make every line narration.
- Make the voice roles fit the character and moment.
- Total spoken story should feel like 40 to 55 seconds.
- Return valid JSON only. No markdown. No explanation.

VOICE ROLE MEANINGS
- narrator: deep warm storyteller narration.
- small_hero: innocent small main character, softer and more vulnerable.
- female_warm: warm caring character.
- wise_elder: slow wise mentor, older and calm.
- danger: tense low dramatic moment, not horror.
- ending: warm hopeful closing lesson.

VISUAL STYLE
- warm 2D cartoon storybook illustration.
- vertical 9:16.
- cute expressive animal character.
- soft cinematic lighting.
- clear subject in frame.
- no text, no logo, no watermark.
- keep the same main character design in every image prompt.

Return exactly this JSON structure:
{{
  "title": "Short emotional YouTube title under 70 characters",
  "description": "Short YouTube description with hashtags",
  "character": {{
    "name": "Character name",
    "animal_type": "Animal type",
    "description": "Consistent 2D storybook character design: animal type, fur/feather color, eyes, accessory, mood, and visual style."
  }},
  "scenes": [
    {{
      "scene_number": 1,
      "moment_type": "hook",
      "camera_motion": "slow_zoom_in",
      "atmosphere": "soft rain",
      "subtitle_en": "Short complete subtitle for the scene.",
      "image_prompt": "Vertical 9:16 warm 2D cartoon storybook illustration matching this scene, no text, no watermark.",
      "lines": [
        {{
          "speaker": "Narrator",
          "voice_role": "narrator",
          "text": "One short dramatic spoken line."
        }}
      ]
    }}
  ]
}}

SCENE PLAN
- Exactly 8 scenes.
- Scene 1: emotional hook.
- Scene 2: introduce the problem.
- Scene 3: the hero feels afraid or alone.
- Scene 4: a choice appears.
- Scene 5: brave action.
- Scene 6: consequence or emotional turn.
- Scene 7: relief or connection.
- Scene 8: simple life lesson with a warm ending.

LINE RULES
- Each scene must have 1 to 3 spoken lines.
- Each line text must be under 120 characters.
- Use voice_role from the allowed list only.
- subtitle_en should summarize the full scene in one short subtitle.
- image_prompt must be specific and must include the same character design.
"""

    response = model.generate_content(prompt)
    data = json.loads(clean_json_response(response.text))

    for key in ["title", "description", "character", "scenes"]:
        if key not in data:
            raise ValueError(f"Missing key from Gemini JSON: {key}")

    scenes = data["scenes"]
    if not isinstance(scenes, list) or len(scenes) != 8:
        raise ValueError(f"Expected exactly 8 scenes, got {len(scenes) if isinstance(scenes, list) else 'not a list'}")

    character = data.get("character") or {}
    character_description = safe_text(character.get("description"), 500)
    if not character_description:
        raise ValueError("Missing character.description")

    cleaned_scenes = []
    script_parts = []

    for i, scene in enumerate(scenes, start=1):
        image_prompt = safe_text(scene.get("image_prompt"), 900)
        subtitle_en = safe_text(scene.get("subtitle_en"), 220)
        moment_type = safe_text(scene.get("moment_type"), 60) or f"scene_{i}"
        camera_motion = safe_text(scene.get("camera_motion"), 60) or "slow_zoom_in"
        atmosphere = safe_text(scene.get("atmosphere"), 80) or "warm light"

        raw_lines = scene.get("lines")
        if not isinstance(raw_lines, list):
            raw_lines = []

        lines = []
        for raw_line in raw_lines[:3]:
            if not isinstance(raw_line, dict):
                continue
            text = safe_text(raw_line.get("text"), 140)
            if not text:
                continue
            voice_role = normalize_voice_role(raw_line.get("voice_role"), "narrator")
            speaker = safe_text(raw_line.get("speaker"), 60) or voice_role.replace("_", " ").title()
            lines.append({"speaker": speaker, "voice_role": voice_role, "text": text})

        if not lines:
            narration = safe_text(scene.get("narration_en") or subtitle_en, 180)
            if narration:
                lines.append({"speaker": "Narrator", "voice_role": "narrator", "text": narration})

        if not lines or not image_prompt:
            raise ValueError(f"Incomplete scene {i}: {scene}")

        if not subtitle_en:
            subtitle_en = safe_text(" ".join(line["text"] for line in lines), 220)

        for line in lines:
            script_parts.append(line["text"])

        cleaned_scenes.append(
            {
                "scene_number": i,
                "moment_type": moment_type,
                "camera_motion": camera_motion,
                "atmosphere": atmosphere,
                "subtitle_en": subtitle_en,
                "image_prompt": image_prompt,
                "lines": lines,
                "narration_en": " ".join(line["text"] for line in lines),
            }
        )

    data["title"] = safe_text(data.get("title"), 70)
    data["description"] = safe_text(data.get("description"), 4500)
    data["character"] = {
        "name": safe_text(character.get("name"), 80) or "Tiny Hero",
        "animal_type": safe_text(character.get("animal_type"), 80) or safe_text(animal, 80),
        "description": character_description,
    }
    data["scenes"] = cleaned_scenes
    data["script"] = " ".join(script_parts)

    if not data["title"] or not data["script"]:
        raise ValueError("Gemini returned empty title or script.")

    return data


def find_column(headers, name):
    if name not in headers:
        raise ValueError(f"Missing required column: {name}")
    return headers.index(name) + 1


def find_optional_column(headers, name):
    return headers.index(name) + 1 if name in headers else None


def get_cell(row, col):
    return row[col - 1].strip() if col and len(row) >= col else ""


def update_optional(sheet, row_number, col, value):
    if col:
        sheet.update_cell(row_number, col, value)


def log(logs_sheet, video_id, action, message):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    logs_sheet.append_row([now, video_id, action, message], value_input_option="USER_ENTERED")


def main():
    client = get_sheets_client()
    spreadsheet = client.open_by_key(SHEET_ID)
    content_sheet = spreadsheet.worksheet(CONTENT_SHEET_NAME)
    logs_sheet = spreadsheet.worksheet(LOGS_SHEET_NAME)

    values = content_sheet.get_all_values()
    if not values:
        raise ValueError("Content sheet is empty.")

    headers = values[0]
    id_col = find_column(headers, "id")
    topic_col = find_column(headers, "topic")
    animal_col = find_column(headers, "animal")
    lesson_col = find_column(headers, "lesson")
    script_col = find_column(headers, "script")
    title_col = find_column(headers, "title")
    description_col = find_column(headers, "description")
    status_col = find_column(headers, "status")
    created_at_col = find_column(headers, "created_at")
    scene_prompts_col = find_column(headers, "scene_prompts")
    image_status_col = find_column(headers, "image_status")
    audio_status_col = find_column(headers, "audio_status")
    youtube_status_col = find_column(headers, "youtube_status")
    youtube_video_id_col = find_column(headers, "youtube_video_id")
    error_message_col = find_optional_column(headers, "error_message")

    target_row_number = None
    target_row = None
    for index, row in enumerate(values[1:], start=2):
        if get_cell(row, status_col).upper() == "IDEA":
            target_row_number = index
            target_row = row
            break

    if target_row_number is None:
        log(logs_sheet, "", "GENERATE_STORY", "No IDEA row found.")
        print("No IDEA row found.")
        return

    video_id = get_cell(target_row, id_col)
    topic = get_cell(target_row, topic_col)
    animal = get_cell(target_row, animal_col)
    lesson = get_cell(target_row, lesson_col)

    try:
        package = generate_story_package(topic, animal, lesson)
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        scene_payload = {"character": package["character"], "scenes": package["scenes"]}

        content_sheet.update_cell(target_row_number, title_col, package["title"])
        content_sheet.update_cell(target_row_number, script_col, package["script"])
        content_sheet.update_cell(target_row_number, description_col, package["description"])
        content_sheet.update_cell(
            target_row_number,
            scene_prompts_col,
            json.dumps(scene_payload, ensure_ascii=False),
        )
        content_sheet.update_cell(target_row_number, status_col, "GENERATED")
        content_sheet.update_cell(target_row_number, created_at_col, now)
        content_sheet.update_cell(target_row_number, image_status_col, "PENDING")
        content_sheet.update_cell(target_row_number, audio_status_col, "PENDING")
        content_sheet.update_cell(target_row_number, youtube_status_col, "")
        content_sheet.update_cell(target_row_number, youtube_video_id_col, "")
        update_optional(content_sheet, target_row_number, error_message_col, "")

        log(logs_sheet, video_id, "GENERATE_STORY", f"Generated cinematic English-only 8-scene story: {package['title']}")
        print(f"Generated story: {package['title']}")

    except Exception as exc:
        content_sheet.update_cell(target_row_number, status_col, "FAILED_STORY")
        update_optional(content_sheet, target_row_number, error_message_col, str(exc)[:500])
        log(logs_sheet, video_id, "FAILED_STORY", str(exc)[:1000])
        raise


if __name__ == "__main__":
    main()
