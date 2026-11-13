"""One honest daily Telegram status when the free E01 renderer makes no clip.

No paid usage, publishing, or new GPU job. Scheduled runs only. GitHub's
remote receipt prevents duplicate alerts across the primary and backup cron.
"""
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from pilot import e01_free_resume as resume
from pilot import e01_telegram_notify as telegram

ALLOWED_STATES = {
    "PAUSED_FREE_QUOTA_INSUFFICIENT":
        "حصة توليد الفيديو المجانية غير كافية اليوم.",
    "BLOCKED_FREE_PROVIDER_OR_AUTH":
        "محرك الفيديو المجاني أو صلاحيات Hugging Face واجهت مشكلة.",
    "PARTIAL_REAL_MOTION_UNAPPROVED":
        "تم حفظ اللقطات السابقة، ولم تُنتج لقطة جديدة في هذا التشغيل.",
    "ALL_SHOTS_READY_AUTOMATIC_ASSEMBLY_PENDING":
        "اكتملت اللقطات، لكن تجميع الحلقة لم ينته بعد.",
    "TECHNICAL_MP4_ONLY_AWAITING_TRUE_LIPSYNC_AND_VISUAL_QA":
        "تم تجميع فيديو تقني، لكن فحص جودة الحركة ومزامنة الشفاه غير مكتمل.",
}


def local_day():
    return datetime.now(ZoneInfo("Africa/Cairo")).strftime("%Y-%m-%d")


def status_text(state, *, date):
    shots = state.get("completed") or []
    seconds = sum(float(item.get("seconds", 0)) for item in shots)
    status = str(state.get("status") or "")
    details = ALLOWED_STATES.get(status, "لم يتم إنتاج لقطة جديدة؛ راجع تفاصيل تشغيل GitHub.")
    message = [
        "📋 تقرير Nightfall Diaries اليومي — " + date,
        "القصة: The Last Little Fox | الحلقة E01",
        "🎞️ اللقطات المحفوظة: " + str(len(shots)) + " من 36",
        "⏱️ مدة الفيديو الحقيقية المحفوظة: " + f"{seconds:.2f}" + " ثانية",
        "ℹ️ " + details,
        "❌ هذا ليس تقرير نشر؛ لم يتم إثبات نشر الحلقة.",
    ]
    rid = os.getenv("GITHUB_RUN_ID", "")
    if rid.isdigit():
        message.append(
            "تفاصيل التشغيل: https://github.com/FadyIasaad/Nightfall-Diaries/actions/runs/"
            + rid)
    return "\n".join(message)


def report_once(*, state, receipts, save=None, sender=None, date=None):
    result = {"provider": "telegram", "messages_sent": 0, "status": "NOT_SCHEDULED"}
    if (os.getenv("GITHUB_EVENT_NAME") != "schedule"
            or os.getenv("GITHUB_REF") != "refs/heads/main"
            or os.getenv("GITHUB_RUN_ATTEMPT") != "1"):
        return result
    run_id = os.getenv("GITHUB_RUN_ID", "")
    if not run_id:
        result["status"] = "MISSING_RUN_ID"
        return result
    token, chat_id = telegram._bot_credentials()
    if not token:
        result["status"] = "TELEGRAM_SETUP_REQUIRED"
        return result
    date = date or local_day()
    notices = receipts.setdefault("telegram_notifications", {})
    days = notices.setdefault("daily_health", {})
    if days.get(date, {}).get("phase") in ("initiated", "sent", "uncertain"):
        result["status"] = "ALREADY_SENT_FOR_CAIRO_DAY"
        return result

    # A real shot saved in THIS job may have just triggered the separate
    # per-shot notification. Do not duplicate the successful update.
    if state.get("last_real_motion_run_id") == run_id:
        last = (state.get("completed") or [None])[-1]
        if isinstance(last, dict):
            key = f"scene_{last.get('scene', 0):02d}_part_{last.get('part', 0):02d}"
            if notices.get("real_shots", {}).get(key, {}).get("phase") == "sent":
                result["status"] = "REAL_SHOT_NOTICE_ALREADY_SENT"
                return result
    if save is None:
        from studio.crosspost import receipt_save
        save = lambda r: receipt_save(telegram.EPISODE, r)
    if sender is None:
        sender = telegram._send_message
    days[date] = {
        "phase": "initiated",
        "run_id": run_id,
        "shots_completed": len(state.get("completed") or []),
    }
    try:
        save(receipts)
    except Exception as exc:
        days.pop(date, None)
        result["status"] = "RECEIPT_SAVE_FAILED_" + type(exc).__name__
        return result
    try:
        msg = sender(token, chat_id, status_text(state, date=date))
        days[date].update({"phase": "sent", "telegram_message_id": int(msg)})
        result["messages_sent"] = 1
        result["status"] = "DAILY_HEALTH_NOTICE_SENT"
    except Exception as exc:
        days[date].update({"phase": "uncertain", "failure_type": type(exc).__name__})
        result["status"] = "TELEGRAM_OUTCOME_UNKNOWN_NO_AUTOMATIC_DUPLICATE"
    try:
        save(receipts)
    except Exception:
        result["status"] = "FINAL_RECEIPT_WRITE_FAILED_REVIEW"
    return result


def main():
    _, plan = resume.film.scene_plan()
    # Verify each cached MP4 SHA before reporting progress.
    state = resume.load_state(plan)
    try:
        from studio.crosspost import receipts_read
        receipts, _ = receipts_read(telegram.EPISODE)
    except Exception as exc:
        result = {"status": "RECEIPT_READ_FAILED_" + type(exc).__name__}
    else:
        result = report_once(state=state, receipts=receipts)
    print("NIGHTFALL_DAILY_TELEGRAM_RESULT",
          json.dumps(result, ensure_ascii=False))
    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write("\n## Daily Telegram liveness\n\n"
                    "- **Status:** " + result["status"] + "\n"
                    "- **This step never makes a GPU request or uploads a video.**\n")


if __name__ == "__main__":
    main()
