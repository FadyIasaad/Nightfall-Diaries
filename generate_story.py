import json
import os
import re
from typing import Any, Dict, List

import google.generativeai as genai

from tbt_common import (
    find_column,
    get_all_values,
    get_cell,
    get_sheets_client,
    get_worksheet,
    log,
    open_spreadsheet,
    require_env,
    run_with_retry,
    update_cell,
    utc_now,
)

CONTENT_SHEET_NAME = "Content"
LOGS_SHEET_NAME = "Logs"
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

EMOTIONAL_BEATS = [
    "cold open hook with danger or loneliness",
    "show the small hero's wound or fear",
    "raise the problem and make it personal",
    "moment of doubt, almost giving up",
    "brave choice with emotional sacrifice",
    "warm rescue / connection / relief",
    "quiet bedtime lesson that lands softly",
]


def clean_json_response(text: str) -> str:
    text = (text or "").strip()
    if not text:
        raise ValueError("Gemini returned empty text")
    text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"```$", "", text).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"Could not find JSON object in Gemini response: {text[:500]}")
    return text[start : end + 1]


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w']+\b", text or ""))


def emotional_score(data: Dict[str, Any]) -> int:
    script = " ".join(scene.get("narration_en", "") for scene in data.get("scenes", []))
    lower = script.lower()
    score = 0
    signals = [
        "alone", "afraid", "scared", "brave", "trembled", "whispered",
        "heart", "tears", "shivered", "promise", "home", "softly",
        "never", "still", "tiny", "warm", "held", "courage",
    ]
    score += sum(1 for s in signals if s in lower)
    wc = word_count(script)
    if 95 <= wc <= 155:
        score += 4
    if data.get("emotional_arc"):
        score += 2
    if len(data.get("scenes", [])) == 7:
        score += 2
    return score


def build_prompt(topic: str, animal: str, lesson: str) -> str:
    beats = "\n".join(f"{i+1}. {beat}" for i, beat in enumerate(EMOTIONAL_BEATS))
    return f"""
You are the head writer and voice director for Tiny Brave Tails.
Create a bedtime YouTube Short that feels emotionally alive, not like a summary.

Inputs:
Topic: {topic}
Animal: {animal}
Life lesson: {lesson}

Non-negotiable quality bar:
- Write a real mini story, not educational narration.
- The hero must want something, fear something, and make one brave choice.
- Use sensory detail: moonlight, tiny paws, quiet rain, warm blanket, trembling voice.
- Keep it soft enough for bedtime, but emotionally strong enough to hold retention.
- No horror, gore, cruelty, explicit violence, or claim that it is true.
- English narration only. Arabic subtitles must fully translate each scene.
- Total narration target: 95 to 145 English words.
- Exactly 7 scenes.
- Every scene must have one clear emotional job.

Emotional beats:
{beats}

Return valid JSON only, exactly in this shape:
{{
  "title": "YouTube title under 70 characters",
  "description": "Short YouTube description with hashtags",
  "emotional_arc": "one sentence describing the feeling journey",
  "character": {{
    "name": "short memorable name",
    "description": "consistent 2D storybook animal design: species, colors, eyes, accessory, size, expression, style"
  }},
  "scenes": [
    {{
      "scene_number": 1,
      "beat": "emotional purpose of this scene",
      "emotion": "one of: wonder, lonely, worried, afraid, brave, relieved, peaceful",
      "voice_style": "specific direction for narrator performance",
      "pause_after": 0.35,
      "camera_motion": "one of: slow_zoom_in, slow_zoom_out, gentle_pan_left, gentle_pan_right, tiny_handheld, still_soft",
      "narration_en": "spoken English narration, 1-2 short sentences",
      "subtitle_en": "same meaning, subtitle-safe English",
      "subtitle_ar": "Arabic translation of the narration",
      "image_prompt": "vertical 9:16 warm 2D cartoon storybook frame, same character, no text"
    }}
  ]
}}

Image prompt rules:
- Include the exact character design in every scene.
- Include warm 2D cartoon storybook, soft colors, expressive animal face, child-safe, vertical 9:16, no text, no watermark.
- Describe the scene action and mood clearly.

Voice style examples:
- "soft whisper, worried, slow at the end"
- "gentle but tense, tiny pause before the final word"
- "warm relief, smile in the voice"
"""


