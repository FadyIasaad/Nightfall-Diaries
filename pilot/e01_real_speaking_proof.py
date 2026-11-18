"""Nightfall E01: real image+audio talking-fox proof, absolutely no paid API.

This is a *technology test*, not the complete first episode. A human-face
SadTalker model may fail on Ember's animal muzzle; that is an honest blocker.
One ZeroGPU request per job, no automatic fallback, retry, social posting, or
claim of lip-sync quality without viewing the actual generated clip.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/e01_real_speaking_proof"
SOURCE = ROOT / "assets/cinematic_refs/ember_approved_candidate_2026-11-13.webp"
SOURCE_SHA256 = "c6cfda4f199c13d5fdf6d4e5057026d718787a495aefc29125c06779eb662432"
SCRIPT = ROOT / "seasons/S01_the_last_little_fox/screenplays/E01.json"
CAST = ROOT / "seasons/S01_the_last_little_fox/characters/character_registry.json"
SPACE = "henrybit/SadTalker-Demo"
API_NAME = "/generate"
VOICE = OUT / "ember_s01_e01_real_kokoro.wav"
VIDEO = OUT / "ember_s01_e01_speaking_UNAPPROVED.mp4"
PAID_CREDENTIAL_NAMES = (
    "AGNES_API_KEY", "EVERYPIXEL_API_KEY", "RUNWAY_API_KEY",
    "ELEVENLABS_API_KEY", "OPENAI_API_KEY", "DASHSCOPE_API_KEY",
    "HF_TOKEN", "HUGGING_FACE_HUB_TOKEN", "HUGGINGFACEHUB_API_TOKEN",
)
MAX_FREE_REQUESTS = 1


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for data in iter(lambda: f.read(65536), b""):
            h.update(data)
    return h.hexdigest()


def ffprobe(path):
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-of", "json",
         "-show_entries", "format=duration:stream=codec_type,codec_name,width,height",
         str(path)],
        capture_output=True, text=True, check=True, timeout=30
    )
    return json.loads(proc.stdout)


def prepare_voice():
    spec = json.loads(SCRIPT.read_text(encoding="utf-8"))
    cast = json.loads(CAST.read_text(encoding="utf-8"))["characters"]
    ember = next(a for a in cast if a["id"] == "s01_ember")
    if spec["episode_id"] != "S01_the_last_little_fox_E01":
        raise RuntimeError("WRONG_ORIGINAL_EPISODE")
    full = next(s["text"] for s in spec["scenes"] if s["character_id"] == "s01_ember")
    # Short canon-exact E01 passage, no invented dialogue/character voice.
    spoken = "Moss? Can anyone hear me?"
    if spoken not in full:
        raise RuntimeError("CANON_DIALOGUE_DRIFT")
    if ember["voice"]["voice_id"] != "am_puck":
        raise RuntimeError("EMBER_LOCKED_VOICE_DRIFT")
    from studio.neural_audio import render_kokoro
    if not VOICE.exists():
        render_kokoro(spoken, ember, VOICE)
    data = ffprobe(VOICE)
    secs = float(data["format"]["duration"])
    if not 0.5 < secs < 5:
        raise RuntimeError("CANON_VOICE_OUTSIDE_SHORT_TEST_WINDOW")
    return {"spoken": spoken, "voice_id": "am_puck",
            "audio_seconds": round(secs, 3), "audio_sha256": sha(VOICE)}


def validate_movie(path):
    data = ffprobe(path)
    movie = next((x for x in data["streams"] if x["codec_type"] == "video"), None)
    sound = next((x for x in data["streams"] if x["codec_type"] == "audio"), None)
    seconds = float(data["format"]["duration"])
    if not movie or not sound or not 0.5 < seconds < 9:
        raise RuntimeError("NO_REAL_PLAYABLE_SPEAKING_VIDEO_WITH_AUDIO")
    if min(int(movie["width"]), int(movie["height"])) < 200:
        raise RuntimeError("TALKING_VIDEO_TOO_LOW_RESOLUTION")
    # Screen-space blackouts and frozen frames are technical disqualifiers.
    scan = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostdin", "-i", str(path),
         "-vf", "blackdetect=d=0.25:pix_th=0.10,freezedetect=n=-55dB:d=1.5",
         "-an", "-f", "null", "-"],
        capture_output=True, text=True, timeout=150
    )
    if scan.returncode != 0:
        raise RuntimeError("VIDEO_QA_FFMPEG_FAILED")
    if "black_start:" in scan.stderr:
        raise RuntimeError("TALKING_VIDEO_HAS_BLACK_GAP")
    if "freeze_start:" in scan.stderr:
        raise RuntimeError("TALKING_VIDEO_IS_FROZEN")
    return {"duration": round(seconds, 3),
            "width": int(movie["width"]), "height": int(movie["height"]),
            "codec": movie["codec_name"], "audio_codec": sound["codec_name"],
            "sha256": sha(path), "no_black_or_frozen_gaps": True}



FREE_QUOTA_PHRASES = (
    "exceeded your zerogpu runs limit",
    "not enough zerogpu quota",
    "insufficient zerogpu quota",
    "zerogpu quota exceeded",
    "zerogpu runs limit",
)


def is_free_quota_error(error):
    """Only classify explicit ZeroGPU quota denials, not arbitrary API failures."""
    message = str(error).lower()
    return any(phrase in message for phrase in FREE_QUOTA_PHRASES)


def execute(mode):
    OUT.mkdir(parents=True, exist_ok=True)
    report = {
        "episode": "S01_the_last_little_fox_E01",
        "goal": "audio_driven_fox_speaking_identity_proof",
        "model_space": SPACE, "api": API_NAME,
        "candidate_model_trained_for_human_faces": True,
        "animals_supported_or_verified": False,
        "source_original_sha256": SOURCE_SHA256,
        "no_paid_credentials_used": True,
        "requests_allowed_per_run": MAX_FREE_REQUESTS,
        "free_daily_capacity_for_180_second_episode_verified": False,
        "realistic_fox_expression_verified": False,
        "phoneme_lipsync_verified": False,
        "visual_quality_owner_approved": False,
        "complete_episode_ready": False,
        "public_posting_allowed": False,
        "render_2d_fallback": False,
        "status": "STARTED",
        "free_gpu_quota_available": None,
        "no_auto_retry_or_token_escalation": True,
    }
    try:
        if any(os.environ.get(key) for key in PAID_CREDENTIAL_NAMES):
            raise RuntimeError("BLOCKED_PROVIDER_CREDENTIAL_COULD_INCURE_COST")
        if not SOURCE.is_file() or sha(SOURCE) != SOURCE_SHA256:
            raise RuntimeError("LOCKED_ORIGINAL_EMBER_IMAGE_NOT_PRESENT")
        if mode == "generate":
            report["voice"] = prepare_voice()
            # Official Space README advertises ZeroGPU, without own billing.
            # Verify actual live runtime before any inference call.
            from huggingface_hub import HfApi
            info = HfApi().space_info(repo_id=SPACE, expand=["runtime"])
            runtime = getattr(info, "runtime", None)
            hardware = str(getattr(runtime, "hardware", "")).lower()
            if "zero" not in hardware:
                raise RuntimeError("MODEL_NO_LONGER_RUNNING_ON_VERIFIED_FREE_ZEROGPU")
            from gradio_client import Client, handle_file
            client = Client(SPACE, verbose=False)
            endpoints = {str(e.api_name) for e in client.endpoints.values()}
            if API_NAME not in endpoints:
                raise RuntimeError("SADTALKER_PUBLIC_ENDPOINT_NOT_AVAILABLE")
            # One request. The model may refuse animal faces; do NOT fake success
            # or replace it with the old mouth-flap animated picture.
            result = client.predict(
                handle_file(str(SOURCE)), handle_file(str(VOICE)),
                "full", False, 0, 1.0, api_name=API_NAME
            )
            if isinstance(result, (tuple, list)):
                result = result[0]
            if isinstance(result, dict):
                result = result.get("video") or result.get("path")
            if not isinstance(result, str) or not Path(result).is_file():
                raise RuntimeError("ZEROGPU_DID_NOT_RETURN_SPEAKING_MP4")
            shutil.copyfile(result, VIDEO)
            report["actual_media_technical"] = validate_movie(VIDEO)
            report["status"] = "TECHNICALLY_PLAYABLE_HUMAN_ART_REVIEW_REQUIRED"
        else:
            report["status"] = "SOURCE_LOCKED_FREE_PROVIDER_PRECHECK"
    except Exception as exc:
        free_quota_exhausted = is_free_quota_error(exc)
        report["status"] = (
            "BLOCKED_FREE_ZEROGPU_QUOTA"
            if free_quota_exhausted else "BLOCKED_NO_TALKING_QUALITY_CLAIM"
        )
        report["free_gpu_quota_available"] = False if free_quota_exhausted else None
        report["error_type"] = type(exc).__name__
        report["error"] = str(exc)[:300]
        if free_quota_exhausted:
            report["next_action"] = (
                "No video was generated. Stop instead of retrying or adding a "
                "token. Run an explicit manual generate test after free quota "
                "resets; animal-face quality is still unverified."
            )
    finally:
        (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n",
                                         encoding="utf-8")
    print("E01_REAL_SPEAKING_PROOF:", report["status"], flush=True)
    if report["status"] == "BLOCKED_FREE_ZEROGPU_QUOTA":
        # A free provider refusing quota is an expected *readiness blocker*, not
        # a broken application. Green workflow status must NOT be misread as a
        # finished video: the report and GitHub warning explicitly say BLOCKED.
        print("::warning title=Free ZeroGPU quota exhausted::"
              "No talking video generated; no automatic retry, no paid API, "
              "and no additional token is used.")
        return
    if report["status"] == "BLOCKED_NO_TALKING_QUALITY_CLAIM":
        raise SystemExit(1)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["preflight", "generate"], default="preflight")
    args = p.parse_args()
    execute(args.mode)
