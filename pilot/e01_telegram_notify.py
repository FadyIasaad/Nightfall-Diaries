"""Telegram owner notifications after real E01 assembly and four-platform delivery.

A Telegram success message is sent ONLY when the four platforms have independently
confirmed PUBLIC availability. A separate informational completion message may
report a technically finished film with honest per-platform pending/blocker status.

Never asks for user approval, uses a free Telegram bot, no user's PC, no token
in commits/logs, no claims of published content based on upload acceptance.
"""
import argparse
import json
import os
from pathlib import Path

EPISODE = "S01_the_last_little_fox_E01"
TARGETS = ("youtube", "facebook", "instagram", "tiktok")
GITHUB_ACTIONS = ("https://github.com/FadyIasaad/Nightfall-Diaries/"
                  "actions/workflows/nightfall_story_one_click.yml")


def _bot_credentials():
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        return None, None
    return token, chat_id


def _destinations(receipts):
    return (receipts.get("destinations") or {})


def _media_complete(progress):
    return (progress.get("technical_full_mp4") is True
            and len(progress.get("completed") or []) == 36
            and len(progress.get("voices") or []) == 14
            and bool(progress.get("assembled_video_sha256")))


def _all_public(receipts):
    dest = _destinations(receipts)
    return all(dest.get(x, {}).get("phase") == "confirmed_public"
               and dest[x].get("public_confirmed") is True
               for x in TARGETS)


def _human_status(entry):
    phase = entry.get("phase", "not_attempted")
    return {
        "confirmed_public": "منشور ومؤكد",
        "accepted": "تم قبول الرفع، بانتظار التأكيد",
        "initiated": "طلب رفع قيد التنفيذ/المراجعة",
        "ambiguous": "حالة غير مؤكدة؛ تم منع الرفع المكرر",
        "failed": "فشل — يحتاج مراجعة الصلاحيات",
        "blocked": "متوقف — يحتاج إصلاحًا",
    }.get(phase, "لم يُرفع بعد")


def format_message(kind, progress, receipts):
    episode = "The Last Little Fox — E01"
    lines = []
    if kind == "film_complete":
        lines.extend([
            "🎬 اكتمل تجميع حلقة Nightfall Diaries",
            episode,
            "المدة المستهدفة: 150 ثانية",
            "اكتملت 36 لقطة حقيقية و14 ملف صوت.",
            "",
            "حالة الرفع الآن:",
        ])
    elif kind == "all_public":
        if not _all_public(receipts):
            raise ValueError("Cannot announce four public uploads without four confirmations")
        lines.extend([
            "🎉 اكتملت الحلقة وتم تأكيد نشرها على المنصات الأربع!",
            episode,
            "",
        ])
    else:
        raise ValueError("Unknown Telegram notification kind")
    for label, key in (("YouTube", "youtube"), ("Facebook", "facebook"),
                       ("Instagram", "instagram"), ("TikTok", "tiktok")):
        entry = _destinations(receipts).get(key, {})
        line = "• " + label + ": " + _human_status(entry)
        url = entry.get("public_url")
        if kind == "all_public" and isinstance(url, str) and url.startswith("https://"):
            line += "\n" + url
        lines.append(line)
    if kind == "film_complete" and not _all_public(receipts):
        lines.extend(["", "لم يتم تأكيد النشر على جميع المنصات بعد؛ لن أذكر أنها نُشرت حتى تؤكدها الواجهات الرسمية."])
    lines.extend(["", "متابعة المشروع:", GITHUB_ACTIONS])
    return "\n".join(lines)


