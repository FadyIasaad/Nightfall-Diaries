import asyncio
import json
import math
import os
import re
import subprocess
import time
from pathlib import Path
from urllib.parse import quote_plus

import edge_tts
import requests
from moviepy.editor import AudioFileClip, ImageClip, VideoFileClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFilter, ImageFont

if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.LANCZOS

from tbt_common import (
    find_optional_column,
    find_column,
    get_all_values,
    get_cell,
    get_sheets_client,
    get_worksheet,
    get_logs_worksheet,
    log,
    open_spreadsheet,
    update_cell,
)

CONTENT_SHEET_NAME = "Content"
LOGS_SHEET_NAME = "Logs"
OUTPUT_DIR = Path("output")
FRAMES_DIR = OUTPUT_DIR / "frames"
VISUALS_DIR = OUTPUT_DIR / "visuals"
AUDIO_DIR = OUTPUT_DIR / "audio"
VIDEO_DIR = OUTPUT_DIR / "videos"
for folder in [OUTPUT_DIR, FRAMES_DIR, VISUALS_DIR, AUDIO_DIR, VIDEO_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

WIDTH = 1080
HEIGHT = 1920
FPS = 24
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "").strip()
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY", "").strip()
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "").strip()
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "").strip()
ELEVENLABS_MODEL_ID = os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2").strip()

EMOTION_STYLE = {
    "wonder": {"voice": "en-US-AvaNeural", "rate": "-10%", "pitch": "+1Hz", "volume": "+0%"},
    "lonely": {"voice": "en-US-AriaNeural", "rate": "-17%", "pitch": "-4Hz", "volume": "-1%"},
    "worried": {"voice": "en-US-SaraNeural", "rate": "-14%", "pitch": "-3Hz", "volume": "+0%"},
    "afraid": {"voice": "en-US-SaraNeural", "rate": "-12%", "pitch": "-5Hz", "volume": "+0%"},
    "brave": {"voice": "en-US-GuyNeural", "rate": "-8%", "pitch": "-1Hz", "volume": "+1%"},
    "relieved": {"voice": "en-US-JennyNeural", "rate": "-11%", "pitch": "-1Hz", "volume": "+0%"},
    "peaceful": {"voice": "en-US-JennyNeural", "rate": "-14%", "pitch": "-2Hz", "volume": "-1%"},
}

SEARCH_WORDS = {
    "lonely": "lonely animal forest cinematic sad",
    "afraid": "animal rain forest dark cinematic",
    "worried": "animal forest night cinematic",
    "brave": "animal rescue forest cinematic",
    "relieved": "animal warm sunlight forest cinematic",
    "peaceful": "peaceful animal nature cinematic",
    "wonder": "animal magical forest cinematic",
}

def load_font(size, bold=True):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for path in paths:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def safe_query(text, emotion):
    raw = f"{text} {SEARCH_WORDS.get(str(emotion).lower(), 'animal nature cinematic')}"
    raw = re.sub(r"[^A-Za-z0-9 ]+", " ", raw)
    words = [w for w in raw.split() if len(w) > 2]
    banned = {"toby", "shot", "wide", "close", "vertical", "text", "watermark", "pixar", "storybook", "illustration"}
    words = [w for w in words if w.lower() not in banned]
    return " ".join(words[:10]) or SEARCH_WORDS.get(str(emotion).lower(), "animal nature cinematic")

def download_file(url, path, headers=None):
    r = requests.get(url, headers=headers or {}, timeout=90, stream=True)
    r.raise_for_status()
    path.write_bytes(r.content)
    return path

def pexels_video(query, output_path):
    if not PEXELS_API_KEY:
        raise RuntimeError("PEXELS_API_KEY is missing")
    r = requests.get(
        "https://api.pexels.com/videos/search",
        headers={"Authorization": PEXELS_API_KEY},
        params={"query": query, "orientation": "portrait", "per_page": 8, "size": "medium"},
        timeout=60,
    )
    r.raise_for_status()
    videos = r.json().get("videos", [])
    for video in videos:
        files = sorted(video.get("video_files", []), key=lambda x: abs((x.get("width") or 0) - WIDTH) + abs((x.get("height") or 0) - HEIGHT))
        for f in files:
            link = f.get("link")
            if link and (f.get("height") or 0) >= 720:
                return download_file(link, output_path)
    raise RuntimeError("No usable Pexels video")

