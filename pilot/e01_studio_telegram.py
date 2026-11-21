"""Free Telegram progress alerts for Nightfall's actual E01 studio.

Sends no secret in a log. Distinguishes actual MP4 from mocked test status,
says auto-ranked is NOT owner-level or lip-sync approval, and never declares
the unfinished episode published.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import urllib.request

OUTPUT=Path("output/e01_free_ai_studio/telegram_receipt.json")
STATUS=Path("output/e01_free_ai_studio/studio_state.json")
REPO="FadyIasaad/Nightfall-Diaries"


def message_for(phase, state=None, run_id=""):
    url=f"https://github.com/{REPO}/actions/runs/{run_id}" if run_id.isdigit() else f"https://github.com/{REPO}/actions"
    prefix="🎬 Nightfall Diaries — The Last Little Fox E01\n"
    if phase=="start":
        return (prefix+"🔄 بدأت دورة إنتاج/فحص جديدة للّقطة الأصلية.\n"
                "💰 0$ — فيديو حقيقي فقط، بدون تحريك صور أو خدمات مدفوعة.\n"
                "سأرسل الحالة الفعلية سواء نجحت أو فشلت.\n"+url)
    if phase!="result":
        raise ValueError("INVALID_TELEGRAM_EVENT")
    state=state or {}
    status=state.get("status","FAILED_BEFORE_REPORT_WRITTEN")
    complete=state.get("completed_technical_shots") or []
    best=state.get("automatic_best_candidates") or {}
    last=(complete[-1] if complete else {})
    score=(last.get("automatic_quality") or {}).get("score_0_to_100")
    summary={
       "AUTO_SHORTLISTED_TECHNICAL_MOTION_NOT_SEMANTICALLY_APPROVED":
           "✅ تم حفظ فيديو AI حقيقي واختيار أفضل مرشح تقنيًا. جودة القصة والشفاه لم تجتز الفحص بعد.",
       "AUTO_REJECTED_WEAK_MOTION_OR_FRAMING":
           "❌ تم رفض المقطع تلقائيًا بسبب ضعف الحركة/التفاصيل أو الإطار، وتم الاحتفاظ به للمراجعة.",
       "AUTO_REJECTED_STORY_BACKGROUND_OR_FRAMING":
           "❌ رُفض المقطع لأن الخلفية/إطار التصوير لا يطابقان القصة. النسخة السابقة محفوظة، وسيستخدم التشغيل التالي الصورة السينمائية النارية المعتمدة.",
       "READ_ONLY_VISUAL_REJECTION_RECONCILIATION_NO_NEW_CHANGE":
           "ℹ️ تم فحص سجل رفض اللقطات فقط، بدون استهلاك أي GPU أو إنتاج مقطع جديد.",
       "BLOCKED_FREE_ZEROGPU_QUOTA_NEXT_DAY":
           "⏸️ رفض المحرك المجاني الحصة اليوم. لم تُستخدم خدمة مدفوعة ولم تحدث إعادة محاولة.",
       "ALREADY_TRIED_ONE_FREE_GPU_CALL_TODAY":
           "⏭️ تم استخدام المحاولة المجانية لهذا اليوم، لا يوجد طلب جديد.",
       "PROVIDER_OR_MEDIA_FAILURE_NO_FALLBACK":
           "⚠️ المحرك أو الملف فشل. لا توجد نسخة بديلة وهمية ولا نشر.",
       "BLOCKED_MOSS_APPROVED_REFERENCE_REQUIRED":
           "⏸️ مشاهد Moss تتطلب مرجعًا بصريًا حقيقيًا؛ ممنوع استعمال صورة Ember مكانها.",
    }
    lines=[prefix+"📋 نتيجة تشغيل إنتاج الحلقة E01",
           "الحالة: "+status,
           summary.get(status,"ℹ️ لم يثبت إنتاج فيديو مقبول في هذا التشغيل."),
           f"🎞️ اللقطات المسجلة تقنيًا: {len(complete)} من 45",
           f"🏆 المرشحون المرتبون تلقائيًا: {len(best)}",
           "🔒 الصوت والتعبيرات ومطابقة القصة لم تعتمد؛ لا نشر عام تلقائي."]
    if score is not None:
        lines.append(f"📊 آخر تقييم حركة/تفاصيل (ليس تقييمًا سينمائيًا شاملاً): {score}/100")
    lines.append(url)
    return "\n".join(lines)


def send(phase, state=None):
    result={"phase":phase,"delivered":False,"status":"NOT_SENT"}
    event=os.getenv("GITHUB_EVENT_NAME","")
    if os.getenv("GITHUB_REF")!="refs/heads/main" or event not in ("schedule","workflow_dispatch","push"):
        result["status"]="NOT_MAIN_PRODUCTION_EVENT"
    elif os.getenv("GITHUB_RUN_ATTEMPT","1")!="1":
        result["status"]="RETRY_DUPLICATE_NOTIFICATION_SKIPPED"
    else:
        token=os.getenv("TELEGRAM_BOT_TOKEN","")
        chat_id=os.getenv("TELEGRAM_CHAT_ID","")
        if not token or not chat_id:
            result["status"]="TELEGRAM_SECRETS_NOT_CONFIGURED"
            result["missing_secret_names"]=[
              name for name,value in (("TELEGRAM_BOT_TOKEN",token),("TELEGRAM_CHAT_ID",chat_id))
              if not value]
        else:
            text=message_for(phase,state,os.getenv("GITHUB_RUN_ID",""))
            request=urllib.request.Request(
                "https://api.telegram.org/bot"+token+"/sendMessage",
                data=json.dumps({"chat_id":chat_id,"text":text,
                                 "disable_web_page_preview":True},ensure_ascii=False).encode(),
                headers={"Content-Type":"application/json"},
                method="POST")
            try:
                with urllib.request.urlopen(request,timeout=25) as resp:
                    # Telegram Bot API sendMessage echoes the original text and
                    # message metadata; for long multilingual result notices its
                    # valid JSON body may exceed 2048 bytes. Truncation caused
                    # JSONDecodeError even though start-notice delivery worked.
                    payload=resp.read(131073)
                    if len(payload)>131072:
                        raise RuntimeError("TELEGRAM_RESPONSE_UNEXPECTEDLY_LARGE")
                    data=json.loads(payload)
                if not data.get("ok") or not (data.get("result") or {}).get("message_id"):
                    raise RuntimeError("NO_TELEGRAM_MESSAGE_RECEIPT")
                result.update({"status":"SENT","delivered":True,
                               "message_id":int(data["result"]["message_id"])})
            except Exception as exc:
                # The exception message can include the bot token in the URL.
                # NEVER log it, especially in CI output or GitHub artifacts.
                result["status"]="TELEGRAM_SEND_FAILED_"+type(exc).__name__
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("E01_TELEGRAM_"+phase.upper(),result["status"],flush=True)
    return result


def main():
    arg=argparse.ArgumentParser()
    arg.add_argument("--phase",choices=("start","result"),required=True)
    args=arg.parse_args()
    state=None
    if args.phase=="result" and STATUS.is_file():
        try:
            state=json.loads(STATUS.read_text(encoding="utf-8"))
        except (ValueError,OSError):
            state={"status":"INVALID_OR_MISSING_STUDIO_REPORT"}
    send(args.phase,state)


if __name__=="__main__":
    main()