def normalize_scene(scene: Dict[str, Any], i: int, character_desc: str) -> Dict[str, Any]:
    narration = str(scene.get("narration_en", "")).strip()
    subtitle_en = str(scene.get("subtitle_en", "")).strip() or narration
    subtitle_ar = str(scene.get("subtitle_ar", "")).strip()
    image_prompt = str(scene.get("image_prompt", "")).strip()
    if not narration or not subtitle_ar or not image_prompt:
        raise ValueError(f"Incomplete scene {i}: {scene}")
    if character_desc and character_desc.lower() not in image_prompt.lower():
        image_prompt = f"{character_desc}. {image_prompt}"
    return {
        "scene_number": i,
        "beat": str(scene.get("beat", EMOTIONAL_BEATS[i - 1])).strip(),
        "emotion": str(scene.get("emotion", "peaceful")).strip().lower(),
        "voice_style": str(scene.get("voice_style", "warm bedtime narrator, gentle emotion")).strip(),
        "pause_after": float(scene.get("pause_after", 0.35) or 0.35),
        "camera_motion": str(scene.get("camera_motion", "slow_zoom_in")).strip(),
        "narration_en": narration,
        "subtitle_en": subtitle_en,
        "subtitle_ar": subtitle_ar,
        "image_prompt": image_prompt,
    }


def generate_story_package(topic: str, animal: str, lesson: str) -> Dict[str, Any]:
    genai.configure(api_key=require_env("GEMINI_API_KEY"))
    model = genai.GenerativeModel(MODEL_NAME)

    def call_model():
        response = model.generate_content(
            build_prompt(topic, animal, lesson),
            generation_config={"temperature": 0.92, "top_p": 0.95, "max_output_tokens": 4096},
        )
        data = json.loads(clean_json_response(response.text))
        return data

    data = run_with_retry("Generating emotional story package", call_model, max_attempts=4)
    for key in ["title", "description", "character", "scenes"]:
        if key not in data:
            raise ValueError(f"Missing key: {key}")
    scenes = data["scenes"]
    if not isinstance(scenes, list) or len(scenes) != 7:
        raise ValueError("Expected exactly 7 scenes.")
    character_desc = str(data.get("character", {}).get("description", "")).strip()
    data["scenes"] = [normalize_scene(scene, i, character_desc) for i, scene in enumerate(scenes, start=1)]
    data["script"] = " ".join(scene["narration_en"] for scene in data["scenes"])
    score = emotional_score(data)
    data["emotional_score"] = score
    if score < 8:
        raise ValueError(f"Generated story is still too flat. emotional_score={score}")
    return data


def main():
    client = get_sheets_client()
    spreadsheet = open_spreadsheet(client)
    content_sheet = get_worksheet(spreadsheet, CONTENT_SHEET_NAME)
    logs_sheet = get_worksheet(spreadsheet, LOGS_SHEET_NAME)
    values = get_all_values(content_sheet)
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
    package = generate_story_package(
        get_cell(target_row, topic_col),
        get_cell(target_row, animal_col),
        get_cell(target_row, lesson_col),
    )
    scene_payload = {
        "character": package["character"],
        "emotional_arc": package.get("emotional_arc", ""),
        "emotional_score": package.get("emotional_score", ""),
        "scenes": package["scenes"],
    }
    update_cell(content_sheet, target_row_number, title_col, package["title"])
    update_cell(content_sheet, target_row_number, script_col, package["script"])
    update_cell(content_sheet, target_row_number, description_col, package["description"])
    update_cell(content_sheet, target_row_number, scene_prompts_col, json.dumps(scene_payload, ensure_ascii=False))
    update_cell(content_sheet, target_row_number, status_col, "GENERATED")
    update_cell(content_sheet, target_row_number, created_at_col, utc_now())
    update_cell(content_sheet, target_row_number, image_status_col, "PENDING")
    update_cell(content_sheet, target_row_number, audio_status_col, "PENDING")
    update_cell(content_sheet, target_row_number, youtube_status_col, "")
    update_cell(content_sheet, target_row_number, youtube_video_id_col, "")
    log(logs_sheet, video_id, "GENERATE_STORY", f"Generated emotional 7-scene story: {package['title']} | score={package['emotional_score']}")
    print(f"Generated story: {package['title']}")


if __name__ == "__main__":
    main()
