"""Read-only cost/capacity evidence for Nightfall E01 real MP4 checkpoints.

No provider request, GPU allocation, billing, video generation or publishing.
Existing progress.json schema and film-plan checksum are never modified.
"""
import argparse
import json
import os
from pathlib import Path
from statistics import median

def _samples(state, field):
    values = []
    for row in state.get("completed", []):
        telemetry = row.get("gpu_telemetry") or {}
        value = telemetry.get(field)
        if isinstance(value, (int, float)) and not isinstance(value, bool) and 0 < value < 86400:
            values.append(float(value))
    return values

def summarize(state):
    completed = state.get("completed", [])
    wall = _samples(state, "inference_wall_seconds")
    charged = _samples(state, "quota_delta_observed_seconds")
    total = int(state.get("expected_distinct_shots") or 36)
    requested = float(state.get("target_seconds") or 150)
    actual = round(sum(float(row.get("seconds", 0)) for row in completed), 2)
    return {
        "status": "READ_ONLY_MEASURED_CAPACITY_AUDIT",
        "episode": state.get("episode", "S01_the_last_little_fox_E01"),
        "real_shots_completed": len(completed),
        "planned_shots": total,
        "real_motion_seconds": actual,
        "old_pilot_target_seconds": requested,
        "owner_required_min_seconds": 180,
        "owner_required_max_seconds": 360,
        "pilot_meets_owner_minimum": requested >= 180,
        "inference_wall_seconds_samples": len(wall),
        "median_inference_wall_seconds": round(median(wall), 2) if wall else None,
        "quota_delta_samples": len(charged),
        "median_observed_quota_delta_seconds": round(median(charged), 2) if charged else None,
        "quota_calculation_warning": (
            "Observed pre/post quota delta can include other account usage; "
            "it is NOT a reserved allowance or a free-provider entitlement."
        ),
        "candidate_engines_qualified": False,
        "kaggle_gpu_proven_for_this_account": False,
        "paid_fallback_enabled": False,
        "public_publishing_enabled_by_audit": False,
        "completed_film_approved_by_audit": False,
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", default="output/e01_resumable/progress.json")
    p.add_argument("--output", default="output/e01_resumable/capacity_audit.json")
    args = p.parse_args()
    path = Path(args.input)
    if not path.is_file():
        print("NIGHTFALL_CAPACITY_AUDIT: NO_VERIFIED_LOCAL_PROGRESS")
        return 0
    state = json.loads(path.read_text(encoding="utf-8"))
    info = summarize(state)
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("NIGHTFALL_CAPACITY_AUDIT", json.dumps(info, ensure_ascii=False))
    if os.getenv("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write("\n## Actual E01 video capacity — no paid GPU\n\n")
            f.write(f"- Genuine MP4 clips: **{info['real_shots_completed']}/{info['planned_shots']}**\n")
            f.write(f"- Film motion: **{actual_label(info)}**\n")
            f.write(f"- Inference duration samples: **{info['inference_wall_seconds_samples']}**; median: **{info['median_inference_wall_seconds']}s**\n")
            f.write(f"- Read-only quota-delta samples: **{info['quota_delta_samples']}**; median: **{info['median_observed_quota_delta_seconds']} GPU-seconds**\n")
            f.write("- Existing 150-second pilot **fails** owner's 180-second minimum; no automatic timeline/plan edits.\n")
            f.write("- **No engine switch, model charges, video posts, or restored-state modification.**\n")
    return 0

def actual_label(info):
    return f"{info['real_motion_seconds']:.2f}s / {info['old_pilot_target_seconds']:.0f}s pilot"

if __name__ == "__main__":
    raise SystemExit(main())
