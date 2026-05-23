import os
import json
import re
from datetime import datetime, timezone

import gspread
import google.generativeai as genai
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

BANNED_TITLE_WORDS = ["true story", "real story", "shocking", "gone wrong", "you won't believe"]


def get_sheets_client():
    service_account_info = json.loads(SERVICE_ACCOUNT_JSON)
    credentials = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
    return gspread.authorize(credentials)


def clean_json_response(text):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE).strip()
        text = re.sub(r"```$", "", text).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON object found in Gemini response: {text}")
    return text[start:end + 1]


def one_sentence(text, max_words=13):
    text = re.sub(r"\s+", " ", str(text or "").replace("\n", " ")).strip()
    text = re.split(r"(?<=[.!?])\s+", text)[0].strip()
    words = text.split()
    if len(words) > max_words:
        text = " ".join(words[:max_words]).rstrip(",;:") + "."
    return text


def clean_title(title, animal, lesson):
    title = re.sub(r"\s+", " ", str(title or "").strip())
    for phrase in BANNED_TITLE_WORDS:
        title = re.sub(re.escape(phrase), "", title, flags=re.IGNORECASE).strip(" -:|,.!")
    if not title:
        title = f"The Tiny {animal} Who Learned {lesson}"
    return title[:70].rstrip(" -:|,.")


def clean_description(description, animal, lesson):
    description = re.sub(r"\s+", " ", str(description or "").strip())
    if not description:
        description = f"A tiny {animal} faces a big moment and learns {lesson}."
    hashtags = "#shorts #animalstory #emotionalstory #lifelessons #tinybravetails"
    if hashtags not in description.lower():
        description = f"{description}\n\n{hashtags}"
    return description[:5000]


def generate_story_package(topic, animal, lesson):
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")

    prompt = f"""
You are the lead writer and retention editor for a family-friendly YouTube Shorts channel called Tiny Brave Tails.

Goal:
Create one highly watchable English-only animated short that can earn higher retention.

Channel style:
Warm emotional 2D cartoon storybook animal stories with simple life lessons.

Input:
Topic: {topic}
Animal: {animal}
Life lesson: {lesson}

Hard rules:
- English only. Do NOT create Arabic text, Arabic subtitles, or translated subtitles.
- Family-friendly.
- No horror, gore, explicit violence, politics, religion, adult content, or claim that the story is true.
- Exactly 7 scenes.
- Total target length: 35 to 48 seconds.
- Each narration line must be one complete sentence, 6 to 13 words.
- Each subtitle_en must match narration_en exactly or be nearly identical.
- Scene 1 must create curiosity in the first 2 seconds.
- Scene 2 must show the problem clearly.
- Scene 3 must raise the emotional stakes.
- Scene 4 must show a failed attempt or fear.
- Scene 5 must show brave action.
- Scene 6 must show emotional payoff.
- Scene 7 must land the lesson and invite comments softly.
- No long paragraphs.
- No text inside image prompts.
- Return valid JSON only.

Title rules:
- Under 70 characters.
- Emotional and clickable without lying.
- Use curiosity, not fake clickbait.
- Good examples: "The Puppy Nobody Picked", "The Smallest Bird Saved the Day".

Description rules:
- One emotional sentence plus hashtags.
- Include #shorts and relevant tags.

Return exactly this JSON:
{{
  "title": "Short emotional YouTube title under 70 characters",
  "description": "Short YouTube description with hashtags",
  "hook_text": "A 3 to 6 word on-screen hook for scene 1 only",
  "comment_prompt": "A short comment question under 9 words",
  "character": {{
    "name": "Character name",
    "description": "Consistent 2D storybook character design. Include animal type, color, eyes, accessory, mood, and visual style."
  }},
  "scenes": [
    {{
      "scene_number": 1,
      "narration_en": "One short English sentence.",
      "subtitle_en": "Same short English sentence.",
      "emotion": "curious",
      "image_prompt": "Vertical 9:16 warm 2D cartoon storybook frame matching this scene, no text"
    }}
  ]
}}

Image prompt rules:
Every image_prompt must include: warm 2D cartoon storybook, soft colors, expressive animal face, cinematic lighting, child-safe, vertical 9:16, no text, no watermark.
Keep the same character design across all scenes.
"""

    response = model.generate_content(prompt)
    data = json.loads(clean_json_response(response.text))

    for key in ["title", "description", "character", "scenes"]:
        if key not in data:
            raise ValueError(f"Missing key: {key}")

    scenes = data["scenes"]
    if not isinstance(scenes, list) or len(scenes) != 7:
        raise ValueError("Expected exactly 7 scenes.")

    cleaned_scenes = []
    for i, scene in enumerate(scenes, start=1):
        narration = one_sentence(scene.get("narration_en", ""), max_words=13)
        subtitle_en = one_sentence(scene.get("subtitle_en", "") or narration, max_words=13)
        image_prompt = str(scene.get("image_prompt", "")).strip()
        emotion = str(scene.get("emotion", "emotional")).strip() or "emotional"
        if not narration or not image_prompt:
            raise ValueError(f"Incomplete scene {i}: {scene}")
        cleaned_scenes.append(
            {
                "scene_number": i,
                "narration_en": narration,
                "subtitle_en": subtitle_en,
                "emotion": emotion,
                "image_prompt": image_prompt,
            }
        )

    data["title"] = clean_title(data.get("title", ""), animal, lesson)
    data["description"] = clean_description(data.get("description", ""), animal, lesson)
    data["hook_text"] = one_sentence(data.get("hook_text", ""), max_words=6).rstrip(".") or "Wait for it"
    data["comment_prompt"] = one_sentence(data.get("comment_prompt", ""), max_words=9).rstrip(".") or "What would you do?"
    data["scenes"] = cleaned_scenes
    data["script"] = " ".join(scene["narration_en"] for scene in cleaned_scenes)
    return data


def find_column(headers, name):
    if name not in headers:
        raise ValueError(f"Missing required column: {name}")
    return headers.index(name) + 1


def get_cell(row, col):
    return row[col - 1].strip() if len(row) >= col else ""


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

    package = generate_story_package(topic, animal, lesson)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    scene_payload = {
        "character": package["character"],
        "hook_text": package["hook_text"],
        "comment_prompt": package["comment_prompt"],
        "scenes": package["scenes"],
    }

    content_sheet.update_cell(target_row_number, title_col, package["title"])
    content_sheet.update_cell(target_row_number, script_col, package["script"])
    content_sheet.update_cell(target_row_number, description_col, package["description"])
    content_sheet.update_cell(target_row_number, scene_prompts_col, json.dumps(scene_payload, ensure_ascii=False))
    content_sheet.update_cell(target_row_number, status_col, "GENERATED")
    content_sheet.update_cell(target_row_number, created_at_col, now)
    content_sheet.update_cell(target_row_number, image_status_col, "PENDING")
    content_sheet.update_cell(target_row_number, audio_status_col, "PENDING")
    content_sheet.update_cell(target_row_number, youtube_status_col, "")
    content_sheet.update_cell(target_row_number, youtube_video_id_col, "")

    log(logs_sheet, video_id, "GENERATE_STORY", f"Generated English-only 7-scene retention story: {package['title']}")
    print(f"Generated story: {package['title']}")


if __name__ == "__main__":
    main()
