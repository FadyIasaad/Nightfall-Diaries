"""Nightfall scheduling and publishing gates.

This module does not fake a completed movie or silently publish assets.
It identifies the next eligible episode and reports exactly what is needed
before fully automatic cloud rendering and account publishing can be enabled.
"""
import argparse
import json
import os
from pathlib import Path
from .restore import ROOT, validate_stories

SERIES = (("S01_the_last_little_fox", 12), ("S02_the_boy_who_forgot_tomorrow", 10))
QUALITY_CONFIG = ROOT / "studio" / "production_settings.json"


def next_episode(root=ROOT):
    """Do not advance past any episode without confirmed publishing receipts."""
    for series, _ in SERIES:
        tracker = json.loads((root / "seasons" / series / "episodes" / "episodes.json").read_text(encoding="utf-8"))
        for episode in tracker["episodes"]:
            if episode.get("status") != "PUBLISHED":
                return episode["id"]
            receipt = episode.get("published") or {}
            if not receipt or not all(receipt.get(name) for name in ("youtube", "facebook", "instagram", "tiktok")):
                return episode["id"]
    return None


def readiness(environ=None, root=ROOT):
    env = os.environ if environ is None else environ
    settings = json.loads((root / "studio" / "production_settings.json").read_text(encoding="utf-8"))
    checks = {
        "production_enabled": settings.get("production_enabled") is True,
        "cloud_video_renderer_configured": bool(env.get("NIGHTFALL_VIDEO_PROVIDER_URL") and env.get("NIGHTFALL_VIDEO_PROVIDER_TOKEN")),
        "renderer_integration_tested": settings.get("renderer_verified") is True,
        "first_cinematic_video_approved": settings.get("cinematic_video_approved") is True,
        "voice_and_lipsync_tested": settings.get("voice_lipsync_verified") is True,
        "youtube_upload_verified": settings.get("youtube_verified") is True,
        "facebook_upload_verified": settings.get("facebook_verified") is True,
        "instagram_upload_verified": settings.get("instagram_verified") is True,
        "tiktok_staging_or_upload_verified": settings.get("tiktok_verified") is True,
        "publishing_integration_implemented": settings.get("publishing_implemented") is True,
    }
    return checks


def report(action, episode=None, root=ROOT, environ=None):
    validate_stories(root)
    selected = episode if episode and episode != "auto" else next_episode(root)
    checks = readiness(environ=environ, root=root)
    status = "READY" if all(checks.values()) else "BLOCKED"
    result = {
        "action": action,
        "episode": selected,
        "status": status,
        "checks": checks,
        "missing": [name for name, okay in checks.items() if not okay],
        "scheduled_time": "10:00 Africa/Cairo",
        "rendered_video": False,
        "uploaded_to_any_platform": False,
    }
    if selected is None:
        result["status"] = "SEASONS_COMPLETE"
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", choices=("check_setup", "scheduled", "generate_only", "generate_and_upload"), required=True)
    parser.add_argument("--episode", default="auto")
    parser.add_argument("--report", default="output/production_readiness.json")
    args = parser.parse_args()
    result = report(args.action, args.episode)
    output = Path(args.report)
    output.parent.mkdir(exist_ok=True, parents=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("NIGHTFALL_STATE:", result["status"], "episode:", result["episode"])
    for key in result["missing"]:
        print("BLOCKER:", key)
    if args.action == "scheduled":
        print("DAILY_STANDBY: No generation or posting while providers/quality gates are not connected.")
        return
    if args.action == "check_setup":
        print("PRECHECK_REPORT_READY; no video or publication attempted.")
        return
    # Refuse to claim a functioning rendering/publishing integration.
    raise SystemExit("NOT_LIVE_YET: the cinematic renderer and upload adapters must be implemented and proven first. No video generated or published.")


if __name__ == "__main__":
    main()
