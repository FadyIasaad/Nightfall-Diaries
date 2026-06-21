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
from moviepy.editor import AudioFileClip, CompositeVideoClip, ImageClip, VideoFileClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFilter, ImageFont

if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.LANCZOS

from config import (
    AMBIENT_BED_VOLUME,
    BRAND_STING_VOLUME,
    CHANNEL_NAME,
    DEFAULT_AMBIENT_BED_VOLUME,
    ENABLE_AMBIENT_BED,
    ENABLE_BRAND_STING,
    LOUDNESS_TARGET_LUFS,
    THUMBNAIL_DIR,
)
from nd_common import (
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
    update_optional,
)

CONTENT_SHEET_NAME = "Content"
LOGS_SHEET_NAME = "Logs"
OUTPUT_DIR = Path("output")
FRAMES_DIR = OUTPUT_DIR / "frames"
VISUALS_DIR = OUTPUT_DIR / "visuals"
AUDIO_DIR = OUTPUT_DIR / "audio"
VIDEO_DIR = OUTPUT_DIR / "videos"
THUMB_DIR = THUMBNAIL_DIR
for folder in [OUTPUT_DIR, FRAMES_DIR, VISUALS_DIR, AUDIO_DIR, VIDEO_DIR, THUMB_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

WIDTH = 1080
HEIGHT = 1920
FPS = 24
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "").strip()
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY", "").strip()
USE_STOCK_FIRST = os.getenv("USE_STOCK_FIRST", "false").lower() in {"1", "true", "yes"}

# ─── EMOTION-DRIVEN VOICE SYSTEM ─────────────────────────────────────────────
# One narrator voice for the whole channel, with calibrated rate / pitch / volume
# per emotion so quiet dread, sharp fear, and matter-of-fact confession all feel
# distinct without ever sounding like a different person.
EMOTION_STYLE = {
    "dread":        {"voice": "en-US-AriaNeural", "rate": "-18%", "pitch": "-3Hz", "volume": "+0%"},
    "tension":      {"voice": "en-US-AriaNeural", "rate": "-10%", "pitch": "-1Hz", "volume": "+2%"},
    "eerie":        {"voice": "en-US-AriaNeural", "rate": "-16%", "pitch": "-4Hz", "volume": "-2%"},
    "calm":         {"voice": "en-US-AriaNeural", "rate": "-20%", "pitch": "-2Hz", "volume": "-3%"},
    "fear":         {"voice": "en-US-AriaNeural", "rate": "-8%",  "pitch": "-2Hz", "volume": "+3%"},
    "relief":       {"voice": "en-US-AriaNeural", "rate": "-14%", "pitch": "+1Hz", "volume": "+0%"},
    "mystery":      {"voice": "en-US-AriaNeural", "rate": "-14%", "pitch": "-2Hz", "volume": "+0%"},
    "anger":        {"voice": "en-US-AriaNeural", "rate": "-6%",  "pitch": "-1Hz", "volume": "+4%"},
    "satisfaction": {"voice": "en-US-AriaNeural", "rate": "-12%", "pitch": "+0Hz", "volume": "+1%"},
}

# Inter-sentence pause per emotion (used in SSML <break> tags)
EMOTION_PAUSE = {
    "dread":        "700ms",
    "tension":      "350ms",
    "eerie":        "650ms",
    "calm":         "750ms",
    "fear":         "300ms",
    "relief":       "500ms",
    "mystery":      "550ms",
    "anger":        "280ms",
    "satisfaction": "450ms",
}

SEARCH_WORDS = {
    "dread":        "empty house night cinematic dark",
    "tension":      "dark hallway suspense cinematic",
    "eerie":        "foggy forest night eerie cinematic",
    "calm":         "rain window night quiet cinematic",
    "fear":         "dark figure shadow cinematic night",
    "relief":       "warm light window night cinematic",
    "mystery":      "dark room mystery cinematic",
    "anger":        "storm dark intense cinematic",
    "satisfaction": "quiet sunrise calm cinematic",
}

# ─── FONT HELPERS ─────────────────────────────────────────────────────────────
def load_font(size, bold=True):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"     if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for path in paths:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

