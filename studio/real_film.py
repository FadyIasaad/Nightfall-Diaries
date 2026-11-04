"""Real-motion candidate renderer. Never fake a scene with still-image zooms.

The external free video Space is unverified and may reject this job. An MP4
candidate is NOT a visual/lip-sync approval; the publishing gate remains off.
"""
import argparse
import json
import math
import os
import shutil
import subprocess
from pathlib import Path

from .restore import ROOT, validate_stories
from .screenplay import load_screenplay

OUT = ROOT / "output"
ROOT_IMAGE = ROOT / "seasons/S01_the_last_little_fox/characters/s01_ember/cloud_reference.png"
SERIES = ("S01_the_last_little_fox", "S02_the_boy_who_forgot_tomorrow")

def command(*args):
    subprocess.run(list(args), check=True, capture_output=True, text=True)

def media_info(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration:stream=codec_name,codec_type,width,height",
         "-of", "json", str(path)],
        capture_output=True, text=True, check=True
    )
    return json.loads(r.stdout)

def duration(path):
    return float(media_info(path)["format"]["duration"])

def validate_motion(path):
    info = media_info(path)
    video = next((s for s in info.get("streams", [])
                  if s.get("codec_type") == "video"), None)
    if not video or (video.get("width") or 0) < 320 or (video.get("height") or 0) < 320:
        raise RuntimeError("Missing usable AI motion video track")
    if duration(path) < 2:
        raise RuntimeError("Free provider returned an unusably short clip")
    return True

