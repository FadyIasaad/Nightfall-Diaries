# Runtime settings for Nightfall Diaries.
# Secrets stay in GitHub Secrets, not in this file.
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
AMBIENT_BED_VOLUME = 0.10  # 0.0–1.0, relative level under the narration
