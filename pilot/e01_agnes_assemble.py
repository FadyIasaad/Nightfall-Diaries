"""CPU-only Kokoro voice preparation and authentic Agnes-shot film assembly.

Never replaces missing animated footage with still images. Technical quality is
separate from emotional voice acting, true lip-sync, visual review and release.
"""
import argparse
import json
from pathlib import Path
import subprocess

from pilot import e01_agnes_production as run
from pilot import e01_full_run as original
from studio.continuity import sha256
from studio.quality_gate import check_media

VOICE_MANIFEST = run.OUT / "voice_manifest.json"
FILM = run.OUT / "E01_The_Night_the_Forest_Burned_216s_UNAPPROVED.mp4"
PREVIEW = run.OUT / "picture_only.mp4"


def cmd(*args, timeout=3600):
    subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "error", "-y",
                    *map(str, args)], capture_output=True, check=True, timeout=timeout)


def duration(path):
    response = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nokey=1:noprint_wrappers=1", str(path)],
        text=True, capture_output=True, check=True, timeout=30
    )
    return float(response.stdout.strip())


def voices():
    plan = run.prepare()
    _, old = original.scene_plan()
    from studio.continuity import locked_cast
    from studio.neural_audio import render_kokoro
    cast = locked_cast(original.SERIES)
    records = []
    previous = None
    if VOICE_MANIFEST.is_file():
        previous = json.loads(VOICE_MANIFEST.read_text(encoding="utf-8"))
    trusted = {}
    if previous and previous.get("plan_sha256") == plan["plan_sha256"]:
        trusted = {v["scene"]: v for v in previous.get("records", [])}
    for scene in old["scenes"]:
        no = scene["scene_no"]
        ref = cast[scene["speaker"]]
        out = run.OUT / f"voice_{no:02d}.wav"
        known = trusted.get(no, {})
        if (not out.is_file() or known.get("sha256") != sha256(out)
                or known.get("voice_id") != scene["voice_id"]):
            render_kokoro(scene["script_text"], ref, out)
        length = duration(out)
        if not 0.5 <= length <= 40:
            raise RuntimeError("INVALID_KOKORO_VOICE_WAV")
        scene_window = sum(s["duration_seconds"] for s in plan["shots"]
                           if s["scene"] == no)
        if length > scene_window + 0.2:
            raise RuntimeError(f"SCENE_{no:02d}_VOICE_LONGER_THAN_REAL_MOTION_WINDOW")
        records.append({
            "scene": no, "speaker": scene["speaker"],
            "voice_id": scene["voice_id"], "file": out.name,
            "sha256": sha256(out), "actual_seconds": round(length, 3),
            "scene_window_seconds": scene_window,
        })
    run.atomic_json(VOICE_MANIFEST, {
        "episode": run.script.EPISODE, "plan_sha256": plan["plan_sha256"],
        "real_kokoro_voice_count": len(records),
        "records": records, "lip_sync_verified": False,
        "public_publish": False,
    })
    print("NIGHTFALL_KOKORO_REAL_VOICES", len(records))
    return records


def assemble():
    plan = run.prepare()
    state = run.load(plan)
    if len(state["completed"]) != 18 or state["pending"] is not None:
        raise RuntimeError("CANNOT_ASSEMBLE_WITHOUT_18_SHA_VERIFIED_REAL_AGNES_CLIPS")
    voice_map = {v["scene"]: v for v in voices()}
    if set(voice_map) != set(range(1, 15)):
        raise RuntimeError("NOT_ALL_ORIGINAL_SCENES_HAVE_NEURAL_VOICES")
    stage = []
    elapsed = 0.
    scene_starts = {}
    scene_windows = {}
    for shot in plan["shots"]:
        idx = shot["index"]
        src = run.OUT / f"shot_{idx:03d}.mp4"
        dest = run.OUT / f"normalized_{idx:03d}.mp4"
        if not dest.is_file():
            cmd("-i", src, "-vf",
                "scale=720:1280:force_original_aspect_ratio=increase,"
                "crop=720:1280,fps=24,format=yuv420p",
                "-an", "-c:v", "libx264", "-preset", "veryfast",
                "-crf", "22", "-movflags", "+faststart", dest)
        seconds = duration(dest)
        if not 3.5 <= seconds <= 14:
            raise RuntimeError("NORMALIZED_VIDEO_NOT_REAL_LENGTH")
        no = shot["scene"]
        scene_starts.setdefault(no, elapsed)
        scene_windows[no] = scene_windows.get(no, 0) + seconds
        elapsed += seconds
        stage.append(dest)
    playlist = run.OUT / "e01_video_concat.txt"
    # Paths are repo-controlled, no arbitrary shell or input filenames.
    playlist.write_text("".join("file '" + str(p.resolve()) + "'\n" for p in stage),
                        encoding="utf-8")
    cmd("-f", "concat", "-safe", "0", "-i", playlist,
        "-c", "copy", "-movflags", "+faststart", PREVIEW)
    movie_seconds = duration(PREVIEW)
    if not 180 <= movie_seconds <= 360:
        raise RuntimeError("CINEMATIC_EPISODE_NOT_3_TO_6_MINUTES")
    voice_paths = [run.OUT / voice_map[i]["file"] for i in range(1, 15)]
    for i, path in enumerate(voice_paths, 1):
        if sha256(path) != voice_map[i]["sha256"]:
            raise RuntimeError("LOCKED_KOKORO_WAV_SHA_CHANGED")
        if duration(path) > scene_windows[i] + 0.2:
            raise RuntimeError("NEURAL_VOICE_OVERLAPS_NEXT_SCRIPTED_SCENE")
    filters = []
    labels = []
    for i in range(1, 15):
        label = f"[voice{i}]"
        ms = int(1000 * scene_starts[i])
        filters.append(
            f"[{i}:a]aformat=sample_rates=24000:channel_layouts=mono,"
            f"adelay={ms}:all=1{label}")
        labels.append(label)
    filters.append("".join(labels) + "amix=inputs=14:duration=longest:"
                   "normalize=0,volume=0.90[mix]")
    args = ["-i", PREVIEW]
    for path in voice_paths:
        args.extend(["-i", path])
    cmd(*args, "-filter_complex", ";".join(filters),
        "-map", "0:v:0", "-map", "[mix]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
        "-t", f"{movie_seconds:.3f}", "-movflags", "+faststart", FILM)
    result = check_media(FILM, mode="cinematic_episode")
    state["full_mp4_verified"] = True
    state["voice_files_verified"] = True
    state["status"] = "TECHNICALLY_PLAYABLE_CINEMATIC_EPISODE_UNAPPROVED"
    state["film_sha256"] = sha256(FILM)
    state["film_seconds"] = result["duration_seconds"]
    state["character_lipsync_verified"] = False
    state["cinematic_acting_approved"] = False
    state["public_publish_attempted"] = False
    run.atomic_json(run.STATE, state)
    run.atomic_json(run.OUT / "technical_film_report.json", {
        **result, "shots": 18, "voices": 14,
        "actual_video_mp4": FILM.name, "sha256": state["film_sha256"],
        "voice_timing_checked": True,
        "true_lipsync_verified": False,
        "visual_cinematic_acting_approved": False,
        "automatic_publishing_blocked_until_real_qa": True,
    })
    print("AGNES_E01_REAL_VIDEO_AND_KOKORO_AUDIO_COMPOSED_UNAPPROVED", result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("voices", "assemble"))
    args = parser.parse_args()
    if args.mode == "voices":
        voices()
    else:
        assemble()


if __name__ == "__main__":
    main()
