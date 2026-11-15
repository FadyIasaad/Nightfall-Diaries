"""Fresh E01 Agnes Flash shot production with durable no-duplicate resume.

This is NOT a fake slideshow, billed fallback, or approval to publish. Strict
account key-type and current-price checks precede every new task submission.
An accepted task is polled by ID on future runs; uncertain submissions are
blocked rather than secretly resubmitted.
"""
import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import subprocess
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

from pilot import e01_agnes_full_episode_plan as script
from studio.agnes_cost_gate import PRICING_URL, fetch_public_get, flash_public_trial_is_zero
from studio.agnes_probe import probe
from studio.continuity import sha256
from studio.restore import ROOT

OUT = ROOT / "output/agnes_e01"
STATE = OUT / "progress.json"
PLAN = OUT / "shot_plan.json"
BILLING = ROOT / "studio/agnes_billing_authorization.json"
REFERENCE_COMMIT = "d235d66f5f17e19b2020623a5cba0ff78caf2321"
CREATE_URL = "https://apihub.agnes-ai.com/v1/videos"
RESULT_URL = "https://apihub.agnes-ai.com/agnesapi"
MODEL = "agnes-video-2.5-flash"
MAX_BYTES = 120 * 1024 * 1024


def atomic_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".temp")
    temp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def prepare():
    plan = script.make_plan(REFERENCE_COMMIT)
    if PLAN.exists():
        existing = json.loads(PLAN.read_text(encoding="utf-8"))
        if existing["plan_sha256"] != plan["plan_sha256"]:
            raise RuntimeError("FRESH_PLAN_CHANGED_DO_NOT_REPLACE_EXISTING_FILM")
    atomic_json(PLAN, plan)
    return plan


def new_state(plan):
    return {
        "schema": plan["schema"], "episode": plan["episode"],
        "plan_sha256": plan["plan_sha256"],
        "completed": [], "pending": None, "status": "PREPARED",
        "full_mp4_verified": False, "voice_files_verified": False,
        "character_lipsync_verified": False, "cinematic_acting_approved": False,
        "public_publish_attempted": False, "billable_fallback_used": False,
        "requests_submitted": 0, "last_completed_utc": None,
        "queue_rejections": 0, "next_allowed_submit_utc": None,
    }


def load(plan):
    if STATE.is_file():
        state = json.loads(STATE.read_text(encoding="utf-8"))
    else:
        if list(OUT.glob("shot_*.mp4")):
            raise RuntimeError("RECORDED_VIDEO_WITHOUT_STATE_DO_NOT_RESTART")
        state = new_state(plan)
        atomic_json(STATE, state)
    if (state.get("schema") != plan["schema"] or
            state.get("episode") != plan["episode"] or
            state.get("plan_sha256") != plan["plan_sha256"]):
        raise RuntimeError("PLAN_HASH_MISMATCH_NO_RESTART")
    records = state.get("completed", [])
    seen = set()
    for item in records:
        idx = item.get("index")
        if not isinstance(idx, int) or not 1 <= idx <= len(plan["shots"]) or idx in seen:
            raise RuntimeError("BAD_COMPLETED_SHOT_INDEX")
        seen.add(idx)
        name = f"shot_{idx:03d}.mp4"
        f = OUT / name
        if item.get("file") != name or not f.is_file() or sha256(f) != item.get("sha256"):
            raise RuntimeError("MISSING_OR_TAMPERED_RENDER_CHECKPOINT_NO_RESTART")
    if seen != set(range(1, len(records) + 1)):
        raise RuntimeError("NON_SEQUENTIAL_RENDER_CHECKPOINT")
    pending = state.get("pending")
    if pending is not None:
        if not isinstance(pending, dict) or pending.get("index") != len(records) + 1:
            raise RuntimeError("CORRUPTED_PENDING_VIDEO_TASK")
    return state


