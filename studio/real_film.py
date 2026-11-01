"""Actual AI-motion scene assembly, natural voices, and video validation.

No still-photo animation, no espeak, no invented output. A single shot proof
is the default because free shared-GPU quotas cannot finance 12 clips/day.
"""
import argparse
import json
import math
import os
import shutil
import subprocess
from pathlib import Path
from .restore import ROOT, validate_stories
from .production import next_episode
from .free_video import generate_video
from .neural_audio import render_kokoro

OUT = ROOT / "output"
ROOT_IMAGE = ROOT / "studio/assets/ember_approved.png"

def command(*args):
    subprocess.run(args, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def media_info(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_name,codec_type,width,height",
         "-of", "json", str(path)],
        capture_output=True, text=True, check=True
    )
    return json.loads(r.stdout)

def duration(path):
    return float(media_info(path)["format"]["duration"])

def validate_motion(path):
    info = media_info(path)
    video = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    if not video or (video.get("width") or 0) < 320 or (video.get("height") or 0) < 320:
        raise RuntimeError("Generated clip lacks sufficient real video frames")
    if duration(path) < 1.8:
        raise RuntimeError("Generated clip is too short")
    return True

def normalize(path, dest):
    # 9:16 without photo zoom. Crops actual model video frames only.
    command("ffmpeg", "-y", "-i", str(path),
            "-vf", "scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,fps=24",
            "-an", "-c:v", "libx264", "-crf", "22", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", str(dest))
    validate_motion(dest)
    return dest

def generate(episode_id="auto", mode="proof"):
    validate_stories()
    episode_id = next_episode() if episode_id == "auto" else episode_id
    if not episode_id or "_E" not in episode_id:
        raise ValueError("No authorized unpublished episode")
    series, number = episode_id.rsplit("_E", 1)
    if series not in ("S01_the_last_little_fox", "S02_the_boy_who_forgot_tomorrow"):
        raise ValueError("Unknown / unapproved new series")
    if mode == "proof" and episode_id != "S01_the_last_little_fox_E01":
        raise ValueError("The first cinematic proof is locked to the original Fox E01")
    season = ROOT / "seasons" / series
    script = json.loads((season / "scripts" / ("E" + number + ".json")).read_text())
    castdata = json.loads((season / "characters" / "character_registry.json").read_text())
    cast = {x["id"]: x for x in castdata["characters"]}
    if not ROOT_IMAGE.is_file():
        raise RuntimeError("Approved Ember reference missing from studio/assets/ember_approved.png; refusing old low-quality reference.")
    OUT.mkdir(parents=True, exist_ok=True)
    sources = script["scenes"][:1] if mode == "proof" else script["scenes"]
    finished = []
    for idx, scene in enumerate(sources, 1):
        char = cast[scene["character_id"]]
        text = scene["text"]
        if mode == "proof":
            text = text.split(". ")[0].rstrip(".") + "."
        sound = render_kokoro(text, char, OUT / f"line_{idx:02d}.wav")
        scene_length = duration(sound)
        if not (0.4 < scene_length < 150):
            raise RuntimeError("Suspicious voice duration. No generation attempted.")
        required_clips = 1 if mode == "proof" else math.ceil(scene_length / 5)
        clips = []
        for chunk in range(required_clips):
            motion_prompt = (
                "High-end cinematic animated film scene in a burning forest at night. "
                "Ember is a russet fox cub with amber eyes, cream muzzle, teal scarf and exactly ONE gold star; "
                "white tip of his LEFT ear. Character performs purposeful physical action and emotional facial acting, "
                "dynamic camera perspective, volumetric firelight, wind-driven ash, stable anatomy and scarf. "
                "Real motion of body and limbs, NOT photo zoom, NOT static slideshow. "
                "For first scene: Ember runs through smoke and ducks a falling burning branch. "
                f"Original spoken line: {text}"
            )
            source = OUT / f"ai_{idx:02d}_{chunk:02d}.mp4"
            generate_video(ROOT_IMAGE, motion_prompt, source)
            validate_motion(source)
            normalized = OUT / f"norm_{idx:02d}_{chunk:02d}.mp4"
            clips.append(normalize(source, normalized))
        listfile = OUT / f"concat_{idx:02d}.txt"
        listfile.write_text("".join("file '" + str(p.resolve()) + "'\n" for p in clips))
        silent = OUT / f"scene_{idx:02d}_video.mp4"
        command("ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listfile), "-c", "copy", str(silent))
        if mode == "full" and duration(silent) < scene_length - 0.1:
            raise RuntimeError("Free provider made insufficient motion footage for voice; refusing a static-frame fill.")
        combined = OUT / f"scene_{idx:02d}_complete.mp4"
        if mode == "proof":
            # First five-second animation is the visual quality test, even if the
            # chosen original narration line is longer. No silent-movie claim.
            command("ffmpeg", "-y", "-i", str(silent), "-i", str(sound),
                    "-map", "0:v:0", "-map", "1:a:0", "-af", "apad", "-shortest",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", str(combined))
        else:
            command("ffmpeg", "-y", "-i", str(silent), "-i", str(sound),
                    "-t", str(scene_length), "-map", "0:v:0", "-map", "1:a:0",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", str(combined))
        finished.append(combined)
    final = OUT / f"{episode_id}_{mode}.mp4"
    if len(finished) == 1:
        shutil.copyfile(finished[0], final)
    else:
        join = OUT / "all_scenes.txt"
        join.write_text("".join("file '" + str(p.resolve()) + "'\n" for p in finished))
        command("ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(join),
                "-c", "copy", "-movflags", "+faststart", str(final))
    validate_motion(final)
    if not any(s.get("codec_type") == "audio" for s in media_info(final)["streams"]):
        raise RuntimeError("Video is missing natural-voice audio")
    return final

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--episode", default="auto")
    p.add_argument("--mode", choices=("proof", "full"), default="proof")
    a = p.parse_args()
    try:
        video = generate(episode_id=a.episode, mode=a.mode)
        print("ACTUAL_MP4_GENERATED:", video)
    except Exception as e:
        raise SystemExit(f"REAL_RENDER_FAILED: {type(e).__name__}: {e}")

if __name__ == "__main__":
    main()
