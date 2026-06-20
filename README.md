# Nightfall Diaries

A fully automated YouTube channel pipeline: Google Sheets as the state store, Gemini for story
writing, edge-tts + AI/stock visuals for video rendering, and the YouTube Data API for upload —
all driven by GitHub Actions, no PC required.

This is a **separate, standalone channel and repo**. It is architecturally forked from an existing
animal-story channel pipeline, but produces completely different content: real-feeling late-night
stories for adults — confessions, betrayal/revenge accounts, and quiet psychological horror —
narrated slowly over dark cinematic visuals with a soft generated ambient sound bed underneath.
Built to watch, unwind, or fall asleep to.

## Video types

| video_type | length | description |
|---|---|---|
| `short` | ~60–90s | a single hook story for YouTube Shorts |
| `horror_story` | ~18 min | a slow-burn psychological horror story |
| `confession_story` | ~16 min | a betrayal / revenge confession story |

Every story is original fiction, written fresh by Gemini from a one-line premise in the sheet —
nothing is copied from real Reddit threads or any other source. Stories are restrained rather
than graphic (no gore, no explicit violence, no real people), so the channel stays
monetization-safe.

## How it works

1. **Google Sheet** (`Content` tab) holds one row per video: a topic, a status, and — once
   generated — the full script and scene-by-scene shot list as JSON.
2. **`generate_story.py`** picks the next `IDEA` row, calls Gemini, and writes back a full
   story broken into scenes and 4 shots per scene (narration, subtitle, image prompt, emotion,
   camera motion). Row status becomes `GENERATED`.
3. **`generate_video.py`** picks the next `GENERATED` row, narrates every shot with edge-tts
   (emotion-calibrated rate/pitch/pauses via SSML), generates a matching dark cinematic image
   for every shot (AI first, stock video/photo as a backup), composites subtitles and branding,
   renders the final vertical video, and mixes in a quiet generated ambient sound bed. Row status
   becomes `VIDEO_CREATED`.
4. **`upload_youtube.py`** uploads the rendered file as a **private** YouTube video and writes
   back the video URL. Row status becomes `UPLOADED`. Videos always upload private — review and
   publish manually from YouTube Studio.

Everything runs through **GitHub Actions** (`.github/workflows/`), triggered manually via
`workflow_dispatch`. You can add a `schedule:` cron trigger once you're happy with output quality.

## The ambient sound bed

`ENABLE_AMBIENT_BED` in `config.py` turns on a quiet rain/drone bed that's mixed under every
narration track. It's generated entirely with ffmpeg's built-in audio sources (`anoisesrc` +
`aevalsrc`) — nothing is downloaded or sourced from a third party, so there is no copyright risk.
If it ever fails for any reason it's skipped silently; it never breaks a render.

## Setup

See **SETUP_GUIDE.md** for the full step-by-step walkthrough (new Google Sheet, new YouTube
OAuth client, GitHub Secrets, run order).

## Repo layout

```
config.py                  Channel settings: voice, visual style, video types, ambient bed
nd_common.py                Shared Google Sheets + retry helpers
generate_story.py          Gemini story generation
generate_video.py          TTS + visuals + subtitles + ambient bed + render
upload_youtube.py          YouTube upload
setup_sheet_schema.py      One-time sheet bootstrap
seed_content_ideas.py      Loads content_ideas_by_type.csv into the sheet
get_youtube_refresh_token.py  Local one-time OAuth helper
content_ideas_by_type.csv  45 starter story premises (15 per video_type)
.github/workflows/         The 5 GitHub Actions workflows
```
