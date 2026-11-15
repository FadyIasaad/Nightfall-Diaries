"""Nightfall E01: cost-safe, read-only backup video engine candidate.

Everypixel Labs' official 2026-11-15 offer is a one-time 10-second trial
for eligible models, NOT free uninterrupted production. The accepted tasks
after trial are billable: no automated POSTs until a provider-enforced $0
spending limit is independently demonstrated. This module sends ZERO HTTP
requests and only prepares a real-image-to-video quality benchmark payload.

Do not use as a replacement for confirmed/unconfirmed ongoing Agnes tasks.
"""
import argparse
import json
import os
from pathlib import Path

from pilot.e01_agnes_full_episode_plan import make_plan
from pilot.e01_agnes_production import load, prepare
from pilot.e01_full_run import CINEMATIC_IMAGE, SOURCE_SHA
from studio.continuity import sha256

BASE = Path("output/e01_backup_ltx23")
OUT = BASE / "safe_candidate.json"
ENDPOINT = "https://api.everypixel.com/v1/video_generate"
MODEL = "ltx23"
TRIAL_SECONDS_ONCE = 10
TEST_SECONDS = 5


def decide(agnes_state, trial_seconds_confirmed=0, credentials_present=False,
           hard_zero_spend_enforced=False, owner_reviewed_quality=False):
    """No fallback to another model on a possibly accepted old Agnes POST.

    An official zero-cost *offer* does not enforce spending caps on the API;
    the user must keep $0 as a hard restriction, even if that means pausing.
    """
    pending = agnes_state.get("pending")
    current = agnes_state.get("status")
    if pending is not None:
        return "BLOCKED_AGNES_TASK_PENDING_OR_AMBIGUOUS_DO_NOT_DUPLICATE"
    if int(agnes_state.get("completed_count", len(agnes_state.get("completed", [])))) >= 18:
        return "ALREADY_ALL_AGNES_CLIPS_READY"
    if current not in ("PAUSED_AGNES_QUEUE_FULL_NOT_ADMITTED",
                       "PAUSED_AGNES_QUEUE_FULL_COOLDOWN"):
        return "NO_OFFICIALLY_UNADMITTED_AGNES_TASK"
    if not credentials_present:
        return "BACKUP_EVERYPIXEL_CLIENT_ID_AND_SECRET_NOT_CONNECTED"
    if trial_seconds_confirmed < TEST_SECONDS:
        return "NO_VERIFIED_UNUSED_TRIAL_SECONDS"
    if not hard_zero_spend_enforced:
        return "NO_PROVIDER_ENFORCED_ZERO_SPEND_CAP_NO_POST"
    if not owner_reviewed_quality:
        return "BACKUP_QUALITY_NOT_APPROVED"
    return "ELIGIBLE_FOR_SEPARATELY_AUDITED_API_INTEGRATION_NOT_AUTOMATIC_POST"


def preview(agnes_state):
    canonical = make_plan("d235d66f5f17e19b2020623a5cba0ff78caf2321")
    assert sha256(CINEMATIC_IMAGE) == SOURCE_SHA, "Ember locked image changed"
    original = canonical["shots"][0]
    refs = original["reference_hashes"]
    ember = [r for r in refs if r["character"] == "s01_ember"]
    if len(ember) != 1 or ember[0]["sha256"] != SOURCE_SHA:
        raise RuntimeError("EMBER_REVIEW_REFERENCE_NOT_ORIGINAL")
    # Everypixel LTX23 requires one starting frame, unlike Agnes's
    # multiple reference images. Other character appearances must be
    # visually tested before accepting this as equal continuity.
    request = {
        "model": MODEL, "prompt": original["prompt"], "duration": TEST_SECONDS,
        "resolution": "720p", "aspect_ratio": "9:16",
        "image_url": ember[0]["url"],
    }
    return {
        "episode": canonical["episode"], "source_plan_sha256": canonical["plan_sha256"],
        "provider": "Everypixel Labs", "model": MODEL, "endpoint": ENDPOINT,
        "request_preview": request,
        "one_time_advertised_free_seconds": TRIAL_SECONDS_ONCE,
        "available_trial_seconds_independently_verified": False,
        "provider_enforced_zero_spend_limit_verified": False,
        "existing_agnes_pending": agnes_state.get("pending"),
        "decision": decide(agnes_state),
        "provider_requests_sent": 0, "paid_api_calls": 0,
        "public_publishing_attempted": False,
        "quality_verified": False,
        "note": "Trial is insufficient for 216s episode. Never start billable inference or automatically replace an ambiguous Agnes task.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(OUT))
    args = parser.parse_args()
    plan = prepare()
    state = load(plan)
    status = preview(state)
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
    print("NIGHTFALL_E01_LTX23_ZERO_CHARGE_CANDIDATE", json.dumps({
        "status": status["decision"], "model": MODEL,
        "requests_sent": 0,
        "automatic_fallback_enabled": False,
        "published": False,
    }))


if __name__ == "__main__":
    main()
