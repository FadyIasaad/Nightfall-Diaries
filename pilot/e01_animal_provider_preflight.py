"""Free public E01 animal-speaking providers: READ-ONLY GitHub schedule health.

Never calls Space Gradio endpoints, consumes ZeroGPU, uploads images, supplies
billing credentials, toggles production or validates artistic output.
"""
import argparse
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

OUTPUT = Path("output/e01_animal_provider_preflight.json")
ANONYMOUS_ZEROGPU_SECONDS = 120

PROVIDERS = (
    {"space": "Ammunity/joyvasa-avatar",
     "role": "animal_audio_driven_lipsync",
     "reservation_seconds": 90,
     "verified_animal_capable_upstream": True,
     "note": "JoyVASA explicitly supports animals; community ZeroGPU Space may be paused."},
    {"space": "victor/LongCat-Video-Avatar-1.5",
     "role": "stylized_audio_image_to_video",
     "reservation_seconds": 300,
     "verified_animal_capable_upstream": False,
     "note": "LongCat offers stylized audio+image, but 300s reservation exceeds anonymous quota."},
    {"space": "meituan-longcat/LongCat-Video-Avatar-1.5-Demo",
     "role": "stylized_audio_image_to_video",
     "reservation_seconds": 300,
     "verified_animal_capable_upstream": False,
     "note": "Official LongCat demo; animal mouth/identity quality is not certified."},
)


def classify(provider, runtime):
    stage = str((runtime or {}).get("stage") or "").upper()
    hardware = str((runtime or {}).get("hardware") or "").lower()
    if not runtime or not stage:
        return "UNKNOWN_NO_AUTOMATED_GENERATION"
    if stage not in ("RUNNING",):
        return "PAUSED_OR_UNAVAILABLE"
    if "zero" not in hardware:
        return "NO_CONFIRMED_FREE_ZEROGPU_HARDWARE"
    if provider["reservation_seconds"] > ANONYMOUS_ZEROGPU_SECONDS:
        return "FREE_ANONYMOUS_QUOTA_TOO_SMALL"
    return "CANDIDATE_ONLY_MODEL_AND_QUALITY_UNVERIFIED"


def public_space_metadata(space):
    if os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN"):
        raise RuntimeError("REFUSE_PROVIDER_TOKEN_IN_READ_ONLY_BUDGET_CHECK")
    url = "https://huggingface.co/api/spaces/" + space
    req = urllib.request.Request(url, headers={
        "User-Agent": "Nightfall-Diaries-public-readonly-GitHub-CI/1.0",
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=12) as response:
        if response.status != 200:
            raise RuntimeError("SPACE_PUBLIC_GET_FAILED")
        if int(response.headers.get("Content-Length", "0") or "0") > 512000:
            raise RuntimeError("SPACE_PUBLIC_METADATA_UNEXPECTED_SIZE")
        data = response.read(512001)
        if len(data) > 512000:
            raise RuntimeError("SPACE_PUBLIC_METADATA_TOO_LARGE")
    return json.loads(data)


def audit():
    reports = []
    for provider in PROVIDERS:
        item = {k:v for k,v in provider.items()}
        try:
            info = public_space_metadata(provider["space"])
            runtime = info.get("runtime") or {}
            item["runtime"] = {
                "stage": str(runtime.get("stage") or "UNKNOWN"),
                "hardware": str(runtime.get("hardware") or "UNKNOWN")
            }
            item["readiness"] = classify(provider, runtime)
        except Exception as exc:
            item["readiness"] = "UNKNOWN_NO_AUTOMATED_GENERATION"
            item["error_type"] = type(exc).__name__
        reports.append(item)
    result = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "anonymous_public_READ_ONLY_NO_GPU_NO_PAID_API",
        "checked_episodes": ["S01_the_last_little_fox_E01"],
        "anonymous_zero_gpu_budget_seconds": ANONYMOUS_ZEROGPU_SECONDS,
        "providers": reports,
        "actual_audio_driven_animal_video_generated": False,
        "model_visual_identity_quality_verified": False,
        "complete_episode_ready": False,
        "public_posting_permitted": False,
        "money_spent": 0,
        "note": "Provider runtime does not prove remaining anonymous GPU quota or video quality. A positive candidate still requires a separate manual one-shot test."
    }
    OUTPUT.parent.mkdir(exist_ok=True, parents=True)
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    for item in reports:
        print(item["space"], item["readiness"], flush=True)
    print("E01_PROVIDER_DISCOVERY_ONLY_NO_VIDEO_RENDERED", flush=True)
    return result


if __name__ == "__main__":
    audit()