# ─── STOCK VISUAL HELPERS ────────────────────────────────────────────────────
def safe_query(text, emotion):
    raw = f"{text} {SEARCH_WORDS.get(str(emotion).lower(), 'dark cinematic night')}"
    raw = re.sub(r"[^A-Za-z0-9 ]+", " ", raw)
    words = [w for w in raw.split() if len(w) > 2]
    banned = {"shot", "wide", "close", "vertical", "text", "watermark", "cinematic", "illustration", "narrator"}
    words = [w for w in words if w.lower() not in banned]
    return " ".join(words[:10]) or SEARCH_WORDS.get(str(emotion).lower(), "dark cinematic night")

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
    emotion = shot.get("emotion", "calm")
    query = safe_query(f"{shot.get('image_prompt','')} {shot.get('narration_en','')}", emotion)
    attempts = [
        ("pexels_video",  pexels_video,  VISUALS_DIR / f"visual_{safe_id}_{index:03d}.mp4"),
        ("pixabay_video", pixabay_video, VISUALS_DIR / f"visual_{safe_id}_{index:03d}.mp4"),
        ("pexels_photo",  pexels_photo,  VISUALS_DIR / f"visual_{safe_id}_{index:03d}.jpg"),
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


# ─── AI CINEMATIC IMAGE (dark, moody Nightfall Diaries look) ─────────────────
def pollinations_cinematic_image(prompt, output_path, seed):
    """
    Generates a dark, moody cinematic still via Pollinations.ai, matching the
    Nightfall Diaries aesthetic: restrained, atmospheric, low-light.
    """
    style_prefix = (
        "ultra-detailed dark cinematic still, moody late-night atmosphere, "
        "deep shadows with a single warm or cold practical light source, subtle film grain, "
        "muted desaturated color palette with one accent color, restrained and suggestive not graphic, "
        "photoreal-painterly hybrid illustration, slow contemplative composition, "
        "faces obscured, in shadow, turned away, or not shown, "
        "no text, no watermark, no logo, vertical 9:16 aspect ratio. "
        "Scene: "
    )
    full_prompt = style_prefix + str(prompt)
    encoded = quote_plus(full_prompt)
    urls = [
        f"https://image.pollinations.ai/prompt/{encoded}?width={WIDTH}&height={HEIGHT}&seed={seed}&nologo=true&enhance=true&model=flux",
        f"https://image.pollinations.ai/prompt/{encoded}?width={WIDTH}&height={HEIGHT}&seed={seed}&nologo=true&enhance=true",
        f"https://pollinations.ai/p/{encoded}?width={WIDTH}&height={HEIGHT}&seed={seed}&nologo=true",
    ]
    last_error = None
    for url in urls:
        try:
            r = requests.get(url, timeout=150)
            r.raise_for_status()
            output_path.write_bytes(r.content)
            with Image.open(output_path) as img:
                img.verify()
            return output_path
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"AI cinematic image failed: {last_error}")


# ─── SUBTITLE / FRAME HELPERS ─────────────────────────────────────────────────
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
    heights = [
        draw.textbbox((0, 0), line, font=font)[3] - draw.textbbox((0, 0), line, font=font)[1]
        for line in lines
    ]
    total_h = sum(heights) + spacing * max(0, len(lines) - 1)
    y = center_y - total_h // 2
    for line, h in zip(lines, heights):
        bbox = draw.textbbox((0, 0), line, font=font)
        x = (WIDTH - (bbox[2] - bbox[0])) // 2
        for dx, dy in [(-3, -3), (3, -3), (-3, 3), (3, 3), (0, 4), (0, -4)]:
            draw.text((x + dx, y + dy), line, font=font, fill=(0, 0, 0, 210))
        draw.text((x, y), line, font=font, fill=fill)
        y += h + spacing

def prepare_photo(path):
    """
    Prepare a visual frame. Darker overlays than a bright/warm channel would
    use, to keep the late-night Nightfall Diaries mood consistent.
    """
    img = Image.open(path).convert("RGB")
    ratio = max(WIDTH / img.width, HEIGHT / img.height)
    new_size = (int(img.width * ratio), int(img.height * ratio))
    img = img.resize(new_size, Image.LANCZOS)
    left = (img.width - WIDTH) // 2
    top  = (img.height - HEIGHT) // 2
    img = img.crop((left, top, left + WIDTH, top + HEIGHT)).convert("RGBA")
    # Header gradient (branding area)
    img.alpha_composite(Image.new("RGBA", (WIDTH, 170), (0, 0, 0, 90)), (0, 0))
    # Subtitle gradient at bottom
    img.alpha_composite(Image.new("RGBA", (WIDTH, 340), (0, 0, 0, 150)), (0, HEIGHT - 340))
    return img