def pexels_photo(query, output_path):
    if not PEXELS_API_KEY:
        raise RuntimeError("PEXELS_API_KEY is missing")
    r = requests.get(
        "https://api.pexels.com/v1/search",
        headers={"Authorization": PEXELS_API_KEY},
        params={"query": query, "orientation": "portrait", "per_page": 10},
        timeout=60,
    )
    r.raise_for_status()
    photos = r.json().get("photos", [])
    for photo in photos:
        src = photo.get("src", {})
        link = src.get("portrait") or src.get("large2x") or src.get("large")
        if link:
            return download_file(link, output_path)
    raise RuntimeError("No usable Pexels photo")

def pixabay_video(query, output_path):
    if not PIXABAY_API_KEY:
        raise RuntimeError("PIXABAY_API_KEY is missing")
    r = requests.get(
        "https://pixabay.com/api/videos/",
        params={"key": PIXABAY_API_KEY, "q": query, "per_page": 10, "safesearch": "true", "video_type": "film"},
        timeout=60,
    )
    r.raise_for_status()
    hits = r.json().get("hits", [])
    for hit in hits:
        vids = hit.get("videos", {})
        for key in ["large", "medium", "small"]:
            link = vids.get(key, {}).get("url")
            if link:
                return download_file(link, output_path)
    raise RuntimeError("No usable Pixabay video")

def pixabay_photo(query, output_path):
    if not PIXABAY_API_KEY:
        raise RuntimeError("PIXABAY_API_KEY is missing")
    r = requests.get(
        "https://pixabay.com/api/",
        params={"key": PIXABAY_API_KEY, "q": query, "image_type": "photo", "orientation": "vertical", "per_page": 10, "safesearch": "true"},
        timeout=60,
    )
    r.raise_for_status()
    hits = r.json().get("hits", [])
    for hit in hits:
        link = hit.get("largeImageURL") or hit.get("webformatURL")
        if link:
            return download_file(link, output_path)
    raise RuntimeError("No usable Pixabay photo")

def fetch_stock_visual(shot, safe_id, index):
    emotion = shot.get("emotion", "peaceful")
    query = safe_query(f"{shot.get('image_prompt','')} {shot.get('narration_en','')}", emotion)
    attempts = [
        ("pexels_video", pexels_video, VISUALS_DIR / f"visual_{safe_id}_{index:03d}.mp4"),
        ("pixabay_video", pixabay_video, VISUALS_DIR / f"visual_{safe_id}_{index:03d}.mp4"),
        ("pexels_photo", pexels_photo, VISUALS_DIR / f"visual_{safe_id}_{index:03d}.jpg"),
        ("pixabay_photo", pixabay_photo, VISUALS_DIR / f"visual_{safe_id}_{index:03d}.jpg"),
    ]
    errors = []
    for name, func, path in attempts:
        try:
            func(query, path)
            return path, name, query
        except Exception as exc:
            errors.append(f"{name}: {exc}")
    raise RuntimeError("Stock visual failed. Add valid PEXELS_API_KEY and PIXABAY_API_KEY. " + " | ".join(errors[:4]))

def wrap_ltr(draw, text, font, max_width, max_lines=3):
    words = str(text or "").split()
    lines, current = [], ""
    for word in words:
        test = (current + " " + word).strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
            if len(lines) >= max_lines:
                break
    if current and len(lines) < max_lines:
        lines.append(current)
    return lines[:max_lines]

def draw_centered_lines(draw, lines, font, center_y, fill, spacing=9):
    if not lines:
        return
    heights = [draw.textbbox((0, 0), line, font=font)[3] - draw.textbbox((0, 0), line, font=font)[1] for line in lines]
    total_h = sum(heights) + spacing * max(0, len(lines) - 1)
    y = center_y - total_h // 2
    for line, h in zip(lines, heights):
        bbox = draw.textbbox((0, 0), line, font=font)
        x = (WIDTH - (bbox[2] - bbox[0])) // 2
        draw.text((x + 4, y + 4), line, font=font, fill=(0, 0, 0, 220))
        draw.text((x, y), line, font=font, fill=fill)
        y += h + spacing

