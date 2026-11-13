"""Actual full E01 attempt: 14 distinct AI motion scenes plus locked Kokoro voices.

No slideshow, no looped/repeated proof clip, no paid API, no publication.
Fail closed if public ZeroGPU quota, identity, voice, video or timing fails.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from studio.restore import ROOT, validate_stories
from studio.screenplay import load_screenplay
from studio.continuity import locked_cast, sha256
from studio.real_film import motion_prompt, visual_lead, character_image
from studio.quality_gate import check_media

EPISODE = "S01_the_last_little_fox_E01"
SERIES = "S01_the_last_little_fox"
PR_BRANCH = "pilot/e01-cinematic-source-first-real-render-20261113"
TRIGGER_MARKER = "[nightfall-E01-150s-run-once]"
CINEMATIC_IMAGE = ROOT / "assets/cinematic_refs/ember_approved_candidate_2026-11-13.webp"
SOURCE_SHA = "c6cfda4f199c13d5fdf6d4e5057026d718787a495aefc29125c06779eb662432"
SPACE = "Lightricks/LTX-2.5"
API = "/run"
OUT = ROOT / "output/e01_full_real_attempt"
REPORT = OUT / "full_e01_evidence.json"
TARGET_SECONDS = 150
TOTAL_SCENES = 14
MAX_GENERATIONS = 14

def save(report):
    OUT.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def allocate_scene_seconds(scenes, target=TARGET_SECONDS):
    """Allocate exactly 150 seconds to 14 DIFFERENT scripted scenes, never loops."""
    if len(scenes) != TOTAL_SCENES or target < TOTAL_SCENES * 7:
        raise ValueError("Expected 14 unique scenes and enough time to act")
    weight = [max(1, len(s["text"].split())) for s in scenes]
    extra = target - TOTAL_SCENES * 7
    shares = [extra * n / sum(weight) for n in weight]
    durations = [7 + int(n) for n in shares]
    fractional = sorted(range(len(shares)), key=lambda k: shares[k] - int(shares[k]), reverse=True)
    for i in fractional[:target - sum(durations)]:
        durations[i] += 1
    if sum(durations) != target or min(durations) < 7 or max(durations) > 15:
        raise ValueError("Full episode shot allocation out of range")
    return durations

def scene_plan():
    if validate_stories() != 22:
        raise RuntimeError("Story archive checksum/episode count failure")
    if not CINEMATIC_IMAGE.is_file() or sha256(CINEMATIC_IMAGE) != SOURCE_SHA:
        raise RuntimeError("New CGI Ember reference missing or SHA-256 changed")
    cast = locked_cast(SERIES)
    script = load_screenplay(EPISODE)
    scenes = script["scenes"]
    if script["episode_id"] != EPISODE or len(scenes) != TOTAL_SCENES:
        raise RuntimeError("E01 storyboard must contain the original 14 scenes")
    if sum(len(s["text"].split()) for s in scenes) < 240:
        raise RuntimeError("E01 expanded script is incomplete")
    settings = json.loads((ROOT / "studio/production_settings.json").read_text())
    cfg = json.loads((ROOT / "config.json").read_text())
    if settings.get("production_enabled") or settings.get("publishing_implemented") or cfg.get("public_publish_enabled"):
        raise RuntimeError("Unexpected public-publishing flag. Stop.")
    budgets = allocate_scene_seconds(scenes)
    planned = []
    for i, (s, budget) in enumerate(zip(scenes, budgets), 1):
        lead = visual_lead(s, cast)
        path = (CINEMATIC_IMAGE if lead == "s01_ember" else character_image(SERIES, lead))
        prompt = motion_prompt(s, cast, lead)
        planned.append({
            "scene_no": i, "speaker": s["character_id"], "visible": s["visible"],
            "visual_lead": lead, "reference_file": str(path.relative_to(ROOT)),
            "reference_sha256": sha256(path), "script_text": s["text"],
            "direction": s["direction"], "ai_motion_prompt": prompt,
            "target_seconds": budget, "status": "NOT_GENERATED",
            "voice_engine": cast[s["character_id"]]["voice"]["engine"],
            "voice_id": cast[s["character_id"]]["voice"]["voice_id"],
            "cinematic_source": lead == "s01_ember",
        })
    report = {
        "episode": EPISODE, "status": "PLAN_VALID_RENDER_NOT_PROVEN",
        "original_episodes_verified": 22, "source_scene_count": TOTAL_SCENES,
        "distinct_scenes_generated": 0, "video_seconds_generated": 0,
        "target_seconds": TARGET_SECONDS, "min_final_seconds": 120,
        "max_final_seconds": 180, "requested_distinct_ai_shots": TOTAL_SCENES,
        "requested_seconds_sum": sum(budgets),
        "real_kokoro_audio_files": 0, "voices_verified": False,
        "true_lip_sync_verified": False, "film_created": False,
        "publication_attempted": False, "paid_api_calls": False,
        "account_publication_authorization_checked": False,
        "technical_acceptance_passed": False, "human_visual_qa_passed": False,
        "unverified_visual_sources": [
            s["visual_lead"] for s in planned if not s["cinematic_source"]
        ],
        "scenes": planned, "output_mp4": None,
    }
    return cast, report

def ffprobe(path):
    p = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration:stream=codec_type,codec_name,width,height",
         "-of", "json", str(path)],
        check=True, capture_output=True, text=True, timeout=30
    )
    return json.loads(p.stdout)

def duration(path):
    return float(ffprobe(path).get("format", {}).get("duration") or 0)

def safe_ffmpeg(*args):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *map(str, args)],
                   capture_output=True, check=True, timeout=240)

def authorized_run():
    """Only a single controlled PR synchronization event, not any PR rerun."""
    if os.getenv("GITHUB_EVENT_NAME") != "pull_request":
        return False
    if os.getenv("GITHUB_HEAD_REF") != PR_BRANCH:
        return False
    if os.getenv("GITHUB_RUN_ATTEMPT") != "1":
        return False
    if os.getenv("NIGHTFALL_E01_FULL_REAL") != "YES":
        return False
    if os.getenv("HF_TOKEN"):
        return False
    try:
        ev = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
        if ev.get("action") != "synchronize":
            return False
        # pull_request checks out a synthetic MERGE COMMIT, not the PR head.
        # Compare the actual PR head commit's subject, never HEAD's subject.
        pr = ev.get("pull_request") or {}
        head = (pr.get("head") or {}).get("sha", "")
        source_repo = ((pr.get("head") or {}).get("repo") or {}).get("full_name")
        if source_repo != "FadyIasaad/Nightfall-Diaries":
            return False
        if not isinstance(head, str) or len(head) != 40 or any(c not in "0123456789abcdef" for c in head):
            return False
        # SHA fetched in the workflow preflight; FETCH_HEAD is detached and safe.
        result = subprocess.run(
            ["git", "show", "-s", "--format=%s", head],
            check=True, capture_output=True, text=True, timeout=15
        )
        return result.stdout.strip() == TRIGGER_MARKER
    except (OSError, KeyError, ValueError, subprocess.SubprocessError):
        return False

def generate_scene(client, scene):
    """An actual new independent I2V inference for each original scene."""
    from gradio_client import handle_file
    image = ROOT / scene["reference_file"]
    result = client.predict(
        scene["ai_motion_prompt"], handle_file(str(image)),
        1024, 576, float(scene["target_seconds"]), 41 + scene["scene_no"],
        "diffusion", False, False, False, api_name=API
    )
    if not isinstance(result, (list, tuple)) or not result:
        raise RuntimeError("ZeroGPU returned no generated scene media")
    value = result[0]
    if isinstance(value, dict):
        value = value.get("video") or value.get("path") or value.get("name")
    if not isinstance(value, str):
        raise RuntimeError("ZeroGPU output did not contain a video path")
    source = Path(value)
    if not source.is_file() or source.suffix.lower() != ".mp4":
        raise RuntimeError("No real MP4 returned from free generation")
    dest = OUT / f"scene_{scene['scene_no']:02d}_generated.mp4"
    shutil.copyfile(source, dest)
    meta = ffprobe(dest)
    v = next((s for s in meta.get("streams", []) if s.get("codec_type") == "video"), None)
    seconds = float(meta.get("format", {}).get("duration") or 0)
    if not v or seconds < scene["target_seconds"] - 1.0:
        raise RuntimeError("Generated unique shot shorter than requested; cannot fake by looping")
    return dest, seconds

def create_voice(scene, cast):
    """Kokoro voices are synthesized from original speaker/text, no robotic fallback."""
    from studio.neural_audio import render_kokoro
    destination = OUT / f"voice_{scene['scene_no']:02d}.wav"
    char = cast[scene["speaker"]]
    wav = render_kokoro(scene["script_text"], char, destination)
    seconds = duration(wav)
    if not 0.3 < seconds <= scene["target_seconds"] + 0.5:
        raise RuntimeError("Kokoro spoken audio exceeds scene's motion window")
    return wav, seconds

def join_scene(video, wav, number, seconds):
    finished = OUT / f"scene_{number:02d}_voiced.mp4"
    safe_ffmpeg("-i", video, "-i", wav,
                "-filter:v", "scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,fps=24,format=yuv420p",
                "-filter:a", "apad", "-map", "0:v:0", "-map", "1:a:0",
                "-t", f"{seconds:.3f}", "-c:v", "libx264", "-crf", "22",
                "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", finished)
    return finished

def render_all(cast, report, factory=None):
    if not authorized_run():
        report["status"] = "BLOCKED_UNAUTHORIZED_ONE_TIME_FULL_RUN"
        save(report)
        return 2
    OUT.mkdir(exist_ok=True, parents=True)
    report["status"] = "RENDER_STARTED_REAL_FREE_INFERENCE"
    save(report)
    try:
        from gradio_client import Client
        client = (factory or Client)(SPACE, token=None)
        params = (client.view_api(return_format="dict").get("named_endpoints", {})
                  .get(API, {}).get("parameters", []))
        if len(params) != 10:
            raise RuntimeError("Official free LTX-2.5 API changed; cannot submit paid fallback")
        report["status"] = "RENDERING_14_DISTINCT_AI_SCENES_AND_KOKORO"
        save(report)
        assembled = []
        for scene in report["scenes"]:
            # Critical: ONE real generation per scene, no fallbacks, no loops.
            wav, audio_seconds = create_voice(scene, cast)
            report["real_kokoro_audio_files"] += 1
            scene["voice_seconds"] = round(audio_seconds, 3)
            scene["status"] = "VOICE_READY_VIDEO_PENDING"
            save(report)
            raw, generated_seconds = generate_scene(client, scene)
            voiced = join_scene(raw, wav, scene["scene_no"], generated_seconds)
            scene["status"] = "ACTUAL_AI_MOTION_WITH_KOKORO_AUDIO"
            scene["generated_seconds"] = round(generated_seconds, 3)
            scene["mp4"] = voiced.name
            assembled.append(voiced)
            report["distinct_scenes_generated"] += 1
            report["video_seconds_generated"] += generated_seconds
            save(report)
        # Only original, distinct scene MP4s are used. No replay or hold frames.
        listing = OUT / "all_actual_scenes.txt"
        listing.write_text("".join("file '" + str(p.resolve()) + "'\n" for p in assembled))
        film = OUT / (EPISODE + "_full_unapproved.mp4")
        safe_ffmpeg("-f", "concat", "-safe", "0", "-i", listing,
                    "-c", "copy", "-movflags", "+faststart", film)
        result = check_media(film, mode="full")
        report["output_mp4"] = film.name
        report["full_duration_seconds"] = result["duration_seconds"]
        report["technical_acceptance_passed"] = True
        report["film_created"] = True
        report["status"] = "FULL_150S_TECHNICAL_MP4_UNAPPROVED"
        # Audio mixing != actual face visemes. This is still NOT release approval.
        report["voices_verified"] = report["real_kokoro_audio_files"] == TOTAL_SCENES
        return 0
    except Exception as exc:
        report["status"] = "BLOCKED_BEFORE_FULL_EPISODE_COMPLETION"
        report["failure_type"] = type(exc).__name__
        error = str(exc)
        for name in ("HF_TOKEN", "AGNES_API_KEY", "KAGGLE_API_TOKEN"):
            token = os.getenv(name) or ""
            if token:
                error = error.replace(token, "[REDACTED]")
        report["failure_message"] = error[:450]
        return 2
    finally:
        # Never set lip-sync or owner approval just from a generated waveform.
        report["true_lip_sync_verified"] = False
        report["human_visual_qa_passed"] = False
        report["publication_attempted"] = False
        save(report)

def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("--mode", choices=["plan", "render"], default="plan")
    args = cli.parse_args()
    cast, report = scene_plan()
    save(report)
    status = render_all(cast, report) if args.mode == "render" else 0
    print("E01_FULL_RESULT", report["status"])
    print("REAL_MOTION_SCENES", report["distinct_scenes_generated"], "/14")
    print("GENERATED_REAL_VIDEO_SECONDS", round(report["video_seconds_generated"], 2))
    print("RELEASE_GATE", "BLOCKED_NO_LIPSYNC_OR_HUMAN_QA")
    print("PAID_APIS_OR_PUBLICATION", False)
    return status

if __name__ == "__main__":
    raise SystemExit(main())
