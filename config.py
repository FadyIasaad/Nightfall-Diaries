# Runtime settings for Nightfall Diaries.
# Secrets stay in GitHub Secrets, not in this file.
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
AUDIO_DIR = OUTPUT_DIR / "audio"
VISUAL_DIR = OUTPUT_DIR / "visuals"
VIDEO_DIR = OUTPUT_DIR / "videos"
METADATA_DIR = OUTPUT_DIR / "metadata"

CHANNEL_NAME = "Nightfall Diaries"
DEFAULT_VIDEO_PRIVACY = "private"
DEFAULT_PRIVACY_STATUS = DEFAULT_VIDEO_PRIVACY
DEFAULT_MADE_FOR_KIDS = False
YOUTUBE_CATEGORY_ID = "24"  # Entertainment

# One calm, controlled narrator voice for the whole channel. It carries both
# quiet horror dread and matter-of-fact confession/revenge storytelling well,
# and a single consistent voice is what makes a channel feel like "a place"
# rather than a random AI feed.
DEFAULT_EDGE_TTS_VOICE = "en-US-AriaNeural"

CHANNEL_POSITIONING = (
    "Real-feeling late-night stories for adults: true-crime-style confessions, "
    "betrayal and revenge accounts, and quiet psychological horror. Narrated slowly "
    "over dark cinematic visuals with a soft ambient sound bed underneath, built to "
    "watch, unwind, or fall asleep to."
)

# There is no fixed mascot. Every story has a different first-person narrator
# and cast, described fresh per story in the Content sheet. This is the
# fallback used when a row does not specify one.
DEFAULT_NARRATOR_STYLE = (
    "an anonymous adult narrator speaking in first person, calm and a little tired, "
    "like someone telling you something true very late at night"
)

# ─── VISUAL STYLE ────────────────────────────────────────────────────────────
# Dark, moody, cinematic — built for low-light viewing. Visual identity leans on
# atmosphere, objects, and silhouettes rather than detailed recurring character
# faces, since this channel covers a different real-feeling story every episode.
CINEMATIC_VISUAL_STYLE = (
    "ultra-detailed dark cinematic still, moody late-night atmosphere, "
    "deep shadows with a single warm or cold practical light source, subtle film grain, "
    "muted desaturated color palette with one accent color, "
    "rain-streaked windows, empty rooms, quiet streets, foggy treelines, hallway light under a door, "
    "restrained and suggestive rather than graphic or gory, "
    "photoreal-painterly hybrid illustration, slow contemplative composition, "
    "faces obscured, in shadow, turned away, or not shown, "
    "no text, no watermark, no logo, vertical 9:16 aspect ratio"
)

VIDEO_TYPES = {
    "short": {
        "category": "hook_short",
        "duration_minutes": 1,
        "scene_count": 6,
        "shots_per_scene": 4,
        "mood": "tense_hook",
        "made_for_kids": False,
    },
    "horror_story": {
        "category": "horror_story",
        "duration_minutes": 18,
        "scene_count": 26,
        "shots_per_scene": 4,
        "mood": "slow_dread",
        "made_for_kids": False,
    },
    "confession_story": {
        "category": "confession_story",
        "duration_minutes": 16,
        "scene_count": 24,
        "shots_per_scene": 4,
        "mood": "betrayal_and_release",
        "made_for_kids": False,
    },
}

# ─── AMBIENT SOUND BED ───────────────────────────────────────────────────────
# A quiet, fully generated (not sourced) rain/drone bed is mixed under every
# narration track. Generated, not downloaded, so there is zero copyright risk.
# This is what gives the channel its "fall asleep to" quality.
ENABLE_AMBIENT_BED = True
# Shorts are usually watched on a phone speaker in a noisier environment, so the
# bed sits quieter there; long-form is usually watched with headphones at night,
# so it can sit a little more present. Falls back to "horror_story" level for
# any video_type not listed here.
AMBIENT_BED_VOLUME = {
    "short": 0.09,
    "horror_story": 0.14,
    "confession_story": 0.14,
}
DEFAULT_AMBIENT_BED_VOLUME = 0.14

# ─── FINAL LOUDNESS NORMALIZATION ────────────────────────────────────────────
# Applied as the last pass on the fully mixed video so every upload lands at a
# consistent loudness and viewers never have to reach for the volume knob
# between videos. -14 LUFS is YouTube's own reference target.
LOUDNESS_TARGET_LUFS = -14.0

# ─── BRAND STING ──────────────────────────────────────────────────────────────
# A short, fully generated (not sourced) two-tone chime mixed in at the very
# start of every video for channel recognition. Same zero-copyright-risk
# approach as the ambient bed: synthesized with ffmpeg, nothing downloaded.
ENABLE_BRAND_STING = True
BRAND_STING_VOLUME = 0.45

# ─── THUMBNAILS ───────────────────────────────────────────────────────────────
THUMBNAIL_DIR = OUTPUT_DIR / "thumbnails"

# ─── STORY GENERATION: CHUNKING & MODEL FALLBACK ─────────────────────────────
# Chunked generation writes a long story in several model calls (intro, middle
# beats, ending) instead of one big call. This raises quality and length on
# long-form, BUT it uses 4-6 model calls per story instead of 1. On Gemini's
# free tier (5 requests/minute) that will hit the quota, so it is OFF by
# default and should only be turned on once billing is enabled.
# Set ENABLE_STORY_CHUNKING=1 in the environment to turn it on.
ENABLE_STORY_CHUNKING = os.getenv("ENABLE_STORY_CHUNKING", "0").strip().lower() in {"1", "true", "yes"}
# Shorts are always single-call regardless of the flag (they are tiny).
STORY_CHUNK_MIN_MINUTES = 8  # only chunk stories at/above this target length

# If the primary model fails (quota, transient error), try these in order.
# The first that succeeds wins. Only currently free-tier-eligible models:
# gemini-2.0-flash / gemini-2.0-flash-lite were retired on 2026-03-03 (free-tier
# quota went to 0), so they are removed. As of 2026 the free text models are
# gemini-2.5-flash (250 req/day) and gemini-2.5-flash-lite (1000 req/day) — the
# lite model has the higher daily quota, making it a strong last-resort fallback.
GEMINI_MODEL_FALLBACKS = [
    os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    "gemini-2.5-flash-lite",
]

# ─── LOCAL STORY BACKUP (artifact) ───────────────────────────────────────────
# Every generated story is also saved as a JSON file under output/stories so
# the work is never lost if the Google Sheet write fails. Picked up by the
# workflow's upload-artifact step.
STORY_BACKUP_DIR = OUTPUT_DIR / "stories"

# ─── VIDEO POLISH: TRANSITIONS, WATERMARK, CHAPTERS, END SCREEN ───────────────
# Short crossfade between shots instead of a hard cut. Kept small so it never
# feels gimmicky. Seconds.
ENABLE_TRANSITIONS = True
TRANSITION_SECONDS = 0.4

# Small persistent channel watermark in a corner of every frame.
ENABLE_WATERMARK = True
WATERMARK_TEXT = CHANNEL_NAME
WATERMARK_OPACITY = 110  # 0-255

# Chapters: write a chapter list (00:00 Title ...) into the description for
# long-form videos so YouTube shows "key moments". Shorts are never chaptered.
ENABLE_CHAPTERS = True
CHAPTERS_MIN_SCENES = 6

# End screen: append a short spoken + on-screen call to watch another story on
# long-form videos. The actual "linked" end-screen element is set in YouTube
# Studio; here we add the verbal/visual nudge that earns the extra watch time.
ENABLE_END_SCREEN = True
END_SCREEN_SECONDS = 6