def make_frame(video_id, shot_index, shot, title, image_path, total_shots):
    bg = prepare_photo(image_path)
    draw = ImageDraw.Draw(bg)

    brand_font = load_font(40, bold=True)
    title_font = load_font(26, bold=False)
    sub_font   = load_font(44, bold=True)

    # Brand name
    draw.text((50, 34), CHANNEL_NAME, font=brand_font, fill=(200, 210, 230, 255))
    # Episode title (2 lines max)
    y = 94
    for line in wrap_ltr(draw, title, title_font, 940, 2):
        draw.text((50, y), line, font=title_font, fill=(225, 225, 230, 220))
        y += 36

    subtitle = ""
    if os.getenv("SHOW_SUBTITLES", "true").lower() not in {"0", "false", "no"}:
        subtitle = (shot.get("subtitle_en") or shot.get("narration_en", "")).strip()

    draw_centered_lines(
        draw,
        wrap_ltr(draw, subtitle, sub_font, 950, 3),
        sub_font,
        HEIGHT - 210,
        (235, 235, 240, 255),
        spacing=10,
    )

    frame_path = FRAMES_DIR / f"frame_{video_id}_{shot_index:03d}.jpg"
    bg.convert("RGB").save(frame_path, quality=95)
    return frame_path


def make_subtitle_overlay(video_id, shot_index, shot, title):
    """
    Same caption styling as make_frame, but rendered onto a transparent layer
    instead of a background photo. Used to burn captions onto stock video
    clips, which previously had no subtitle text at all.
    """
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    brand_font = load_font(40, bold=True)
    title_font = load_font(26, bold=False)
    sub_font   = load_font(44, bold=True)

    # Soft gradient strips behind the brand/title area and the subtitle area
    # so captions stay readable over busy stock footage.
    overlay.alpha_composite(Image.new("RGBA", (WIDTH, 170), (0, 0, 0, 90)), (0, 0))
    overlay.alpha_composite(Image.new("RGBA", (WIDTH, 340), (0, 0, 0, 150)), (0, HEIGHT - 340))

    draw.text((50, 34), CHANNEL_NAME, font=brand_font, fill=(200, 210, 230, 255))
    y = 94
    for line in wrap_ltr(draw, title, title_font, 940, 2):
        draw.text((50, y), line, font=title_font, fill=(225, 225, 230, 220))
        y += 36

    subtitle = ""
    if os.getenv("SHOW_SUBTITLES", "true").lower() not in {"0", "false", "no"}:
        subtitle = (shot.get("subtitle_en") or shot.get("narration_en", "")).strip()

    draw_centered_lines(
        draw,
        wrap_ltr(draw, subtitle, sub_font, 950, 3),
        sub_font,
        HEIGHT - 210,
        (235, 235, 240, 255),
        spacing=10,
    )

    overlay_path = FRAMES_DIR / f"caption_{video_id}_{shot_index:03d}.png"
    overlay.save(overlay_path)
    return overlay_path


