"""Cloud-only zero-inference-cost Nightfall E01 illustrated film renderer.

Renders characters acting, mouth movement, eyes, legs and scenery on each frame
from original script and locked Kokoro WAVs. Not diffusion/image-to-video:
visually a 2D illustrated drama, NOT the requested 3D film look.
No API tokens, no GPUs, no card, no media scraping, no paid provider.

--mode sample: make one playable scene review MP4 first
--mode full:  14 original illustrated scenes + 14 real Kokoro voices = 216 sec
Public posting remains gated until actual film review and official platforms.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import subprocess
import wave

from pilot import e01_agnes_full_episode_plan as timeline
from pilot import e01_full_run as canon
from studio.cpu_motion_engine import FPS, W, H, render_frame
from studio.continuity import sha256
from studio.quality_gate import check_media

ROOT = canon.ROOT
VOICE_DIR = ROOT / "output/agnes_e01"
VOICE_MANIFEST = VOICE_DIR / "voice_manifest.json"
OUT = ROOT / "output/cpu_story_e01"
STATUS = OUT / "progress.json"
FILM = OUT / "Nightfall_S01_E01_original_2D_animated_UNAPPROVED.mp4"
REFERENCE_REV = "d235d66f5f17e19b2020623a5cba0ff78caf2321"
SCHEMA = "nightfall-2d-original-puppet-v1"


def run_cmd(args, timeout=1200):
    done = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    if done.returncode != 0:
        raise RuntimeError("FFMPEG_FAILURE: " + done.stderr[-900:])
    return done


def seconds(path):
    data = run_cmd(["ffprobe", "-v", "error", "-of", "json",
                    "-show_entries", "format=duration", str(path)])
    return float(json.loads(data.stdout)["format"]["duration"])


def load_inputs():
    # All 22 story files and approved Ember reference are verified by canon.
    _, old = canon.scene_plan()
    plan = timeline.make_plan(REFERENCE_REV)
    if plan["target_seconds"] != 216 or len(old["scenes"]) != 14:
        raise RuntimeError("STORYBOARD_OR_DURATION_LOCK_CHANGED")
    if not VOICE_MANIFEST.is_file():
        raise RuntimeError("LOCKED_14_KOKORO_VOICES_MISSING_RESTORE_GITHUB_ARTIFACT")
    doc = json.loads(VOICE_MANIFEST.read_text(encoding="utf-8"))
    if doc.get("plan_sha256") != plan["plan_sha256"]:
        raise RuntimeError("KOKORO_VOICE_PLAN_DIGEST_MISMATCH")
    records = doc.get("records", [])
    if len(records) != 14 or len({v.get("scene") for v in records}) != 14:
        raise RuntimeError("NOT_ALL_14_ORIGINAL_SCENE_VOICES_PRESENT")
    voices = {}
    for rec in records:
        n = rec["scene"]
        fn = f"voice_{n:02d}.wav"
        path = VOICE_DIR / fn
        if rec.get("file") != fn or not path.is_file() or sha256(path) != rec.get("sha256"):
            raise RuntimeError("VOICE_WAV_FILE_MISSING_OR_TAMPERED")
        if rec.get("voice_id") != old["scenes"][n - 1]["voice_id"]:
            raise RuntimeError("VOICE_CAST_LOCK_CHANGED")
        voices[n] = path
    budgets = {}
    for shot in plan["shots"]:
        n = shot["scene"]
        budgets[n] = budgets.get(n, 0) + shot["duration_seconds"]
    if set(budgets) != set(range(1, 15)) or sum(budgets.values()) != 216:
        raise RuntimeError("ORIGINAL_14_SCENES_DID_NOT_MATCH_216_SECONDS")
    return old, plan, voices, budgets


def audio_levels(wav_path, count):
    """Small energy-based mouth animation, not a phonetic lip-sync claim."""
    with wave.open(str(wav_path), "rb") as wf:
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2:
            raise RuntimeError("NEURAL_VOICE_NOT_MONO_PCM16")
        rate = wf.getframerate()
        samples = wf.readframes(wf.getnframes())
    import array
    array_samples = array.array("h")
    array_samples.frombytes(samples)
    if os.sys.byteorder != "little":
        array_samples.byteswap()
    step = rate / FPS
    result = []
    for frame in range(count):
        start = int(frame * step)
        end = min(len(array_samples), int((frame + 1) * step))
        if end <= start:
            result.append(0)
            continue
        # Average absolute wave energy from actual Kokoro voice waveform.
        rms = sum(abs(x) for x in array_samples[start:end]) / (end - start)
        result.append(min(1, max(0, (rms - 220) / 1800)))
    return result


def original_ambience(dest, seconds_total, scene):
    """Original generated wind, ember crackle and soft suspense chords; no music licence."""
    import random
    rng = random.Random(1000 + scene)
    rate = 24000
    n = int(seconds_total * rate)
    with wave.open(str(dest), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(rate)
        block = bytearray()
        for i in range(n):
            t = i / rate
            # Low-volume deterministic forest sound bed, dramatic but beneath speech.
            wind = (math.sin(t * 0.79 + scene) + .5 * math.sin(t * 1.92)) * 155
            drone = (math.sin(2 * math.pi * 55 * t) +
                     .35 * math.sin(2 * math.pi * 82.4 * t)) * 165
            crackle = rng.randrange(-1000, 1000) * (0.21 if scene < 12 else .08)
            value = int(max(-32767, min(32767, wind + drone + crackle)))
            block.extend(struct.pack("<h", value))
            if len(block) >= 48000:
                out.writeframesraw(block)
                block.clear()
        if block:
            out.writeframesraw(block)


def encode_frames(path, scene, duration, wav, meta):
    total = round(duration * FPS)
    if total <= 0 or abs(total / FPS - duration) > .01:
        raise RuntimeError("INVALID_SCENE_FRAME_DURATION")
    levels = audio_levels(wav, total)
    voice_seconds = seconds(wav)
    if voice_seconds > duration + .05:
        raise RuntimeError("ORIGINAL_SCRIPT_VOICE_LONGER_THAN_SCENE_WINDOW")
    cmd = [
        "ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s:v", f"{W}x{H}",
        "-r", str(FPS), "-i", "pipe:0",
        "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(path)
    ]
    errfile = path.with_suffix(".ffmpeg.log")
    with errfile.open("wb") as errs:
        with subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=errs) as proc:
            if proc.stdin is None:
                raise RuntimeError("FFMPEG_STDIN_MISSING")
            try:
                for i in range(total):
                    t = i / FPS
                    frame = render_frame(
                        scene, t, levels[i], voice_seconds,
                        meta["script_text"], meta["speaker"],
                        meta["visible"], meta["direction"])
                    if i == total // 3:
                        thumbnail = OUT / f"scene_{scene:02d}_frame.png"
                        frame.save(thumbnail)
                    proc.stdin.write(frame.tobytes())
            except (BrokenPipeError, OSError):
                proc.stdin.close()
                proc.wait()
                raise RuntimeError("FFMPEG_RAW_VIDEO_PIPE_BROKEN")
            proc.stdin.close()
            rc = proc.wait(timeout=1200)
        if rc:
            raise RuntimeError("FFMPEG_RENDER_FAILED: " +
                               errfile.read_text(encoding="utf-8", errors="replace")[-900:])
    errfile.unlink(missing_ok=True)
    if not path.is_file() or path.stat().st_size < 10_000:
        raise RuntimeError("ANIMATED_SCENE_VIDEO_NOT_CREATED")


def voiced_scene(raw, voice, scene, duration, dest):
    ambience = OUT / f"ambient_{scene:02d}.wav"
    if not ambience.is_file():
        original_ambience(ambience, duration, scene)
    run_cmd([
        "ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "error", "-y",
        "-i", str(raw), "-i", str(voice), "-i", str(ambience),
        "-filter_complex",
        "[1:a]apad,volume=1.0[v];[2:a]volume=0.38[amb];"
        "[v][amb]amix=inputs=2:duration=longest:normalize=0[out]",
        "-map", "0:v:0", "-map", "[out]", "-c:v", "copy", "-c:a", "aac",
        "-b:a", "160k", "-t", f"{duration:.3f}",
        "-movflags", "+faststart", str(dest)
    ])
    if abs(seconds(dest) - duration) > .22:
        raise RuntimeError("VOICE_AND_ANIMATION_SCENE_DURATION_MISMATCH")


def record(status):
    OUT.mkdir(parents=True, exist_ok=True)
    temp = STATUS.with_suffix(".tmp")
    temp.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    temp.replace(STATUS)


def draw(sample=True):
    old, plan, voices, budgets = load_inputs()
    OUT.mkdir(parents=True, exist_ok=True)
    core = {"schema": SCHEMA, "episode": plan["episode"],
            "story_plan": plan["plan_sha256"],
            "render_type": "2d_original_articulated_character_animation",
            "target_seconds": 216, "frame_rate": FPS,
            "original_reference_art_reused_as_video": False,
            "scene_voices": {str(n): sha256(v) for n, v in voices.items()}}
    digest = hashlib.sha256(json.dumps(core, sort_keys=True).encode()).hexdigest()
    if STATUS.is_file():
        state = json.loads(STATUS.read_text(encoding="utf-8"))
        if state.get("input_sha256") != digest:
            raise RuntimeError("LOCKED_ANIMATION_PLAN_CHANGED_REFUSE_CORRUPTED_RESUME")
    else:
        state = {
            **core, "input_sha256": digest, "complete_scenes": [],
            "status": "READY_TO_ANIMATE_ON_CPU", "public_posting_attempted": False,
            "viseme_lipsync_verified": False, "character_motion_approval": False,
            "genuine_ai_video_generated": False,
        }
        record(state)
    max_scene = 1 if sample else 14
    for index in range(1, max_scene + 1):
        duration = min(12, budgets[index]) if sample else budgets[index]
        scene = old["scenes"][index - 1]
        dest = OUT / (f"review_scene_{index:02d}.mp4"
                      if sample else f"scene_{index:02d}_animated.mp4")
        raw = OUT / f"scene_{index:02d}_raw_{'preview' if sample else 'full'}.mp4"
        if not sample:
            previous = next((x for x in state["complete_scenes"]
                             if x["scene"] == index), None)
            if previous:
                if (previous["file"] != dest.name or not dest.is_file() or
                        sha256(dest) != previous["sha256"]):
                    raise RuntimeError("SHA_VERIFIED_ANIMATION_CHECKPOINT_MISSING")
                continue
        if not raw.is_file():
            encode_frames(raw, index, duration, voices[index], scene)
        voiced_scene(raw, voices[index], index, duration, dest)
        if sample:
            state["sample_output"] = str(dest.relative_to(ROOT))
            state["status"] = "ANIMATED_SAMPLE_READY_FOR_HUMAN_QUALITY_REVIEW"
        else:
            state["complete_scenes"].append({
                "scene": index, "file": dest.name, "sha256": sha256(dest),
                "seconds": round(seconds(dest), 3),
                "voice_sha256": sha256(voices[index]),
            })
            state["status"] = "CPU_CHARACTER_ANIMATION_IN_PROGRESS"
        record(state)
        print("CPU_ANIMATED_SCENE", index, "/", max_scene, "seconds", duration, flush=True)
    if sample:
        print("CPU_ANIMATED_SAMPLE", json.dumps({
            "path": state["sample_output"], "size": dest.stat().st_size,
            "public_upload": False, "quality_approved": False}))
        return state
    if len(state["complete_scenes"]) != 14:
        raise RuntimeError("FULL_EPISODE_CANNOT_ASSEMBLE_BEFORE_14_ANIMATED_SCENES")
    playlist = OUT / "episodes_concat.txt"
    playlist.write_text("".join(
        "file '" + str((OUT / f"scene_{i:02d}_animated.mp4").resolve()) + "'\n"
        for i in range(1, 15)), encoding="utf-8")
    run_cmd([
        "ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "error", "-y",
        "-f", "concat", "-safe", "0", "-i", str(playlist),
        "-vf", "scale=720:1280:flags=lanczos",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
        "-movflags", "+faststart", str(FILM)
    ], timeout=2400)
    media = check_media(FILM, mode="cinematic_episode")
    state["status"] = "COMPLETE_ORIGINAL_2D_ANIMATED_FILM_UNAPPROVED"
    state["full_video"] = FILM.name
    state["full_video_sha256"] = sha256(FILM)
    state["verified_duration_seconds"] = media["duration_seconds"]
    state["public_posting_attempted"] = False
    record(state)
    print("CPU_FULL_ANIMATED_FILM", json.dumps({
        "seconds": media["duration_seconds"], "sha256": state["full_video_sha256"],
        "shots": 14, "audio_verified": True, "public_upload": False,
        "2d_puppets_not_cinematic_3d": True
    }))
    return state


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("sample", "full"), required=True)
    args = ap.parse_args()
    draw(sample=args.mode == "sample")


if __name__ == "__main__":
    main()
