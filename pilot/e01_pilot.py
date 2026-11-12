"""First episode E01 integration audit + optional single free motion clip.

This is NOT a full episode renderer. It proves integration before consuming a
single *public ZeroGPU* clip and fails closed on quota/provider failure.
There is no billing, retry, scheduler or publication integration.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess

from studio.restore import ROOT, validate_stories
from studio.screenplay import load_screenplay
from studio.continuity import locked_cast, sha256
from studio.real_film import visual_lead, motion_prompt, character_image, proof_scenes
from studio.auto_prepare import prepare as prepare_original_pack
from studio.motion_provider import probe as motion_probe

EPISODE_ID = "S01_the_last_little_fox_E01"
SEASON = "S01_the_last_little_fox"
DEFAULT_DIR = ROOT / "output/e01_pilot"
APPROVED_HEAD = "pilot/e01-first-clip-one-shot-20261112"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def audit(output_dir):
    """Verify source-locked E01 assets, scenes, voices and film safety offline."""
    if validate_stories() != 22:
        raise RuntimeError("22 original episodes must remain intact")
    expanded = load_screenplay(EPISODE_ID)
    if expanded["episode_id"] != EPISODE_ID:
        raise ValueError("Wrong first-episode screenplay")
    cast = locked_cast(SEASON)
    scenes = expanded["scenes"]
    words = sum(len(s["text"].split()) for s in scenes)
    if not 240 <= words <= 430 or len(scenes) < 12:
        raise ValueError("First episode is not a complete expanded screenplay")

    production = read(ROOT / "studio/production_settings.json")
    config = read(ROOT / "config.json")
    if production.get("production_enabled") or config.get("public_publish_enabled"):
        raise RuntimeError("Unexpected enabled production or public publishing")
    scene_jobs = []
    for i, scene in enumerate(scenes, 1):
        on_screen = visual_lead(scene, cast)
        image_path = character_image(SEASON, on_screen)
        prompt = motion_prompt(scene, cast, on_screen)
        if not image_path.is_file() or not prompt or len(prompt) < 100:
            raise RuntimeError("Missing real actor reference or direction")
        speaker = cast[scene["character_id"]]
        scene_jobs.append({
            "shot_number": i,
            "speaker_id": speaker["id"],
            "on_screen_reference_id": on_screen,
            "image_ref_sha256": sha256(image_path),
            "voice_engine": speaker["voice"]["engine"],
            "locked_voice_id": speaker["voice"]["voice_id"],
            "spoken_words": len(scene["text"].split()),
            "direction": scene.get("direction"),
            "prompt": prompt,
            "status": "PLANNED_NOT_RENDERED",
        })

    pack = prepare_original_pack(EPISODE_ID)
    proof = proof_scenes(read(ROOT / "seasons" / SEASON / "scripts/E01.json"), EPISODE_ID)
    report = {
        "episode_id": EPISODE_ID,
        "status": "E01_SCRIPT_AND_LOCKS_VALID_MOTION_UNPROVEN",
        "original_episode_count_verified": 22,
        "expanded_scene_count": len(scenes),
        "expanded_spoken_words": words,
        "locked_cast_count": len(cast),
        "locked_voice_engine": "kokoro",
        "proof_shot_count": len(proof),
        "original_image_references_verified": True,
        "full_episode_render_attempted": False,
        "full_episode_mp4_generated": False,
        "first_motion_clip_attempted": False,
        "voice_audio_generated": False,
        "lip_sync_verified": False,
        "public_publishing_attempted": False,
        "paid_api_calls": False,
        "production_enabled": False,
        "video_engine_approved": bool(production.get("renderer_verified")),
        "cinematic_video_approved": bool(production.get("cinematic_video_approved")),
        "release_gate": "BLOCKED_UNTIL_REAL_CINEMATIC_MP4_AND_LIP_SYNC",
        "blockers": [
            "No owner-approved cinematic image-to-video engine with verified repeatable free GPU quota",
            "Kaggle CUDA GPU was not allocated in the previous real owner test",
            "Kokoro emotional performance and true mouth-to-voice synchronization unverified",
            "No measured, approved 90-180s multi-scene episode MP4",
            "Publishing intentionally off",
        ],
    }
    output_dir = Path(output_dir)
    write(output_dir / "e01_integration_report.json", report)
    write(output_dir / "e01_all_14_scenes.json", {
        "episode_id": EPISODE_ID, "scene_jobs": scene_jobs,
        "status": "PLAN_ONLY_NO_AUDIO_OR_VIDEO",
    })
    write(output_dir / "e01_original_cast_and_3shot_pack.json", pack)
    return report, proof, cast


def one_shot(output_dir, report, proof, cast):
    """One no-payment 5s E01 motion trial, never a full 90-180s episode."""
    output_dir = Path(output_dir)
    report["single_test_provider"] = "Hugging Face public ZeroGPU Wan2.2 Space"
    report["single_test_mode"] = "ONE_ATTEMPT_5_SECONDS_NO_RETRY"
    report["single_test_clip_mp4"] = None

    # Restrict GPU inference to this explicit one-off pilot PR.
    if (os.getenv("GITHUB_EVENT_NAME") != "pull_request"
            or os.getenv("GITHUB_HEAD_REF") != APPROVED_HEAD
            or os.getenv("NIGHTFALL_E01_ONE_SHOT") != "YES_ONCE"):
        report["single_test_status"] = "BLOCKED_WRONG_CI_CONTEXT"
        return 2
    try:
        provider = motion_probe()  # GET only, no GPU or payment
        report["public_space_preflight"] = provider.get("state")
        if provider.get("state") != "READY_FOR_ONE_QUOTA_LIMITED_TEST":
            report["single_test_status"] = "BLOCKED_PUBLIC_FREE_PROVIDER"
            report["provider_note"] = str(provider.get("notes", ""))[:250]
            return 2
        from studio.free_video import generate_video
        source = proof[0]
        first_lead = visual_lead(source, cast)
        image_path = character_image(SEASON, first_lead)
        report["first_motion_clip_attempted"] = True
        raw = output_dir / "e01_first_shot_unapproved.mp4"
        generate_video(image_path, motion_prompt(source, cast, first_lead),
                       raw, seconds=5.0)
        if not raw.is_file() or raw.stat().st_size < 10000:
            raise RuntimeError("Provider did not return nonempty moving video")
        report["single_test_status"] = "VIDEO_CANDIDATE_UNAPPROVED"
        report["single_test_clip_mp4"] = raw.name
        try:
            info = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries",
                 "format=duration:stream=codec_type,width,height",
                 "-of", "json", str(raw)],
                capture_output=True, text=True, check=True, timeout=20
            )
            report["single_test_ffprobe"] = json.loads(info.stdout)
        except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired,
                ValueError) as exc:
            report["ffprobe_error"] = type(exc).__name__
        return 0
    except Exception as exc:
        detail = str(exc)[:320]
        for name in ("HF_TOKEN", "AGNES_API_KEY", "KAGGLE_API_TOKEN"):
            secret = os.getenv(name) or ""
            if secret:
                detail = detail.replace(secret, "[REDACTED]")
        report["single_test_status"] = "BLOCKED_BY_FREE_PROVIDER_OR_QUOTA"
        report["single_test_error_type"] = type(exc).__name__
        report["single_test_error"] = detail
        return 2
    finally:
        # No release approval is ever granted by a successful 5-second clip.
        report["full_episode_mp4_generated"] = False
        report["public_publishing_attempted"] = False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("audit", "one-shot"), default="audit")
    parser.add_argument("--output-dir", default=str(DEFAULT_DIR))
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    report, proof, cast = audit(output_dir)
    if args.mode == "one-shot":
        exit_code = one_shot(output_dir, report, proof, cast)
        write(output_dir / "e01_integration_report.json", report)
    else:
        exit_code = 0
    print("E01_PILOT:", report["status"])
    print("FULL_EPISODE_MP4_GENERATED:", report["full_episode_mp4_generated"])
    print("FIRST_CLIP:", report.get("single_test_status", "NOT_ATTEMPTED"))
    print("SOCIAL_PUBLICATION: NEVER")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
