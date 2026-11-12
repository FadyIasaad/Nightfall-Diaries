"""One zero-billing LTX-2.5 image-to-video trial of the NEW cinematic Ember still.

Not a finished E01, not a voice/lip-sync test, and NEVER an upload.
This file deliberately cannot approve any release or social publishing.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from studio.restore import ROOT, validate_stories
from studio.continuity import sha256, locked_cast
from studio.screenplay import load_screenplay

MODEL_SPACE = "Lightricks/LTX-2.5"
API_NAME = "/run"
EPISODE_ID = "S01_the_last_little_fox_E01"
SERIES = "S01_the_last_little_fox"
BRANCH = "pilot/ember-cinematic-ltx25-20261113"
IMAGE = ROOT / "pilot/assets/ember_cinematic_fullbody_512.webp"
IMAGE_SHA256 = "c6cfda4f199c13d5fdf6d4e5057026d718787a495aefc29125c06779eb662432"
OUTPUT = ROOT / "output/ember_cinematic_ltx25"
REPORT = OUTPUT / "trial.json"
VIDEO = OUTPUT / "ember_cinematic_2sec_unapproved.mp4"
PROMPT = (
    "First shot of the original animated adventure The Night the Forest Burned. "
    "The first frame is an EXACT reference for the design, materials, hair grooming "
    "and identity of Ember, a russet fox cub with expressive amber eyes, soft "
    "individually groomed fur, a white tip on LEFT ear only and a turquoise "
    "woven scarf with exactly ONE gold star. Ember takes three believable "
    "grounded paw steps across a mossy forest ledge. He suddenly notices a "
    "distant glowing blaze; his eyes widen, brows furrow, his ear pivots and "
    "his expression changes to genuine fear. Subtle tail, fur, and scarf physics, "
    "natural animal anatomy and weight transfer. Cinematic tracking camera, "
    "warm fire rim light, cool blue twilight shadows, rich forest atmosphere, "
    "volumetric mist and soft depth of field. Beautiful original high-budget "
    "stylized 3D animated feature-film CGI. Hold character identity and scarf "
    "detail at every frame. NO TEXT, no title, no captions, no logo, no extra "
    "star, no lip movement or dialogue, no character morphing, no still zoom."
)


def build_report():
    if validate_stories() != 22:
        raise RuntimeError("Source stories changed")
    cast = locked_cast(SERIES)
    screenplay = load_screenplay(EPISODE_ID)
    if len(screenplay["scenes"]) != 14 or len(cast) != 5:
        raise RuntimeError("E01 source/cast mismatch")
    settings = json.loads((ROOT / "studio/production_settings.json").read_text())
    config = json.loads((ROOT / "config.json").read_text())
    if settings.get("production_enabled") or settings.get("publishing_implemented") or config.get("public_publish_enabled"):
        raise RuntimeError("Pilot only allowed while all public release gates stay disabled")
    if not IMAGE.is_file() or sha256(IMAGE) != IMAGE_SHA256:
        raise RuntimeError("The new approved-style visual asset is missing or altered")
    return {
        "episode": EPISODE_ID, "status": "REFERENCE_READY_NO_VIDEO_APPROVAL",
        "provider": MODEL_SPACE, "api_name": API_NAME,
        "new_cinematic_reference": IMAGE.relative_to(ROOT).as_posix(),
        "new_cinematic_reference_sha256": IMAGE_SHA256,
        "original_reference_unchanged": True,
        "story_count": 22, "E01_scene_count": 14, "locked_cast_count": 5,
        "width": 576, "height": 1024, "duration_request_seconds": 2,
        "paid_provider_called": False, "hf_access_token_used": False,
        "generation_attempted": False, "single_clip_created": False,
        "full_episode_generated": False, "voice_lipsync_verified": False,
        "cinematic_quality_approved": False, "social_upload_attempted": False,
        "video_file": None,
        "blockers": [
            "Only one short free motion proof, NOT all 14 E01 scenes",
            "No Kokoro speech or character lip-sync integrated into the proof",
            "ZeroGPU free quota cannot guarantee a complete daily film",
            "Public publishing intentionally closed until full quality and platform tests"
        ],
    }


def allowed():
    if not (
        os.getenv("GITHUB_EVENT_NAME") == "pull_request"
        and os.getenv("GITHUB_HEAD_REF") == BRANCH
        and os.getenv("GITHUB_RUN_ATTEMPT") == "1"
        and os.getenv("NIGHTFALL_EMBER_LTX_ONCE") == "YES"
    ):
        return False
    try:
        event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    except (OSError, KeyError, ValueError):
        return False
    return event.get("action") == "opened"


def save(report):
    OUTPUT.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run_trial(report, client_factory=None, image_handler=None):
    if not allowed():
        report["status"] = "BLOCKED_NOT_PR_FIRST_OPEN_RUN"
        return 2
    # Explicitly refuse paid/token-backed routes. ZeroGPU anonymous only.
    if any(os.getenv(x) for x in ("HF_TOKEN", "AGNES_API_KEY", "RUNWAY_API_KEY", "LTX_API_KEY")):
        report["status"] = "BLOCKED_ANY_GENERATION_TOKEN_PRESENT"
        return 2
    try:
        if client_factory is None:
            from gradio_client import Client, handle_file
            client_factory, image_handler = Client, handle_file
        elif image_handler is None:
            image_handler = lambda x: x  # offline tests only
        OUTPUT.mkdir(parents=True, exist_ok=True)
        # Official demo image upload is PIL/PNG-friendly; preserve source WebP bytes.
        png = OUTPUT / "ember_cinematic_from_webp.png"
        subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
             "-i", str(IMAGE), "-frames:v", "1", str(png)],
            check=True, capture_output=True, text=True, timeout=30
        )
        client = client_factory(MODEL_SPACE, token=None)
        # Check public schema before sending any GPU inference request.
        info = client.view_api(return_format="dict")
        endpoint = (info.get("named_endpoints") or {}).get(API_NAME)
        if not isinstance(endpoint, dict) or len(endpoint.get("parameters") or []) != 10:
            report["status"] = "BLOCKED_OFFICIAL_LTX_API_SCHEMA_CHANGED"
            return 2
        report["generation_attempted"] = True
        output = client.predict(
            PROMPT, image_handler(str(png)), 1024, 576, 2.0, 41,
            "diffusion", False, False, False, api_name=API_NAME
        )
        first = output[0] if isinstance(output, (list, tuple)) and output else None
        if isinstance(first, dict):
            first = first.get("video") or first.get("path") or first.get("name")
        if not isinstance(first, str):
            raise RuntimeError("No file result from official LTX Space")
        src = Path(first)
        if not src.is_file() or src.suffix.lower() != ".mp4":
            raise RuntimeError("LTX response did not include a local MP4")
        shutil.copyfile(src, VIDEO)
        if VIDEO.stat().st_size < 10000:
            raise RuntimeError("MP4 candidate too small")
        probed = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries",
             "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate",
             "-of", "json", str(VIDEO)],
            check=True, text=True, capture_output=True, timeout=30
        )
        media = json.loads(probed.stdout)
        v = next((s for s in media.get("streams", []) if s.get("codec_type") == "video"), None)
        secs = float(media.get("format", {}).get("duration") or 0)
        if not v or secs < 1 or v.get("width", 0) < 512 or v.get("height", 0) < 900:
            raise RuntimeError("Real moving video track missing or too short/small")
        report["video_metadata"] = media
        report["video_file"] = VIDEO.name
        report["single_clip_created"] = True
        report["status"] = "UNAPPROVED_CINEMATIC_REFERENCE_MOTION_PROOF"
        return 0
    except Exception as exc:
        report["status"] = "BLOCKED_FREE_PROVIDER_OR_TECHNICAL_ERROR"
        report["error_type"] = type(exc).__name__
        msg = str(exc)[:400]
        for key in ("HF_TOKEN", "AGNES_API_KEY", "RUNWAY_API_KEY", "LTX_API_KEY"):
            token = os.getenv(key)
            if token:
                msg = msg.replace(token, "[REDACTED]")
        report["error"] = msg
        return 2
    finally:
        save(report)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "audit"
    if mode not in ("audit", "trial"):
        raise SystemExit("Usage: python -m pilot.ember_cinematic_trial audit|trial")
    report = build_report()
    code = run_trial(report) if mode == "trial" else 0
    save(report)
    print("EMBER_CINEMATIC_STATUS:", report["status"])
    print("SINGLE_CLIP_GENERATED:", report["single_clip_created"])
    print("FULL_EPISODE_GENERATED: False")
    print("PUBLIC_POSTING: NEVER")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