# ─── THUMBNAIL GENERATION ──────────────────────────────────────────────────────
def generate_thumbnail(video_id, title, image_path):
    """
    Builds a simple high-contrast custom thumbnail from one of the episode's
    own cinematic stills: dark gradient band, bold title text. No extra API
    calls or paid tools, just PIL on an image already generated for the video.
    """
    thumb_w, thumb_h = 1280, 720
    try:
        img = Image.open(image_path).convert("RGB")
    except Exception:
        img = Image.new("RGB", (thumb_w, thumb_h), (10, 10, 14))

    ratio = max(thumb_w / img.width, thumb_h / img.height)
    new_size = (int(img.width * ratio), int(img.height * ratio))
    img = img.resize(new_size, Image.LANCZOS)
    left = (img.width - thumb_w) // 2
    top = (img.height - thumb_h) // 2
    img = img.crop((left, top, left + thumb_w, top + thumb_h)).convert("RGBA")

    # Darken slightly overall, then a stronger gradient band behind the title
    # so bold text stays readable over any background.
    img.alpha_composite(Image.new("RGBA", (thumb_w, thumb_h), (0, 0, 0, 60)))
    band_h = 260
    img.alpha_composite(Image.new("RGBA", (thumb_w, band_h), (0, 0, 0, 175)), (0, thumb_h - band_h))

    draw = ImageDraw.Draw(img)
    title_font = load_font(72, bold=True)
    brand_font = load_font(34, bold=True)

    lines = wrap_ltr(draw, title, title_font, thumb_w - 100, max_lines=2)
    total_h = len(lines) * 84
    y = thumb_h - band_h + (band_h - total_h) // 2 - 10
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=title_font)
        x = (thumb_w - (bbox[2] - bbox[0])) // 2
        for dx, dy in [(-4, -4), (4, -4), (-4, 4), (4, 4)]:
            draw.text((x + dx, y + dy), line, font=title_font, fill=(0, 0, 0, 230))
        draw.text((x, y), line, font=title_font, fill=(245, 245, 250, 255))
        y += 84

    draw.text((40, 30), CHANNEL_NAME.upper(), font=brand_font, fill=(230, 200, 120, 255))

    thumb_path = THUMB_DIR / f"thumb_{video_id}.jpg"
    img.convert("RGB").save(thumb_path, quality=92)
    return thumb_path


# ─── VOICE: HUMANIZE + SSML AUDIO ────────────────────────────────────────────
def humanize_text(text):
    clean = re.sub(r"\s+", " ", str(text or "").replace("\n", " ")).strip()
    if not clean:
        raise ValueError("Empty narration text")
    clean = re.sub(r"\.{4,}", "...", clean)
    return clean


def _build_ssml(text: str, emotion: str, style: dict) -> str:
    pause = EMOTION_PAUSE.get(emotion, "480ms")
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    if not sentences:
        sentences = [text]

    def esc(t):
        return (t.replace("&", "&amp;")
                 .replace("<", "&lt;")
                 .replace(">", "&gt;")
                 .replace('"', "&quot;"))

    body = "".join(f"<s>{esc(s)}</s><break time='{pause}'/>" for s in sentences)

    return (
        "<speak version='1.0' "
        "xmlns='http://www.w3.org/2001/10/synthesis' "
        "xml:lang='en-US'>"
        f"<voice name='{style['voice']}'>"
        f"<prosody rate='{style['rate']}' "
        f"pitch='{style['pitch']}' "
        f"volume='{style['volume']}'>"
        f"{body}"
        "</prosody></voice></speak>"
    )


async def create_edge_audio_async(text, output_path, emotion="calm"):
    style = EMOTION_STYLE.get(str(emotion).lower(), EMOTION_STYLE["calm"])
    voice = style["voice"]
    clean = humanize_text(text)

    try:
        ssml = _build_ssml(clean, emotion, style)
        communicate = edge_tts.Communicate(text=ssml, voice=voice)
        await communicate.save(str(output_path))
        return
    except Exception:
        pass

    communicate = edge_tts.Communicate(
        text=clean,
        voice=voice,
        rate=style["rate"],
        pitch=style["pitch"],
        volume=style["volume"],
    )
    await communicate.save(str(output_path))


def create_edge_audio(text, output_path, emotion="calm"):
    asyncio.run(create_edge_audio_async(text, output_path, emotion))
    return output_path

def create_espeak_audio(text, output_path):
    subprocess.run(
        ["espeak-ng", "-v", "en-us", "-s", "112", "-p", "30", "-a", "140",
         "-w", str(output_path), humanize_text(text)],
        check=True,
    )
    return output_path

def normalize_audio(input_path, video_id, shot_index):
    normalized = AUDIO_DIR / f"audio_{video_id}_{shot_index:03d}_norm.m4a"
    command = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-af", "loudnorm=I=-14:TP=-1.5:LRA=11,acompressor=threshold=-22dB:ratio=2.2:attack=20:release=250",
        "-ar", "48000", "-ac", "2", "-c:a", "aac", "-b:a", "192k",
        str(normalized),
    ]
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return normalized
    except Exception:
        return input_path