def check_no_charge(key):
    auth = json.loads(BILLING.read_text(encoding="utf-8"))
    for name in ("key_type_verified", "owner_confirmed_default_free_trial",
                 "owner_confirmed_no_agent_plan_or_billable_key",
                 "owner_authorized_zero_charge_generation"):
        if auth.get(name) is not True:
            raise RuntimeError("ACCOUNT_FREE_KEY_TYPE_NOT_VERIFIED_NO_VIDEO_POST")
    if not key:
        raise RuntimeError("AGNES_API_KEY_SECRET_MISSING")
    if not flash_public_trial_is_zero(fetch_public_get(PRICING_URL)):
        raise RuntimeError("OFFICIAL_AGNES_FLASH_FREE_PROMOTION_ENDED")
    if probe(key).get("target_model_listed") is not True:
        raise RuntimeError("AGNES_FLASH_MODEL_NOT_ACCESSIBLE")
    return True


def read_response(req, timeout=45):
    with urlopen(req, timeout=timeout) as resp:
        body = resp.read(500001)
        if len(body) > 500000:
            raise RuntimeError("OVERSIZE_PROVIDER_JSON")
        value = json.loads(body)
        if not isinstance(value, dict):
            raise RuntimeError("UNEXPECTED_PROVIDER_JSON")
        return value


def confirmed_queue_rejection(error):
    """Only Agnes's explicit 503 video_queue_full + null task permits a new attempt.

    Generic HTTP 503, gateway resets, timeouts and malformed errors remain
    AMBIGUOUS, even when no video_id reached the client. Never log the body.
    """
    if getattr(error, "code", None) != 503:
        return False
    try:
        body = error.read(4097)
        if len(body) > 4096:
            return False
        doc = json.loads(body)
    except (ValueError, UnicodeError, OSError, TypeError):
        return False
    return (
        isinstance(doc, dict)
        and str(doc.get("code", "")).strip().casefold().replace(" ", "_")
            in {"video_queue_full", "video_query_full"}
        and doc.get("data") is None
        and not doc.get("video_id")
        and not doc.get("task_id")
    )


def request_shot(shot, state, key):
    # Never revisit an already accepted/uncertain task, even before billing GET.
    if shot["index"] != len(state["completed"]) + 1 or state["pending"]:
        raise RuntimeError("NEVER_SUBMIT_DUPLICATE_OR_OUT_OF_ORDER_SHOT")
    not_before = state.get("next_allowed_submit_utc")
    if not_before and datetime.now(timezone.utc) < datetime.fromisoformat(not_before):
        raise RuntimeError("AGNES_QUEUE_FULL_COOLDOWN_ACTIVE_NO_POST")
    check_no_charge(key)
    payload = {
        "model": MODEL, "prompt": shot["prompt"], "mode": "reference",
        "images": shot["images"], "seconds": str(shot["duration_seconds"]),
        "size": "720P", "aspect_ratio": "9:16", "n": 1,
    }
    if shot["index"] != len(state["completed"]) + 1 or state["pending"]:
        raise RuntimeError("NEVER_SUBMIT_DUPLICATE_OR_OUT_OF_ORDER_SHOT")
    state["pending"] = {
        "index": shot["index"], "status": "SUBMISSION_UNCERTAIN",
        "video_id": None, "created_utc": datetime.now(timezone.utc).isoformat(),
    }
    state["status"] = "SUBMISSION_UNCERTAIN_DO_NOT_AUTORETRY"
    state["requests_submitted"] += 1
    atomic_json(STATE, state)  # must persist BEFORE POST
    headers = {"Authorization": "Bearer " + key,
               "Content-Type": "application/json", "Accept": "application/json"}
    req = Request(CREATE_URL, data=json.dumps(payload).encode("utf-8"),
                  headers=headers, method="POST")
    try:
        result = read_response(req, timeout=90)  # exactly one POST, no fallback
    except HTTPError as exc:
        if confirmed_queue_rejection(exc):
            # Official Agnes response explicitly says the request was rejected
            # before task admission; no video_id exists and no quota charged.
            # Resume at a future scheduled run, never hammer the free queue.
            state["pending"] = None
            state["queue_rejections"] = int(state.get("queue_rejections", 0)) + 1
            state["next_allowed_submit_utc"] = (
                datetime.now(timezone.utc) + timedelta(hours=4)
            ).isoformat()
            state["status"] = "PAUSED_AGNES_QUEUE_FULL_NOT_ADMITTED"
            atomic_json(STATE, state)
            print("AGNES_FLASH_QUEUE_FULL_EXPLICIT_NO_TASK_RETRY_AFTER_COOLDOWN")
            return False
        # Generic 503 may have had an ambiguous outcome. Do not release lock.
        raise
    video_id = result.get("video_id")
    if not isinstance(video_id, str) or not video_id or len(video_id) > 150:
        raise RuntimeError("AMBIGUOUS_PROVIDER_ACCEPTANCE_NO_RESUBMIT")
    state["pending"]["video_id"] = video_id
    state["pending"]["status"] = "ACCEPTED_POLL_BY_ID"
    state["status"] = "POLLING_EXISTING_VIDEO_TASK"
    state["next_allowed_submit_utc"] = None
    atomic_json(STATE, state)
    return True


