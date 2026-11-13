"""Continue real E01 clips immediately while registered-free quota permits.

Each successful SHA-locked clip is announced on Telegram BEFORE the next
GPU request. A quota pause, provider error, 36/36 completion, or safety
time limit stops the loop; no paid overquota, fabricated shot, or public post.
"""
import json
import os
import time

from pilot import e01_free_resume as resume
from pilot import e01_telegram_notify as telegram

MAX_NEW_SHOTS = 36
MAX_SECONDS_IN_BATCH = 110 * 60


def report_shot(state, *, load_receipts=None, notify=None):
    """A failed notification may not fake delivery or destroy produced MP4s."""
    if load_receipts is None:
        from studio.crosspost import receipts_read
        load_receipts = lambda: receipts_read(telegram.EPISODE)[0]
    if notify is None:
        notify = telegram.notify_progress_once
    try:
        receipt = load_receipts()
        result = notify(state=state, receipts=receipt)
    except Exception as exc:
        result = {"status": "TELEGRAM_NOTIFICATION_ERROR_" + type(exc).__name__,
                  "messages_sent": 0}
    # Only bounded non-secret fields from this known internal result.
    safe = {"status": str(result.get("status", "UNKNOWN")),
            "messages_sent": int(result.get("messages_sent", 0))}
    print("NIGHTFALL_E01_EACH_SHOT_TELEGRAM", json.dumps(safe))
    return safe


def continue_free(*, single_shot=None, plan_loader=None, alert=None,
                  monotonic=None, max_new_shots=MAX_NEW_SHOTS,
                  max_elapsed_seconds=MAX_SECONDS_IN_BATCH):
    single_shot = single_shot or resume.resume_one_shot
    plan_loader = plan_loader or resume.film.scene_plan
    alert = alert or report_shot
    monotonic = monotonic or time.monotonic
    _, plan = plan_loader()
    start = monotonic()
    new_shots = 0
    alerts_sent = 0
    alert_failures = 0
    final = None
    stopped = None
    while new_shots < max_new_shots:
        if monotonic() - start >= max_elapsed_seconds:
            stopped = "BATCH_SAFE_TIME_LIMIT"
            break
        before = len(resume.load_state(plan)["completed"])
        if before == 36:
            stopped = "ALL_36_GENUINE_CLIPS_DONE"
            break
        try:
            final = single_shot(allow_same_run_retry=True)
        except Exception as exc:
            # The E01 renderer already checkpoints the specific safe error type.
            stopped = "FREE_PROVIDER_OR_AUTH_ERROR_" + type(exc).__name__
            break
        after_state = resume.load_state(plan)
        after = len(after_state["completed"])
        if after > before + 1 or after < before:
            raise RuntimeError("Unsafe unexpected clip count change")
        if after == before:
            stopped = str(final.get("state", "NO_NEW_REAL_SHOT"))
            break
        # Do not start the next part until this completed part was reported.
        # Even Telegram auth failure does not destroy valid paid-free footage.
        new_shots += 1
        reported = alert(after_state)
        alerts_sent += int(reported.get("messages_sent", 0))
        if reported.get("status") != "REAL_MOTION_SHOT_NOTIFICATION_SENT":
            alert_failures += 1
    else:
        stopped = "MAX_GENUINE_SHOTS_FOR_THIS_RUN"

    state = resume.load_state(plan)
    result = {
        "episode": resume.film.EPISODE,
        "status": stopped,
        "new_real_shots_in_this_run": new_shots,
        "shots_completed": len(state["completed"]),
        "shots_expected": 36,
        "telegram_messages_sent": alerts_sent,
        "telegram_alerts_not_confirmed": alert_failures,
        "state": state.get("status"),
        "paid_gpu_calls": False,
        "public_posts_created": False,
    }
    print("NIGHTFALL_CONTINUOUS_REAL_MOTION", json.dumps(result))
    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write("\n## E01 immediate free-quota shot-by-shot continuation\n\n")
            for k in ("status", "new_real_shots_in_this_run", "shots_completed",
                      "telegram_messages_sent", "telegram_alerts_not_confirmed"):
                f.write("- **" + k + ":** " + str(result[k]) + "\n")
            f.write("- **Public posting:** NOT attempted here\n")
    return result


if __name__ == "__main__":
    continue_free()