def create_shot_audio(shot, video_id, shot_index):
    narration = shot.get("narration_en", "").strip()
    emotion   = shot.get("emotion", "calm").strip().lower()
    mp3_path  = AUDIO_DIR / f"audio_{video_id}_{shot_index:03d}.mp3"
    wav_path  = AUDIO_DIR / f"audio_{video_id}_{shot_index:03d}.wav"
    try:
        create_edge_audio(narration, mp3_path, emotion)
        voice = EMOTION_STYLE.get(emotion, EMOTION_STYLE["calm"])["voice"]
        return normalize_audio(mp3_path, video_id, shot_index), f"edge-ssml:{voice}:{emotion}"
    except Exception:
        create_espeak_audio(narration, wav_path)
        return normalize_audio(wav_path, video_id, shot_index), "espeak-ng:fallback"


# ─── AMBIENT SOUND BED (generated, not sourced — zero copyright risk) ────────
def build_ambient_bed(duration_seconds, output_path):
    """
    Generates a quiet rain/drone ambient bed entirely with ffmpeg's built-in
    audio sources (anoisesrc + aevalsrc). Nothing is downloaded, so there is
    no licensing risk, and it never depends on a third-party music API.
    """
    duration = max(3.0, float(duration_seconds))
    fade_out_start = max(0.0, duration - 6.0)
    filter_complex = (
        "[0:a]lowpass=f=700,highpass=f=80,volume=0.5[rain];"
        "[1:a]volume=0.35[drone];"
        "[rain][drone]amix=inputs=2:duration=longest:normalize=0[bed];"
        f"[bed]afade=t=in:st=0:d=5,afade=t=out:st={fade_out_start:.2f}:d=6[out]"
    )
    command = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"anoisesrc=color=brown:amplitude=1:duration={duration:.2f}",
        "-f", "lavfi", "-i", f"aevalsrc=0.3*sin(2*PI*55*t):duration={duration:.2f}",
        "-filter_complex", filter_complex,
        "-map", "[out]", "-ac", "2", "-ar", "48000",
        str(output_path),
    ]
    subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return output_path


def build_brand_sting(output_path, duration=1.6):
    """
    Generates a short two-tone chime entirely with ffmpeg's built-in audio
    sources, the same zero-copyright-risk approach as the ambient bed. Mixed
    in at the very start of every video for channel recognition.
    """
    filter_complex = (
        "[0:a]volume=1.0,afade=t=in:st=0:d=0.05,afade=t=out:st=0.55:d=0.35[note1];"
        "[1:a]volume=0.8,afade=t=in:st=0:d=0.05,afade=t=out:st=0.85:d=0.45[note2];"
        "[note1][note2]concat=n=2:v=0:a=1[chime]"
    )
    command = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "aevalsrc=0.35*sin(2*PI*392*t):duration=0.65",
        "-f", "lavfi", "-i", "aevalsrc=0.30*sin(2*PI*523*t):duration=0.95",
        "-filter_complex", filter_complex,
        "-map", "[chime]", "-ac", "2", "-ar", "48000",
        str(output_path),
    ]
    subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return output_path


def add_ambient_bed(video_path: Path, ambient_volume: float = 0.10, sting_volume: float = 0.0) -> bool:
    """
    Mixes the generated ambient bed quietly under the video's existing
    narration track, and (if sting_volume > 0) overlays the brand sting at the
    very start. Wrapped so a failure here never breaks the whole render; the
    video is still perfectly usable without these layers.
    """
    bed_path = None
    sting_path = None
    mixed_path = None
    try:
        with VideoFileClip(str(video_path)) as probe:
            duration = probe.duration
        bed_path = video_path.with_name(video_path.stem + "_ambient_bed.wav")
        build_ambient_bed(duration, bed_path)
        mixed_path = video_path.with_name(video_path.stem + "_mixed.mp4")

        inputs = ["-i", str(video_path), "-i", str(bed_path)]
        if sting_volume > 0:
            sting_path = video_path.with_name(video_path.stem + "_sting.wav")
            build_brand_sting(sting_path)
            inputs += ["-i", str(sting_path)]
            filter_complex = (
                f"[1:a]volume={ambient_volume}[amb];"
                f"[2:a]volume={sting_volume}[sting];"
                "[0:a][amb][sting]amix=inputs=3:duration=first:normalize=0[aout]"
            )
        else:
            filter_complex = f"[1:a]volume={ambient_volume}[amb];[0:a][amb]amix=inputs=2:duration=first:normalize=0[aout]"

        command = [
            "ffmpeg", "-y", *inputs,
            "-filter_complex", filter_complex,
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            str(mixed_path),
        ]
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        mixed_path.replace(video_path)
        return True
    except Exception as exc:
        print(f"Ambient bed / sting skipped (non-fatal): {exc}")
        return False
    finally:
        for p in (bed_path, sting_path, mixed_path):
            try:
                if p and p.exists():
                    p.unlink()
            except Exception:
                pass