def prepare_photo(path):
    img = Image.open(path).convert("RGB")
    ratio = max(WIDTH / img.width, HEIGHT / img.height)
    new_size = (int(img.width * ratio), int(img.height * ratio))
    img = img.resize(new_size, Image.LANCZOS)
    left = (img.width - WIDTH) // 2
    top = (img.height - HEIGHT) // 2
    img = img.crop((left, top, left + WIDTH, top + HEIGHT)).convert("RGBA")
    img.alpha_composite(Image.new("RGBA", (WIDTH, 260), (0, 0, 0, 70)), (0, 0))
    img.alpha_composite(Image.new("RGBA", (WIDTH, 380), (0, 0, 0, 110)), (0, HEIGHT - 380))
    return img

def make_frame(video_id, shot_index, shot, title, image_path, total_shots):
    bg = prepare_photo(image_path)
    draw = ImageDraw.Draw(bg)
    brand_font = load_font(40, True)
    title_font = load_font(28, False)
    sub_font = load_font(42, True)
    small_font = load_font(26, False)
    draw.text((50, 34), "Tiny Brave Tails", font=brand_font, fill=(255, 238, 190, 255))
    y = 92
    for line in wrap_ltr(draw, title, title_font, 940, 2):
        draw.text((50, y), line, font=title_font, fill=(245, 245, 245, 235))
        y += 36
    subtitle = os.getenv("SHOW_SUBTITLES", "true").lower() not in {"0", "false", "no"} and (shot.get("subtitle_en") or shot.get("narration_en", "")) or ""
    draw_centered_lines(draw, wrap_ltr(draw, subtitle, sub_font, 930, 3), sub_font, HEIGHT - 210, (255, 255, 255, 255), 8)
    frame_path = FRAMES_DIR / f"frame_{video_id}_{shot_index:03d}.jpg"
    bg.convert("RGB").save(frame_path, quality=95)
    return frame_path

def humanize_text(text):
    clean = re.sub(r"\s+", " ", str(text or "").replace("\n", " ")).strip()
    if not clean:
        raise ValueError("Empty narration text")
    clean = re.sub(r"\bbut\b", "but...", clean, flags=re.I)
    clean = re.sub(r"\bfor a moment\b", "for a moment...", clean, flags=re.I)
    clean = re.sub(r"\bstill\b", "still...", clean, flags=re.I)
    clean = re.sub(r"\.{4,}", "...", clean)
    return clean

async def create_edge_audio_async(text, output_path, emotion="peaceful"):
    style = EMOTION_STYLE.get(str(emotion).lower(), EMOTION_STYLE["peaceful"])
    communicate = edge_tts.Communicate(text=humanize_text(text), voice=style["voice"], rate=style["rate"], pitch=style["pitch"], volume=style["volume"])
    await communicate.save(str(output_path))

def create_edge_audio(text, output_path, emotion="peaceful"):
    asyncio.run(create_edge_audio_async(text, output_path, emotion))
    return output_path

def create_espeak_audio(text, output_path):
    subprocess.run(["espeak-ng", "-v", "en-us", "-s", "118", "-p", "35", "-a", "145", "-w", str(output_path), humanize_text(text)], check=True)
    return output_path

def normalize_audio(input_path, video_id, shot_index):
    normalized = AUDIO_DIR / f"audio_{video_id}_{shot_index:03d}_norm.m4a"
    command = ["ffmpeg", "-y", "-i", str(input_path), "-af", "loudnorm=I=-18:TP=-1.5:LRA=9,acompressor=threshold=-22dB:ratio=2.2:attack=20:release=250", "-ar", "48000", "-ac", "2", "-c:a", "aac", "-b:a", "192k", str(normalized)]
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return normalized
    except Exception:
        return input_path