def download_clip(url, dest):
    p = urlsplit(url)
    if p.scheme != "https" or not p.hostname or p.username or p.password:
        raise RuntimeError("INVALID_PROVIDER_CLIP_URL")
    req = Request(url, method="GET", headers={"Accept": "video/mp4,application/octet-stream"})
    part = dest.with_suffix(".mp4.partial")
    try:
        with urlopen(req, timeout=150) as res, part.open("wb") as out:
            total = 0
            while True:
                block = res.read(1024 * 1024)
                if not block:
                    break
                total += len(block)
                if total > MAX_BYTES:
                    raise RuntimeError("CLIP_EXCEEDS_SAFE_FILE_LIMIT")
                out.write(block)
        if part.stat().st_size < 10240:
            raise RuntimeError("PROVIDER_FILE_TOO_SMALL")
        info = subprocess.run(
            ["ffprobe", "-v", "error", "-of", "json", "-show_entries",
             "format=duration:stream=codec_type,width,height", str(part)],
            capture_output=True, text=True, check=True, timeout=30
        )
        data = json.loads(info.stdout)
        seconds = float(data.get("format", {}).get("duration") or 0)
        v = next((x for x in data.get("streams", [])
                  if x.get("codec_type") == "video"), None)
        if (not v or not 3.5 <= seconds <= 14
                or int(v.get("height", 0)) <= int(v.get("width", 0))):
            raise RuntimeError("PROVIDER_RETURNED_WRONG_VIDEO_DURATION_OR_ORIENTATION")
        part.replace(dest)
        return round(seconds, 3)
    finally:
        part.unlink(missing_ok=True)


def poll(state, key, max_wait_seconds=900):
    pending = state.get("pending")
    if not pending or not pending.get("video_id"):
        return False
    vid = pending["video_id"]
    deadline = time.monotonic() + max_wait_seconds
    while time.monotonic() < deadline:
        req = Request(RESULT_URL + "?" + urlencode({
            "video_id": vid, "model_name": MODEL,
        }), headers={"Authorization": "Bearer " + key,
                     "Accept": "application/json"}, method="GET")
        try:
            result = read_response(req)
        except (HTTPError, URLError, TimeoutError):
            time.sleep(20)
            continue
        status = result.get("status")
        if status == "failed":
            state["status"] = "PROVIDER_TASK_FAILED_REVIEW_REQUIRED"
            atomic_json(STATE, state)
            return False
        if status == "completed":
            link = result.get("url")
            if not isinstance(link, str):
                state["status"] = "COMPLETED_BUT_MEDIA_URL_MISSING_REVIEW_REQUIRED"
                atomic_json(STATE, state)
                return False
            i = pending["index"]
            file = OUT / f"shot_{i:03d}.mp4"
            seconds = download_clip(link, file)
            state["completed"].append({
                "index": i, "scene": script.make_plan(REFERENCE_COMMIT)["shots"][i-1]["scene"],
                "file": file.name, "sha256": sha256(file), "seconds": seconds,
                "video_id": vid, "model": MODEL, "genuine_motion_media": True,
            })
            state["pending"] = None
            state["status"] = "REAL_VIDEO_CLIP_VERIFIED_UNAPPROVED"
            state["last_completed_utc"] = datetime.now(timezone.utc).isoformat()
            atomic_json(STATE, state)
            return True
        time.sleep(20)
    state["status"] = "ACCEPTED_VIDEO_STILL_RUNNING_POLL_NEXT_RUN"
    atomic_json(STATE, state)
    return False


