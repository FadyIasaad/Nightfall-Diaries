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


def format_shot_message(state):
    """One real new AI-video sub-shot, never a model request or still image."""
    completed = state.get("completed") or []
    if not completed:
        raise ValueError("No genuinely completed AI shots")
    if len(completed) > 36:
        raise ValueError("Unexpected number of completed E01 shots")
    last = completed[-1]
    scene, part = last.get("scene"), last.get("part")
    if (not isinstance(scene, int) or not 1 <= scene <= 14
            or not isinstance(part, int) or part < 1
            or not isinstance(last.get("sha256"), str)
            or len(last["sha256"]) != 64):
        raise ValueError("Missing SHA-verified generated motion clip")
    seconds = sum(float(row["seconds"]) for row in completed)
    msg = [
        "🎞️ تم إنتاج جزء فيديو جديد — Nightfall Diaries",
        "القصة: The Last Little Fox | الحلقة E01",
        f"🎬 المشهد {scene} من 14 — الجزء {part}",
        f"✅ اللقطات المكتملة: {len(completed)} من 36",
        f"⏱️ مدة الحركة المنتجة: {seconds:.2f} من أصل 150 ثانية تقريبًا",
    ]
    if len(completed) == 36:
        msg.append("🎬 اكتملت اللقطات، وجار تجميع الأصوات وفحص الفيلم الكامل.")
    else:
        msg.append("🔄 جاري استكمال بقية اللقطات ضمن حصة المحرك المجانية.")
    msg.append("📌 هذه لقطة مكتملة، وليست حلقة منشورة بعد.")
    rid = os.getenv("GITHUB_RUN_ID", "")
    if rid.isdigit():
        msg.append("التشغيل: https://github.com/FadyIasaad/Nightfall-Diaries/actions/runs/" + rid)
    return "\n".join(msg)


def notify_progress_once(*, state, receipts, save=None, sender=None):
    """Send one Telegram message for ONE real shot saved during this exact run.

    GitHub's cumulative artifact can be restored many times. We announce only
    when the renderer has saved last_real_motion_run_id == GITHUB_RUN_ID,
    and persist a remote receipt BEFORE the Telegram HTTP call.
    """
    result = {
        "episode": EPISODE, "provider": "telegram", "messages_sent": 0,
        "messages_attempted": 0, "status": "NO_NEW_REAL_SHOT_THIS_RUN",
    }
    run_id = os.getenv("GITHUB_RUN_ID", "")
    if not run_id or state.get("last_real_motion_run_id") != run_id:
        return result
    token, chat_id = _bot_credentials()
    if not token:
        result["status"] = "TELEGRAM_SETUP_REQUIRED"
        result["missing_secret_names"] = [
            key for key in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID")
            if not os.getenv(key)
        ]
        return result
    completed = state.get("completed") or []
    if not completed:
        result["status"] = "NO_VERIFIED_COMPLETED_CLIP"
        return result
    current = completed[-1]
    scene, part = current.get("scene"), current.get("part")
    if (not isinstance(scene, int) or not 1 <= scene <= 14
            or not isinstance(part, int) or part < 1
            or not isinstance(current.get("sha256"), str)
            or len(current["sha256"]) != 64):
        result["status"] = "UNSAFE_SHOT_CHECKPOINT"
        return result
    key = f"scene_{scene:02d}_part_{part:02d}"
    notices = receipts.setdefault("telegram_notifications", {})
    progress = notices.setdefault("real_shots", {})
    if progress.get(key, {}).get("phase") in ("initiated", "sent", "uncertain"):
        result["status"] = "ALREADY_REPORTED_NO_DUPLICATE"
        return result
    if save is None:
        from studio.crosspost import receipt_save
        save = lambda doc: receipt_save(EPISODE, doc)
    if sender is None:
        sender = _send_message
    progress[key] = {
        "phase": "initiated", "sha256": current["sha256"],
        "run_id": run_id, "shot_index": len(completed),
    }
    try:
        save(receipts)
    except Exception as exc:
        progress.pop(key, None)
        result["status"] = "RECEIPT_SAVE_FAILED_NO_TELEGRAM_" + type(exc).__name__
        return result
    result["messages_attempted"] = 1
    try:
        message_id = sender(token, chat_id, format_shot_message(state))
        progress[key].update({"phase": "sent", "telegram_message_id": int(message_id)})
        result["messages_sent"] = 1
        result["status"] = "REAL_MOTION_SHOT_NOTIFICATION_SENT"
    except Exception as exc:
        progress[key].update({"phase": "uncertain", "failure_type": type(exc).__name__})
        result["status"] = "TELEGRAM_OUTCOME_UNCERTAIN_NO_AUTO_DUPLICATE"
    try:
        save(receipts)
    except Exception:
        result["status"] = "TELEGRAM_RECEIPT_FINAL_SAVE_FAILED_REVIEW"
    result["shot_index"] = len(completed)
    result["scene"] = scene
    result["part"] = part
    return result


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
        verified = entry.get("phase") == "confirmed_public" and entry.get("public_confirmed") is True
        glyph = "✅" if verified else (
            "⏳" if entry.get("phase") in ("accepted", "initiated") else
            "⚠️" if entry.get("phase") in ("ambiguous", "failed", "blocked") else "▫️"
        )
        line = glyph + " " + label + ": " + _human_status(entry)
        url = entry.get("public_url")
        if verified and isinstance(url, str) and url.startswith("https://"):
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
    p.add_argument("--mode", choices=("completion", "check", "progress", "connection-test"),
                   default="completion")
    args = p.parse_args()
    if args.mode == "connection-test":
        if (os.getenv("GITHUB_EVENT_NAME") != "push"
                or os.getenv("GITHUB_REF") != "refs/heads/main"
                or os.getenv("GITHUB_RUN_ATTEMPT") != "1"):
            raise RuntimeError("One-time main-branch Telegram connection test only")
        token, chat_id = _bot_credentials()
        if not token:
            result = {"status": "TELEGRAM_SETUP_REQUIRED"}
            print("TELEGRAM_NIGHTFALL_RESULT", json.dumps(result))
            raise SystemExit(1)
        msg_id = _send_message(
            token, chat_id,
            "✅ تم ربط إشعارات Nightfall Diaries على Telegram بنجاح!\n"
            "🎞️ هيوصلك إشعار مع كل لقطة فيديو حقيقية جديدة، "
            "وتقرير عند اكتمال الحلقة والرفع على المنصات الأربع.\n"
            "ℹ️ دي رسالة اختبار اتصال فقط؛ الحلقة لسه ما اكتملتش."
        )
        result = {"status": "TELEGRAM_CONNECTION_TEST_SENT", "has_message_id": bool(msg_id)}
        print("TELEGRAM_NIGHTFALL_RESULT", json.dumps(result))
        return
    _, plan = resume.film.scene_plan()
    state = resume.load_state(plan)  # SHA-256 verifies all existing real shots
    if args.mode != "progress" and _media_complete(state):
        mp4 = resume.OUT / "S01_the_last_little_fox_E01_full_unapproved.mp4"
        if not mp4.is_file() or sha256(mp4) != state["assembled_video_sha256"]:
            raise RuntimeError("Verified full MP4 missing: no false completion notification")
    # Never pretend Telegram was delivered if remote receipt storage fails.
    try:
        receipts, _etag = receipts_read(EPISODE)
    except Exception as exc:
        result = {"status": "RECEIPT_READ_FAILED", "error_type": type(exc).__name__}
    else:
        if args.mode == "progress":
            result = notify_progress_once(state=state, receipts=receipts)
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