def create_shot_audio(shot, video_id, shot_index):
    narration = shot.get("narration_en", "").strip()
    emotion = shot.get("emotion", "peaceful").strip().lower()
    mp3_path = AUDIO_DIR / f"audio_{video_id}_{shot_index:03d}.mp3"
    wav_path = AUDIO_DIR / f"audio_{video_id}_{shot_index:03d}.wav"
    try:
        create_edge_audio(narration, mp3_path, emotion)
        voice = EMOTION_STYLE.get(emotion, EMOTION_STYLE["peaceful"])["voice"]
        return normalize_audio(mp3_path, video_id, shot_index), f"edge-multivoice:{voice}:{emotion}"
    except Exception:
        create_espeak_audio(narration, wav_path)
        return normalize_audio(wav_path, video_id, shot_index), "espeak-ng:fallback"

def motion_params(motion, duration):
    if motion == "slow_zoom_out":
        return lambda t: 1.09 - 0.055 * (t / max(duration, 0.1))
    return lambda t: 1.0 + 0.07 * (t / max(duration, 0.1))

def animated_photo_clip(frame_path, duration, motion):
    clip = ImageClip(str(frame_path)).set_duration(duration)
    zoom = motion_params(motion, duration)
    clip = clip.resize(lambda t: zoom(t))
    return clip.set_position(("center", "center")).on_color(size=(WIDTH, HEIGHT), color=(0, 0, 0), pos=("center", "center"))

def stock_video_clip(video_path, duration):
    clip = VideoFileClip(str(video_path)).without_audio()
    if clip.duration > duration:
        start = max(0, (clip.duration - duration) / 2)
        clip = clip.subclip(start, start + duration)
    else:
        clip = clip.loop(duration=duration)
    ratio = max(WIDTH / clip.w, HEIGHT / clip.h)
    clip = clip.resize(ratio)
    clip = clip.crop(x_center=clip.w / 2, y_center=clip.h / 2, width=WIDTH, height=HEIGHT)
    return clip.set_duration(duration)

def split_scene_to_shots(scene):
    if isinstance(scene.get("shots"), list) and scene["shots"]:
        return scene["shots"][:4]
    narration = scene.get("narration_en", "")
    parts = [x.strip() for x in re.split(r"(?<=[.!?])\s+", narration) if x.strip()]
    if len(parts) < 4:
        parts = [narration or "The small animal waited in the quiet forest.", "The night felt too large.", "A small sound changed everything.", "Courage arrived softly."]
    motions = ["slow_zoom_in", "gentle_pan_left", "tiny_handheld", "slow_zoom_out"]
    return [{"shot_number": i + 1, "emotion": scene.get("emotion", "peaceful"), "narration_en": part, "subtitle_en": part, "image_prompt": f"{scene.get('image_prompt','')} {part}", "camera_motion": motions[i % 4], "pause_after": 0.25} for i, part in enumerate(parts[:4])]

def flatten_story(scene_payload):
    shots = []
    character = scene_payload.get("character", {})
    char_desc = character.get("description", "")
    for scene_index, scene in enumerate(scene_payload.get("scenes", []), start=1):
        for shot in split_scene_to_shots(scene):
            prompt = shot.get("image_prompt") or scene.get("image_prompt", "")
            shots.append({"scene_number": scene_index, "shot_number": shot.get("shot_number", len(shots) + 1), "emotion": shot.get("emotion", scene.get("emotion", "peaceful")), "narration_en": shot.get("narration_en") or scene.get("narration_en", ""), "subtitle_en": shot.get("subtitle_en") or shot.get("narration_en") or scene.get("subtitle_en", ""), "image_prompt": f"{char_desc}. {prompt}", "camera_motion": shot.get("camera_motion") or scene.get("camera_motion", "slow_zoom_in"), "pause_after": shot.get("pause_after", 0.25)})
    return shots

