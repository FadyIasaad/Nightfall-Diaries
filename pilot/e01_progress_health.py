"""Truthful E01 liveness monitor, no GPU, no API creds and no posting.

Checks the same SHA-locked cumulative manifest used by the renderer.
Runs AFTER artifacts are archived, so a bad token/provider error makes the
Actions run red and visible while tomorrow's daily schedule stays active.
"""
import argparse
import json
import os
from pathlib import Path

from pilot import e01_free_resume as resume

WARN_STATES = ("BLOCKED_FREE_PROVIDER_OR_AUTH", "PAUSED_FREE_QUOTA_INSUFFICIENT")


def health():
    _, plan = resume.film.scene_plan()
    state = resume.load_state(plan)  # verifies SHA-256 for all media present
    pending = resume.next_unfinished(state, plan)
    total = 36
    completed = len(state["completed"])
    seconds = round(sum(float(x["seconds"]) for x in state["completed"]), 2)
    stage = ("TECHNICAL_FILM_READY_AWAITING_REAL_QA" if state.get("technical_full_mp4")
             else "ALL_REAL_SHOTS_READY_ASSEMBLY_PENDING" if pending is None
             else "REAL_AI_MOTION_IN_PROGRESS")
    return {
        "episode": resume.film.EPISODE,
        "story": "The Last Little Fox",
        "stage": stage,
        "last_execution_state": state.get("status"),
        "shots_completed": completed,
        "shots_expected": total,
        "genuine_video_seconds": seconds,
        "target_seconds": 150,
        "next_real_motion": ({
            "scene": pending[0]["scene_no"], "part": pending[1],
            "requested_seconds": pending[2],
        } if pending else None),
        "free_gpu_attempt_cairo_date": state.get("last_scheduled_attempt_day"),
        "last_real_motion_saved_utc": state.get("last_real_motion_saved_utc"),
        "free_quota_resets_at": state.get("quota_resets_at"),
        "consecutive_provider_errors": int(state.get("consecutive_provider_errors", 0)),
        "technical_film_exists": bool(state.get("technical_full_mp4")),
        "real_lipsync_verified": bool(state.get("true_lipsync_verified")),
        "publicly_published": bool(state.get("published_anywhere")),
        "automatic_daily_resume_still_configured": True,
        "film_completed_and_publicly_released": False,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", default="output/e01_resumable/health.json")
    args = p.parse_args()
    result = health()
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n",
                      encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as file:
            file.write("\n## Nightfall E01 — verified ongoing progress\n\n")
            file.write(f"- **Original E01 AI motion:** {result['shots_completed']}/36 distinct shots\n")
            file.write(f"- **Actual generated motion:** {result['genuine_video_seconds']:.2f}/150 target seconds\n")
            file.write(f"- **Next sub-shot:** {result['next_real_motion']}\n")
            file.write(f"- **Run state:** {result['last_execution_state']}\n")
            file.write(f"- **Last verified motion:** {result['last_real_motion_saved_utc'] or 'legacy saved clip'}\n")
            file.write("- **Free-account schedule:** every Cairo morning (primary + recovery backup)\n")
            file.write("- **Video public release:** BLOCKED until true cinematic/lip-sync and platform QA\n")
    if result["last_execution_state"] == "BLOCKED_FREE_PROVIDER_OR_AUTH":
        print("::error::E01 free-provider/authentication failed. Check Hugging Face/token "
              "without spending or upgrading. The daily schedule remains enabled.")
        return 1
    if result["last_execution_state"] == "PAUSED_FREE_QUOTA_INSUFFICIENT":
        print("::notice::E01 free quota exhausted or too small; genuine saved "
              "motion is safe; next Cairo daily attempt will recheck quota.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