def _send_message(token, chat_id, text, session=None):
    """Official Bot API, no third-party messaging plan or WhatsApp billing."""
    if session is None:
        import requests
        session = requests
    try:
        response = session.post(
            "https://api.telegram.org/bot" + token + "/sendMessage",
            json={"chat_id": chat_id, "text": text,
                  "disable_web_page_preview": True},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        if not data.get("ok") or not (data.get("result") or {}).get("message_id"):
            raise RuntimeError("No Telegram message receipt")
        return int(data["result"]["message_id"])
    except Exception as exc:
        # Never emit URL, HTTP response body, or exception text: bot token is in URL.
        raise RuntimeError("TELEGRAM_SEND_FAILED_" + type(exc).__name__) from None


def notify_once(*, state, receipts, save=None, sender=None):
    """Persist an initiated marker BEFORE HTTP call to prevent double alerts."""
    result = {"episode": EPISODE, "provider": "telegram",
              "configured": False, "messages_attempted": 0, "messages_sent": 0,
              "statuses": {}}
    token, chat_id = _bot_credentials()
    if not token:
        result["status"] = "TELEGRAM_SETUP_REQUIRED"
        result["missing_secret_names"] = [
            x for x in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID") if not os.getenv(x)
        ]
        return result
    result["configured"] = True
    if not _media_complete(state):
        result["status"] = "WAITING_FOR_FULL_EPISODE"
        return result
    if save is None:
        from studio.crosspost import receipt_save
        save = lambda r: receipt_save(EPISODE, r)
    if sender is None:
        sender = _send_message
    notices = receipts.setdefault("telegram_notifications", {})
    kinds = ["film_complete"]
    if _all_public(receipts):
        kinds.append("all_public")
    for kind in kinds:
        old = notices.get(kind, {})
        if old.get("phase") in ("initiated", "sent", "uncertain"):
            result["statuses"][kind] = "ALREADY_ATTEMPTED_NO_DUPLICATE"
            continue
        text = format_message(kind, state, receipts)
        notices[kind] = {"phase": "initiated"}
        try:
            save(receipts)
        except Exception as exc:
            result["statuses"][kind] = "BLOCKED_RECEIPT_SAVE_" + type(exc).__name__
            notices.pop(kind, None)
            continue
        try:
            msg_id = sender(token, chat_id, text)
            notices[kind] = {"phase": "sent", "telegram_message_id": int(msg_id)}
            result["messages_sent"] += 1
            result["statuses"][kind] = "SENT"
        except Exception as exc:
            notices[kind] = {"phase": "uncertain", "error_type": type(exc).__name__}
            result["statuses"][kind] = "OUTCOME_UNKNOWN_MANUAL_CHECK_TO_AVOID_DUPLICATE"
        result["messages_attempted"] += 1
        try:
            save(receipts)
        except Exception:
            result["statuses"][kind] = "SENT_STATUS_PERSIST_FAILED_REVIEW"
    result["status"] = "NOTIFICATION_PROCESSED"
    return result


def main():
    from pilot import e01_free_resume as resume
    from studio.crosspost import receipts_read
    from studio.continuity import sha256
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=("completion", "check"), default="completion")
    args = p.parse_args()
    _, plan = resume.film.scene_plan()
    state = resume.load_state(plan)
    if _media_complete(state):
        mp4 = resume.OUT / "S01_the_last_little_fox_E01_full_unapproved.mp4"
        if not mp4.is_file() or sha256(mp4) != state["assembled_video_sha256"]:
            raise RuntimeError("Verified full MP4 missing: do not send completion notification")
    try:
        receipts, _etag = receipts_read(EPISODE)
    except Exception as exc:
        result = {"status": "RECEIPT_READ_FAILED", "error_type": type(exc).__name__}
    else:
        result = notify_once(state=state, receipts=receipts)
    print("TELEGRAM_NIGHTFALL_RESULT", json.dumps(result, ensure_ascii=False))
    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write("\n## Nightfall Telegram owner alert\n\n")
            f.write("- **Status:** " + result["status"] + "\n")
            f.write("- **No approval click is requested.**\n")
            f.write("- **Four-platform public success is never announced without confirmed posts.**\n")


if __name__ == "__main__":
    main()