def create_video(video_id, title, scene_payload):
    shots = flatten_story(scene_payload)
    if len(shots) < 8:
        raise ValueError(f"Too few shots ({len(shots)}). Regenerate story first.")
    safe_id = re.sub(r"[^A-Za-z0-9_-]", "_", str(video_id).strip() or "video")
    video_path = VIDEO_DIR / f"tiny_brave_tails_{safe_id}.mp4"
    clips, voice_sources, visual_sources = [], [], []
    for i, shot in enumerate(shots, start=1):
        audio_path, voice_source = create_shot_audio(shot, safe_id, i)
        voice_sources.append(voice_source)
        audio_clip = AudioFileClip(str(audio_path))
        duration = max(3.0, audio_clip.duration + min(0.6, max(0.15, float(shot.get("pause_after", 0.25) or 0.25))))
        visual_path, visual_source, query = fetch_stock_visual(shot, safe_id, i)
        visual_sources.append(visual_source)
        if visual_path.suffix.lower() == ".mp4":
            clip = stock_video_clip(visual_path, duration).set_audio(audio_clip)
        else:
            frame_path = make_frame(safe_id, i, shot, title, visual_path, len(shots))
            clip = animated_photo_clip(frame_path, duration, shot.get("camera_motion", "slow_zoom_in")).set_audio(audio_clip)
        clips.append(clip)
        time.sleep(0.1)
    video = concatenate_videoclips(clips, method="compose")
    video.write_videofile(str(video_path), fps=FPS, codec="libx264", audio_codec="aac", preset="medium", threads=2, bitrate="9000k", ffmpeg_params=["-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart"])
    video.close()
    for clip in clips:
        try:
            if clip.audio:
                clip.audio.close()
            clip.close()
        except Exception:
            pass
    return video_path, ",".join(sorted(set(voice_sources))) + f" | visuals={','.join(sorted(set(visual_sources)))} | shots={len(shots)}"

def main():
    client = get_sheets_client()
    spreadsheet = open_spreadsheet(client)
    content_sheet = get_worksheet(spreadsheet, CONTENT_SHEET_NAME)
    logs_sheet = get_logs_worksheet(spreadsheet)
    values = get_all_values(content_sheet)
    headers = values[0]
    id_col = find_column(headers, "id")
    title_col = find_column(headers, "title")
    status_col = find_column(headers, "status")
    scene_prompts_col = find_column(headers, "scene_prompts")
    image_status_col = find_column(headers, "image_status")
    audio_status_col = find_column(headers, "audio_status")
    video_type_col = find_optional_column(headers, "video_type")
    error_message_col = find_optional_column(headers, "error_message")
    requested_video_type = (os.getenv("TBT_VIDEO_TYPE", "") or "").strip().lower().replace("-", "_").replace(" ", "_")
    target_row_number, target_row = None, None
    for index, row in enumerate(values[1:], start=2):
        if get_cell(row, status_col).upper() == "GENERATED":
            row_type = get_cell(row, video_type_col).lower() if video_type_col else ""
            if requested_video_type and row_type and row_type != requested_video_type:
                continue
            target_row_number, target_row = index, row
            break
    if target_row_number is None:
        log(logs_sheet, "", "GENERATE_VIDEO", "No GENERATED row found.")
        print("No GENERATED row found.")
        return
    video_id = get_cell(target_row, id_col)
    title = get_cell(target_row, title_col)
    scene_raw = get_cell(target_row, scene_prompts_col)
    if not title or not scene_raw:
        raise ValueError("Missing title or scene_prompts.")
    scene_payload = json.loads(scene_raw)
    try:
        video_path, voice_source = create_video(video_id, title, scene_payload)
    except Exception as exc:
        if error_message_col:
            update_cell(content_sheet, target_row_number, error_message_col, str(exc)[:1500])
        log(logs_sheet, video_id, "GENERATE_VIDEO_ERROR", str(exc))
        raise
    update_cell(content_sheet, target_row_number, status_col, "VIDEO_CREATED")
    update_cell(content_sheet, target_row_number, image_status_col, "STOCK_CREATED")
    update_cell(content_sheet, target_row_number, audio_status_col, voice_source)
    if error_message_col:
        update_cell(content_sheet, target_row_number, error_message_col, "")
    log(logs_sheet, video_id, "GENERATE_VIDEO", f"Created stock cinematic video: {video_path}. Voice: {voice_source}")
    print(f"Video created: {video_path}")
    print(f"Voice source: {voice_source}")

if __name__ == "__main__":
    main()