def normalize(path, dest):
    # Crops actual generated moving footage, never substitutes a still photo.
    command("ffmpeg", "-y", "-i", str(path),
            "-vf", "scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,fps=24",
            "-an", "-c:v", "libx264", "-crf", "22", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", str(dest))
    validate_motion(dest)
    return dest

def character_image(season, character_id):
    if character_id.endswith("_narrator"):
        raise RuntimeError("Narration must use a storyboard-visible character, never a narrator portrait")
    path = ROOT / "seasons" / season / "characters" / character_id / "cloud_reference.png"
    if not path.is_file():
        raise RuntimeError(f"Missing locked visual reference for {character_id}; no generic-substitute imagery allowed")
    return path

def visual_lead(scene, cast):
    """Choose on-screen identity independently of the speaking neural voice.

    Never use a narrator portrait or a generic substitute. Explicit original
    scene visibility must designate an existing drawable locked character.
    """
    speaker = scene.get("character_id")
    if speaker not in cast:
        raise ValueError("Unapproved scene speaker: " + str(speaker))
    visible = scene.get("visible")
    if not isinstance(visible, list) or not visible:
        raise ValueError("Scene has no explicit visible character; create a reviewed storyboard first")
    for identity in visible:
        if identity not in cast:
            raise ValueError("Unapproved visible character: " + str(identity))
        if not isinstance(cast[identity].get("visual"), str) or not cast[identity]["visual"].strip():
            raise ValueError("Scene visible cast has no drawable identity: " + str(identity))
    # For dialogue, use the speaking character's reference when they are
    # visible. Narrator is never on-screen; choose the first directed actor.
    return speaker if speaker in visible else visible[0]


def motion_prompt(scene, cast, image_char):
    """Build only from the source-locked visible cast, not the narrator's null visual."""
    speaker = scene["character_id"]
    if image_char not in scene["visible"] or not cast[image_char].get("visual"):
        raise ValueError("Image character is not an approved on-screen actor")
    lead = cast[image_char]
    markers = "; ".join(lead.get("never_change") or [])
    secondary = [
        f"{cast[identity]['name']}: {cast[identity]['visual']}"
        for identity in scene["visible"] if identity != image_char
    ]
    speech = ("Narration is voice-over only; do not show or animate a narrator. "
              if speaker.endswith("_narrator") else
              ("On-screen dialogue spoken by " if speaker == image_char else
               "Off-screen dialogue by ") + speaker + ". ")
    return (
        "Polished stylized 3D animated feature-film acting, real body locomotion and facial expression. "
        + lead["visual"]
        + " Preserve exact identity and costume every frame. Locked details: " + markers + ". "
        + ("Other on-screen characters (same locked canonical identities): " + " | ".join(secondary) + ". "
           if secondary else "")
        + (scene.get("direction") or "Meaningful acting, paw gestures, eye movement, environmental motion and camera changes.")
        + " Real animation only: no static image pan, slideshow, generic substitute, or primitive shapes. "
        + speech
        + "Dialogue/narration text for audio timing: " + scene["text"]
    )


def proof_scenes(script, episode_id):
    proof = json.loads((ROOT / "studio/proofs/ember_E01_proof_plan.json").read_text())
    if proof.get("episode_id") != episode_id or len(proof.get("shots", [])) != 3:
        raise RuntimeError("Approved original three-shot proof plan missing")
    scenes = []
    for shot in proof["shots"]:
        original = script["scenes"][shot["script_scene_index"]]
        if shot["character_id"] != original["character_id"] or shot["dialogue_excerpt"] not in original["text"]:
            raise RuntimeError("Proof shot diverged from original storyline")
        scenes.append({"character_id": original["character_id"],
                       "text": shot["dialogue_excerpt"],
                       "seconds": float(shot["seconds"]),
                       "visible": shot["visible"], "direction": shot["direction"]})
    return scenes

def generate(episode_id, mode="proof"):
    validate_stories()
    if mode not in ("proof", "full") or "_E" not in episode_id:
        raise ValueError("Explicit approved episode and valid rendering mode required")
    season_id, n = episode_id.rsplit("_E", 1)
    if season_id not in SERIES or not n.isdigit() or not 1 <= int(n) <= (12 if season_id == SERIES[0] else 10):
        raise ValueError("Unknown original episode ID")
    if mode == "proof" and episode_id != "S01_the_last_little_fox_E01":
        raise ValueError("First quality proof belongs to the original Fox E01")
    season = ROOT / "seasons" / season_id
    original = json.loads((season / "scripts" / ("E" + n + ".json")).read_text())
    script = load_screenplay(episode_id)
    from .continuity import locked_cast
    cast = locked_cast(season_id)
    if mode == "full":
        words = sum(len(scene["text"].split()) for scene in script["scenes"])
        if not 240 <= words <= 430:
            raise RuntimeError(f"SCREENPLAY_WORD_COUNT: {words} words; 240–430 required for a ≤180-second target")
        sources = script["scenes"]
    else:
        sources = proof_scenes(original, episode_id)
    OUT.mkdir(exist_ok=True, parents=True)

    # Optional heavy dependencies must not be imported by check_setup/schedule standby.
    from .free_video import generate_video
    from .neural_audio import render_kokoro

    from .checkpoints import fingerprint,restore_clip,save_clip
    from .continuity import sha256
    from .motion_provider import settings as provider_settings
    # Validate ALL storyboards before loading heavyweight TTS or using GPU quota.
    # Narration remains the locked narrator voice; its pictures come from scene.visible.
    visible_leads = [visual_lead(scene, cast) for scene in sources]
    prompts = [motion_prompt(scene, cast, lead)
               for scene, lead in zip(sources, visible_leads)]
    finished = []
    for idx, (scene, image_char, prompt) in enumerate(zip(sources, visible_leads, prompts), 1):
        char = cast[scene["character_id"]]
        speaker = scene["character_id"]
        image_file = character_image(season_id, image_char)
        audio = render_kokoro(scene["text"], char, OUT / f"{episode_id}_line_{idx:02d}.wav")
        voice_seconds = duration(audio)
        if not 0.4 < voice_seconds < 150:
            raise RuntimeError("Invalid neural-voice sample duration")
        clip_count = 1 if mode == "proof" else math.ceil(voice_seconds / 5)
        clips = []
        for ci in range(clip_count):
            source = OUT / f"{episode_id}_ai_{idx:02d}_{ci:02d}.mp4"
            norm = OUT / f"{episode_id}_norm_{idx:02d}_{ci:02d}.mp4"
            clip_seconds = float(scene.get("seconds", 5.0))
            cache_key = fingerprint({
                "version": 2, "episode": episode_id, "mode": mode, "scene": idx, "part": ci,
                "speaker": speaker, "line": scene["text"], "voice": char["voice"],
                "image_character": image_char, "image_sha256": sha256(image_file),
                "prompt": prompt, "provider": provider_settings(), "seconds": clip_seconds
            })
            if restore_clip(episode_id, mode, idx, ci, cache_key, norm):
                validate_motion(norm)
                print(f"REUSED_VERIFIED_CLIP: scene={idx} part={ci}", flush=True)
            else:
                generate_video(image_file, prompt, source, seconds=clip_seconds)
                validate_motion(source)
                normalize(source, norm)
                save_clip(episode_id, mode, idx, ci, cache_key, norm)
                print(f"CHECKPOINT_SAVED: scene={idx} part={ci}", flush=True)
            clips.append(norm)

        listing = OUT / f"{episode_id}_clips_{idx:02d}.txt"
        listing.write_text("".join("file '" + str(p.resolve()) + "'\n" for p in clips))
        silent = OUT / f"{episode_id}_silent_{idx:02d}.mp4"
        command("ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i",
                str(listing), "-c", "copy", str(silent))
        video_seconds = duration(silent)
        if video_seconds < voice_seconds - 0.05:
            raise RuntimeError("Generated character motion shorter than spoken line; no static fill or cut-off audio")
        completed = OUT / f"{episode_id}_scene_{idx:02d}.mp4"
        # Audio pad leaves time for actual on-screen reactions after a short line.
        command("ffmpeg", "-y", "-i", str(silent), "-i", str(audio),
                "-map", "0:v:0", "-map", "1:a:0",
                "-af", "apad", "-t", str(video_seconds if mode == "proof" else voice_seconds),
                "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
                "-movflags", "+faststart", str(completed))
        finished.append(completed)
    final = OUT / f"{episode_id}_{mode}.mp4"
    listing = OUT / f"{episode_id}_all_scenes.txt"
    listing.write_text("".join("file '" + str(p.resolve()) + "'\n" for p in finished))
    command("ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i",
            str(listing), "-c", "copy", "-movflags", "+faststart", str(final))

    from .quality_gate import check_media
    check_media(final, mode=mode)
    return final

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--episode", default="S01_the_last_little_fox_E01")
    p.add_argument("--mode", choices=("proof", "full"), default="proof")
    opts = p.parse_args()
    try:
        print("MOTION_CANDIDATE:", generate(opts.episode, opts.mode))
        print("CINEMATIC_APPROVAL_PENDING: video pixels alone cannot verify acting or lip sync.")
    except Exception as exc:
        raise SystemExit(f"REAL_RENDER_FAILED: {type(exc).__name__}: {exc}")

if __name__ == "__main__":
    main()
