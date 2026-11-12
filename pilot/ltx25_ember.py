"""One controlled, unpaid LTX-2.5 image-to-video experiment.

Uses the official Lightricks ZeroGPU demo with *no Hugging Face token*:
no paid inference endpoint, no billing key, no uploads to social accounts.
The existing archived characters/stories/voice locks remain immutable.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess

from studio.restore import ROOT, validate_stories
from studio.continuity import locked_cast, sha256
from studio.screenplay import load_screenplay

SPACE = "Lightricks/LTX-2.5"
ENDPOINT = "/run"
EPISODE = "S01_the_last_little_fox_E01"
SEASON = "S01_the_last_little_fox"
BRANCH = "pilot/ltx25-ember-cinematic-20261112"
IMAGE = ROOT / "seasons" / SEASON / "characters" / "s01_ember" / "cloud_reference.png"
OUTPUT = ROOT / "output/ltx25_ember_pilot"
# Two-stage image-to-video wants dimensions divisible by 64; 576x1024 is 9:16.
WIDTH, HEIGHT, DURATION, SEED = 576, 1024, 2.0, 41
DECODER = "diffusion"  # quality-oriented, potentially slower/limited by free quota

PROMPT = (
    "Original cinematic 3D animated family adventure, sumptuous film-quality "
    "groomed fur, stylized high-end feature-film lighting; FIRST FRAME follows "
    "the supplied approved image of Ember exactly. Ember is the same young "
    "russet fox cub, cream chest and muzzle, white tip on LEFT ear only, "
    "teal scarf with precisely ONE embroidered gold star, large expressive eyes. "
    "In the burning magical forest, Ember RUNS three natural, grounded paw "
    "steps through drifting ash, suddenly brakes and turns his head in alarm "
    "toward a falling glowing branch. Face and ears show credible fear. "
    "Physical tail and scarf movement, soft fur responding to air and light, "
    "deep atmospheric fire haze, cinematic moving tracking camera, consistent "
    "anatomy and identity in every frame. No cuts, no titles, no captions, "
    "no logos, no image zoom, no slide show, no talking or invented characters. "
    "Beautiful physically plausible motion, original 3D animated film aesthetic."
)


def save(report):
    OUTPUT.mkdir(parents=True, exist_ok=True)
    target = OUTPUT / "ltx25_report.json"
    target.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )


def audit():
    if validate_stories() != 22:
        raise ValueError("Original story archive integrity failed")
    cast = locked_cast(SEASON)
    loaded = load_screenplay(EPISODE)
    if len(loaded["scenes"]) < 12:
        raise ValueError("Original expanded screenplay E01 missing")
    expected = ROOT / "seasons" / SEASON / "characters/cloud_reference_locks.json"
    images = json.loads(expected.read_text(encoding="utf-8"))
    if not IMAGE.is_file() or sha256(IMAGE) != images["s01_ember"]:
        raise ValueError("Ember original image failed SHA-256 lock")
    settings = json.loads(
        (ROOT / "studio/production_settings.json").read_text(encoding="utf-8")
    )
    if settings.get("production_enabled") or settings.get("publishing_implemented"):
        raise ValueError("Production/publishing was unexpectedly activated")
    return {
        "episode_id": EPISODE,
        "status": "E01_LTX25_TRIAL_STAGED_NOT_APPROVED",
        "original_22_episodes_verified": True,
        "expanded_scene_count": len(loaded["scenes"]),
        "locked_cast_count": len(cast),
        "source_ember_sha256": sha256(IMAGE),
        "provider": SPACE, "api_name": ENDPOINT,
        "image_to_video": True,
        "width": WIDTH, "height": HEIGHT, "seconds": DURATION,
        "decoder": DECODER, "seed": SEED,
        "token_used": False,
        "paid_api_calls": False,
        "social_uploads": False,
        "full_episode_created": False,
        "cinematic_quality_approved": False,
        "accurate_kokoro_lipsync_proven": False,
        "generation_attempted": False,
        "result_mp4": None,
    }


def allowed_one_shot():
    if os.environ.get("GITHUB_EVENT_NAME") != "pull_request":
        return False
    if os.environ.get("GITHUB_HEAD_REF") != BRANCH:
        return False
    if os.environ.get("NIGHTFALL_LTX25_ONE_SHOT") != "YES":
        return False
    event = os.environ.get("GITHUB_EVENT_PATH")
    try:
        data = json.loads(Path(event).read_text(encoding="utf-8")) if event else {}
        return data.get("action") == "opened"
    except (ValueError, OSError, TypeError):
        return False


def trial(report, client_factory=None):
    if not allowed_one_shot():
        report["status"] = "BLOCKED_NOT_ORIGINAL_PR_OPEN_EVENT"
        return 2
    # Explicitly refuse any supplied HF_TOKEN so no prepaid credits can be used.
    if os.environ.get("HF_TOKEN"):
        report["status"] = "BLOCKED_UNEXPECTED_HF_TOKEN"
        return 2
    report["zero_gpu_account_mode"] = "anonymous_no_card_no_token"
    if client_factory is None:
        from gradio_client import Client, handle_file
        client_factory = Client
    else:
        from gradio_client import handle_file

    try:
        client = client_factory(SPACE, token=None)
        # Public metadata only; never guess endpoint or silently use another Space.
        api = client.view_api(return_format="dict")
        endpoints = api.get("named_endpoints", {})
        entry = endpoints.get(ENDPOINT)
        if not isinstance(entry, dict):
            report["status"] = "BLOCKED_LTX25_API_MISMATCH"
            report["available_api_names"] = list(endpoints)[:12]
            return 2
        parameters = entry.get("parameters") or []
        if len(parameters) != 10:
            report["status"] = "BLOCKED_LTX25_API_SCHEMA_CHANGED"
            report["endpoint_parameter_count"] = len(parameters)
            return 2
        report["generation_attempted"] = True
        # Single request, no retries, no credential; prompt enhancement off.
        output = client.predict(
            PROMPT, handle_file(str(IMAGE)), HEIGHT, WIDTH, DURATION, SEED,
            DECODER, False, False, False,
            api_name=ENDPOINT
        )
        # Official demo returns (video, used_prompt, seed, length)
        if not isinstance(output, (list, tuple)) or not output:
            raise RuntimeError("Official Space returned no video tuple")
        first = output[0]
        if isinstance(first, dict):
            first = first.get("video") or first.get("path") or first.get("name")
        video = Path(first) if isinstance(first, str) else None
        if video is None or not video.is_file() or video.suffix.lower() != ".mp4":
            raise RuntimeError("Official Space did not return a local MP4 file")
        dest = OUTPUT / "ltx25_ember_first_shot_unapproved.mp4"
        OUTPUT.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(video, dest)
        if dest.stat().st_size < 10000:
            raise RuntimeError("LTX-2.5 video artifact suspiciously small")
        metadata = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries",
             "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate",
             "-of", "json", str(dest)],
            check=True, capture_output=True, text=True, timeout=30
        )
        probed = json.loads(metadata.stdout)
        video_stream = next((s for s in probed.get("streams", [])
                             if s.get("codec_type") == "video"), None)
        seconds = float(probed.get("format", {}).get("duration") or 0)
        if video_stream is None or seconds < 1.0:
            raise RuntimeError("No valid moving LTX-2.5 video stream")
        report["video_metadata"] = probed
        report["result_mp4"] = dest.name
        report["status"] = "UNAPPROVED_LTX25_VIDEO_CANDIDATE"
        report["technical_video_found"] = True
        return 0
    except Exception as exc:
        report["status"] = "BLOCKED_FREE_PROVIDER_OR_QUOTA"
        report["failure_type"] = type(exc).__name__
        # Never expose authentication strings or URLs with ephemeral tokens.
        detail = str(exc)
        for k in ("HF_TOKEN", "AGNES_API_KEY", "KAGGLE_API_TOKEN"):
            value = os.environ.get(k)
            if value:
                detail = detail.replace(value, "[REDACTED]")
        report["error"] = detail[:350]
        return 2


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("audit", "trial"), default="audit")
    args = parser.parse_args()
    report = audit()
    outcome = trial(report) if args.mode == "trial" else 0
    save(report)
    print("LTX25_STATUS:", report["status"])
    print("LTX25_VIDEO_CREATED:", bool(report["result_mp4"]))
    print("E01_FULL_EPISODE_CREATED: False")
    print("PUBLIC_PUBLISHING: NEVER")
    return outcome


if __name__ == "__main__":
    raise SystemExit(main())