def notify(state):
    """Best-effort one notification per new SHA-verified MP4, not per task."""
    key = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat = os.getenv("TELEGRAM_CHAT_ID", "")
    if not key or not chat or not state["completed"]:
        return
    index = len(state["completed"])
    notices = state.setdefault("telegram_attempts", [])
    if index in notices:
        return
    notices.append(index)
    atomic_json(STATE, state)  # never duplicate notifications
    msg = ("🎬 Nightfall Diaries: تم إنتاج لقطة حقيقية جديدة من الحلقة الأولى.\n"
           + f"اللقطات: {index}/18 | الوقت المنتج: "
           + f"{sum(x['seconds'] for x in state['completed']):.1f} ثانية\n"
           + "هذه ليست حلقة مكتملة أو منشورة.")
    request = Request("https://api.telegram.org/bot" + key + "/sendMessage",
                      data=urlencode({"chat_id": chat, "text": msg}).encode(),
                      method="POST")
    try:
        with urlopen(request, timeout=12) as response:
            response.read(4096)
    except (HTTPError, URLError, TimeoutError):
        pass


def render(max_new):
    plan = prepare()
    state = load(plan)
    key = os.getenv("AGNES_API_KEY", "")
    if os.getenv("GITHUB_EVENT_NAME") not in ("workflow_dispatch", "schedule"):
        raise RuntimeError("RENDER_NOT_AUTHORIZED_OUTSIDE_OWNER_OR_SCHEDULE")
    # No POST or even poll with this key until the owner verifies billing.
    check_no_charge(key)
    new = 0
    while new < max_new and len(state["completed"]) < len(plan["shots"]):
        if state["pending"]:
            if not state["pending"].get("video_id"):
                state["status"] = "AMBIGUOUS_POST_DO_NOT_RETRY"
                atomic_json(STATE, state)
                break
        else:
            if state.get("next_allowed_submit_utc"):
                if datetime.now(timezone.utc) < datetime.fromisoformat(
                        state["next_allowed_submit_utc"]):
                    state["status"] = "PAUSED_AGNES_QUEUE_FULL_COOLDOWN"
                    atomic_json(STATE, state)
                    break
            if request_shot(plan["shots"][len(state["completed"])], state, key) is False:
                break
        if not poll(state, key):
            break
        new += 1
        notify(state)
        # Dynamic free rate limit; this is a voluntary minimum interval.
        if new < max_new:
            time.sleep(65)
    print("NIGHTFALL_AGNES_E01", json.dumps({
        "status": state["status"], "completed": len(state["completed"]),
        "expected": len(plan["shots"]), "new_this_run": new,
        "actual_seconds": round(sum(x["seconds"] for x in state["completed"]), 2),
        "next_allowed_submit_utc": state.get("next_allowed_submit_utc"),
        "queue_rejections": state.get("queue_rejections", 0),
        "public_publish_attempted": False,
    }))
    return state


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=("prepare", "render"), default="prepare")
    p.add_argument("--max-new-shots", type=int, default=3)
    args = p.parse_args()
    if args.mode == "prepare":
        plan = prepare()
        state = load(plan)
        print("AGNES_E01_PREPARED", json.dumps({
            "shots": len(plan["shots"]), "target_seconds": plan["target_seconds"],
            "finished": len(state["completed"]), "pending": state["pending"],
            "paid_generation_attempted": False, "publishing_attempted": False,
        }))
        return
    if not 1 <= args.max_new_shots <= 18:
        raise SystemExit("max-new-shots must be 1-18")
    render(args.max_new_shots)


if __name__ == "__main__":
    main()