def normalize_final_loudness(video_path: Path, target_lufs: float = -14.0) -> bool:
    """
    Final loudness pass over the fully mixed video (narration + ambient + sting
    already combined), so every upload lands at the same perceived loudness
    regardless of how the layers above summed. Non-fatal on failure.
    """
    normalized_path = video_path.with_name(video_path.stem + "_loudnorm.mp4")
    try:
        command = [
            "ffmpeg", "-y", "-i", str(video_path),
            "-af", f"loudnorm=I={target_lufs}:TP=-1.5:LRA=11",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            str(normalized_path),
        ]
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        normalized_path.replace(video_path)
        return True
    except Exception as exc:
        print(f"Final loudness normalization skipped (non-fatal): {exc}")
        return False
    finally:
        try:
            if normalized_path.exists():
                normalized_path.unlink()
        except Exception:
            pass


def add_audio_sting(video_path: Path) -> bool:
    """
    Prepends a 1.2-second low-volume brand sting (soft sine sweep 220→440 Hz)
    to the video. Fails silently so a missing ffmpeg filter never blocks the render.
    """
    sting_path = None
    output_path = None
    try:
        sting_path = video_path.with_name(video_path.stem + "_sting.wav")
        output_path = video_path.with_name(video_path.stem + "_stinged.mp4")
        # Generate sting: 1.2s sine sweep 220→440 Hz, fade in+out, very quiet (-20 dB)
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", "sine=frequency=220:beep_factor=2:duration=1.2",
            "-af", "volume=-20dB,afade=t=in:ss=0:d=0.15,afade=t=out:st=1.0:d=0.2",
            str(sting_path),
        ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # Mix sting quietly under the start of the video audio
        subprocess.run([
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(sting_path),
            "-filter_complex",
            "[1:a]volume=0.35[s];[0:a][s]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            str(output_path),
        ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output_path.replace(video_path)
        return True
    except Exception as exc:
        print(f"Audio sting skipped (non-fatal): {exc}")
        return False
    finally:
        for p in (sting_path, output_path):
            try:
                if p and p.exists():
                    p.unlink()
            except Exception:
                pass

# ─── VIDEO CLIP HELPERS ───────────────────────────────────────────────────────
def motion_params(motion, duration):
    if motion == "slow_zoom_out":
        return lambda t: 1.09 - 0.055 * (t / max(duration, 0.1))
    return lambda t: 1.0 + 0.07 * (t / max(duration, 0.1))

def animated_photo_clip(frame_path, duration, motion):
    clip = ImageClip(str(frame_path)).set_duration(duration)
    zoom = motion_params(motion, duration)
    clip = clip.resize(lambda t: zoom(t))
    return clip.set_position(("center", "center")).on_color(
        size=(WIDTH, HEIGHT), color=(0, 0, 0), pos=("center", "center")
    )

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


# ─── STORY → FLAT SHOT LIST ───────────────────────────────────────────────────
def split_scene_to_shots(scene):
    if isinstance(scene.get("shots"), list) and scene["shots"]:
        return scene["shots"][:4]
    narration = scene.get("narration_en", "")
    parts = [x.strip() for x in re.split(r"(?<=[.!?])\s+", narration) if x.strip()]
    if len(parts) < 4:
        parts = [
            narration or "The room was quiet, in a way that felt deliberate.",
            "The night felt too large around it.",
            "A small sound changed everything.",
            "Whatever it was, it was not finished yet.",
        ]
    motions = ["slow_zoom_in", "gentle_pan_left", "tiny_handheld", "slow_zoom_out"]
    return [
        {
            "shot_number":  i + 1,
            "emotion":      scene.get("emotion", "calm"),
            "narration_en": part,
            "subtitle_en":  part,
            "image_prompt": f"{scene.get('image_prompt','')} {part}",
            "camera_motion": motions[i % 4],
            "pause_after":  0.25,
        }
        for i, part in enumerate(parts[:4])
    ]

def flatten_story(scene_payload):
    shots = []
    for scene_index, scene in enumerate(scene_payload.get("scenes", []), start=1):
        for shot in split_scene_to_shots(scene):
            prompt = shot.get("image_prompt") or scene.get("image_prompt", "")
            shots.append({
                "scene_number": scene_index,
                "shot_number":  shot.get("shot_number", len(shots) + 1),
                "emotion":      shot.get("emotion", scene.get("emotion", "calm")),
                "narration_en": shot.get("narration_en") or scene.get("narration_en", ""),
                "subtitle_en":  shot.get("subtitle_en") or shot.get("narration_en") or scene.get("subtitle_en", ""),
                "image_prompt": prompt,
                "camera_motion": shot.get("camera_motion") or scene.get("camera_motion", "slow_zoom_in"),
                "pause_after":  shot.get("pause_after", 0.25),
            })
    return shots


# ─── VISUAL FETCH (AI primary, stock fallback) ────────────────────────────────
def fetch_visual(shot, safe_id, index, numeric_seed):
    prompt = (
        f"{shot.get('image_prompt','')} "
        f"Emotion: {shot.get('emotion','calm')}. "
        f"Moment: {shot.get('narration_en','')}"
    )
    cinematic_path = VISUALS_DIR / f"visual_{safe_id}_{index:03d}.jpg"
    if not USE_STOCK_FIRST:
        try:
            pollinations_cinematic_image(prompt, cinematic_path, seed=numeric_seed * 1000 + index)
            return cinematic_path, "ai_cinematic", "dark cinematic still"
        except Exception as exc:
            print(f"AI cinematic image failed for shot {index}, trying stock backup: {exc}")
    try:
        return fetch_stock_visual(shot, safe_id, index)
    except Exception as stock_exc:
        if USE_STOCK_FIRST:
            pollinations_cinematic_image(prompt, cinematic_path, seed=numeric_seed * 1000 + index)
            return cinematic_path, "ai_cinematic_after_stock", "dark cinematic still"
        raise RuntimeError(
            f"All visual sources failed for shot {index}. "
            f"AI cinematic + stock backup failed: {stock_exc}"
        ) from stock_exc


# ─── MAIN VIDEO BUILDER ───────────────────────────────────────────────────────
def extract_thumbnail_source_frame(video_path: Path) -> Path:
    """Fallback for when every shot used stock video (no still image to reuse)."""
    frame_path = video_path.with_name(video_path.stem + "_thumb_source.jpg")
    try:
        with VideoFileClip(str(video_path)) as clip:
            t = min(2.0, max(0.0, clip.duration * 0.1))
            clip.save_frame(str(frame_path), t=t)
    except Exception as exc:
        print(f"Thumbnail source frame extraction failed (non-fatal): {exc}")
    return frame_path


def create_video(video_id, title, scene_payload, video_type="horror_story"):
    shots = flatten_story(scene_payload)
    if len(shots) < 8:
        raise ValueError(f"Too few shots ({len(shots)}). Regenerate story first.")
    safe_id    = re.sub(r"[^A-Za-z0-9_-]", "_", str(video_id).strip() or "video")
    video_path = VIDEO_DIR / f"nightfall_diaries_{safe_id}.mp4"
    clips, voice_sources, visual_sources = [], [], []
    thumb_source_path = None

    for i, shot in enumerate(shots, start=1):
        audio_path, voice_source = create_shot_audio(shot, safe_id, i)
        voice_sources.append(voice_source)
        audio_clip = AudioFileClip(str(audio_path))
        duration = max(3.0, audio_clip.duration + min(0.6, max(0.15, float(shot.get("pause_after", 0.25) or 0.25))))

        visual_path, visual_source, query = fetch_stock_visual(shot, safe_id, i)
        visual_sources.append(visual_source)

        if visual_path.suffix.lower() == ".mp4":
            base_clip = stock_video_clip(visual_path, duration)
            caption_path = make_subtitle_overlay(safe_id, i, shot, title)
            caption_clip = ImageClip(str(caption_path)).set_duration(duration)
            clip = CompositeVideoClip([base_clip, caption_clip], size=(WIDTH, HEIGHT)).set_audio(audio_clip)
        else:
            if thumb_source_path is None:
                thumb_source_path = visual_path
            frame_path = make_frame(safe_id, i, shot, title, visual_path, len(shots))
            clip = animated_photo_clip(frame_path, duration, shot.get("camera_motion", "slow_zoom_in")).set_audio(audio_clip)

        clips.append(clip)
        time.sleep(0.1)

    video = concatenate_videoclips(clips, method="compose")
    video.write_videofile(
        str(video_path),
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        threads=2,
        bitrate="9000k",
        ffmpeg_params=["-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
    )
    video.close()
    for clip in clips:
        try:
            if clip.audio:
                clip.audio.close()
            clip.close()
        except Exception:
            pass

    normalized_type = str(video_type or "horror_story").strip().lower().replace("-", "_").replace(" ", "_")
    ambient_volume = AMBIENT_BED_VOLUME.get(normalized_type, DEFAULT_AMBIENT_BED_VOLUME)
    sting_volume = BRAND_STING_VOLUME if ENABLE_BRAND_STING else 0.0

    ambient_applied = False
    if ENABLE_AMBIENT_BED or sting_volume > 0:
        ambient_applied = add_ambient_bed(video_path, ambient_volume, sting_volume)

    loudness_applied = normalize_final_loudness(video_path, LOUDNESS_TARGET_LUFS)

    if thumb_source_path is None:
        thumb_source_path = extract_thumbnail_source_frame(video_path)
    thumb_path = generate_thumbnail(safe_id, title, thumb_source_path)

    summary = (
        ",".join(sorted(set(voice_sources)))
        + f" | visuals={','.join(sorted(set(visual_sources)))}"
        + f" | shots={len(shots)}"
        + f" | ambient={'on' if ambient_applied else 'off'}"
        + f" | loudnorm={'on' if loudness_applied else 'off'}"
    )
    return video_path, summary, thumb_path


# ─── ENTRY POINT ─────────────────────────────────────────────────────────────
def main():
    client = get_sheets_client()
    spreadsheet = open_spreadsheet(client)
    content_sheet = get_worksheet(spreadsheet, CONTENT_SHEET_NAME)
    logs_sheet    = get_logs_worksheet(spreadsheet)
    values  = get_all_values(content_sheet)
    headers = values[0]

    id_col           = find_column(headers, "id")
    title_col        = find_column(headers, "title")
    status_col       = find_column(headers, "status")
    scene_prompts_col = find_column(headers, "scene_prompts")
    image_status_col = find_column(headers, "image_status")
    audio_status_col = find_column(headers, "audio_status")
    video_type_col   = find_optional_column(headers, "video_type")
    error_message_col = find_optional_column(headers, "error_message")
    thumbnail_path_col = find_optional_column(headers, "thumbnail_path")

    requested_video_type = (
        (os.getenv("TBT_VIDEO_TYPE", "") or "")
        .strip().lower().replace("-", "_").replace(" ", "_")
    )

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

    video_id   = get_cell(target_row, id_col)
    title      = get_cell(target_row, title_col)
    scene_raw  = get_cell(target_row, scene_prompts_col)
    row_video_type = get_cell(target_row, video_type_col) if video_type_col else "horror_story"
    if not title or not scene_raw:
        raise ValueError("Missing title or scene_prompts.")
    scene_payload = json.loads(scene_raw)

    try:
        video_path, voice_source, thumb_path = create_video(video_id, title, scene_payload, row_video_type)
    except Exception as exc:
        if error_message_col:
            update_cell(content_sheet, target_row_number, error_message_col, str(exc)[:1500])
        log(logs_sheet, video_id, "GENERATE_VIDEO_ERROR", str(exc))
        raise

    update_cell(content_sheet, target_row_number, status_col,       "VIDEO_CREATED")
    update_cell(content_sheet, target_row_number, image_status_col, "CREATED")
    update_cell(content_sheet, target_row_number, audio_status_col, voice_source)
    update_optional(content_sheet, target_row_number, thumbnail_path_col, str(thumb_path))
    if error_message_col:
        update_cell(content_sheet, target_row_number, error_message_col, "")
    log(logs_sheet, video_id, "GENERATE_VIDEO",
        f"Created video: {video_path}. Voice: {voice_source}. Thumbnail: {thumb_path}")
    print(f"Video created: {video_path}")
    print(f"Voice source: {voice_source}")
    print(f"Thumbnail created: {thumb_path}")


if __name__ == "__main__":
    main()
