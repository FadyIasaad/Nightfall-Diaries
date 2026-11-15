"""One unpublished Agnes Flash Ember proof; prepare is free, run is opt-in only.

Never tries a paid model, alternate route, account rotation, POST retry, or publishing.
Only after the OWNER verifies their Agnes account/key is the default free trial
rather than Agent Plan, AND current official promotional pricing is still $0.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

from pilot.e01_full_run import CINEMATIC_IMAGE, SOURCE_SHA
from studio.agnes_cost_gate import EMBER_PROMPT, PRICING_URL, fetch_public_get, flash_public_trial_is_zero
from studio.agnes_probe import probe

MODEL = "agnes-video-2.5-flash"
CREATE_URL = "https://apihub.agnes-ai.com/v1/videos"
CHECK_URL = "https://apihub.agnes-ai.com/agnesapi"
IMAGE_REVISION = "00d4147b84b7b6bba37ad91bcaa2f867115b138c"
IMAGE_RELATIVE = "assets/cinematic_refs/ember_approved_candidate_2026-11-13.webp"
IMAGE_URL = ("https://raw.githubusercontent.com/FadyIasaad/Nightfall-Diaries/"
             + IMAGE_REVISION + "/" + IMAGE_RELATIVE)
OUTPUT = Path("output/agnes_ember_one_clip")
STATUS_FILE = OUTPUT / "status.json"
CONFIRMATION = "DEFAULT_FREE_TRIAL_NO_AGENT_PLAN_NO_CHARGES"


def build_request():
    """Local SHA check prevents replacing Ember or accidentally using wrong references."""
    if not CINEMATIC_IMAGE.is_file():
        raise RuntimeError("LOCKED_EMBER_REFERENCE_MISSING")
    actual = hashlib.sha256(CINEMATIC_IMAGE.read_bytes()).hexdigest()
    if actual != SOURCE_SHA:
        raise RuntimeError("LOCKED_EMBER_REFERENCE_HASH_MISMATCH")
    return {
        "model": MODEL,
        "mode": "reference",
        "images": [IMAGE_URL],
        "prompt": EMBER_PROMPT,
        "seconds": "5",
        "size": "720P",
        "aspect_ratio": "9:16",
        "n": 1,
    }


def save(state):
    OUTPUT.mkdir(parents=True, exist_ok=True)
    STATUS_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")


def read_json(request, timeout=40):
    """Limit response size; never print secrets or raw error responses."""
    with urlopen(request, timeout=timeout) as response:
        payload = response.read(500_001)
        if len(payload) > 500_000:
            raise RuntimeError("UNEXPECTED_RESPONSE_TOO_LARGE")
        result = json.loads(payload)
        if not isinstance(result, dict):
            raise RuntimeError("UNEXPECTED_RESPONSE_FORMAT")
        return result


def eligibility(key, confirmed):
    if confirmed != CONFIRMATION:
        raise RuntimeError("AGNES_DEFAULT_FREE_TRIAL_NOT_OWNER_CONFIRMED")
    if not key:
        raise RuntimeError("AGNES_SECRET_UNAVAILABLE")
    current = fetch_public_get(PRICING_URL)
    if not flash_public_trial_is_zero(current):
        raise RuntimeError("FLASH_PUBLIC_PRICE_IS_NOT_ZERO")
    catalog = probe(key)
    if not catalog["target_model_listed"]:
        raise RuntimeError("FLASH_NOT_AVAILABLE_ON_THIS_API_KEY")
    # An official public zero-price promotion is NOT independent evidence
    # of the account-specific plan; this must be checked in Agnes console.
    return True


def save_video(url):
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
        raise RuntimeError("PROVIDER_VIDEO_URL_NOT_HTTPS")
    filename = OUTPUT / "ember_agnes_flash_5sec_UNAPPROVED.mp4"
    request = Request(url, method="GET", headers={"Accept": "video/mp4,application/octet-stream"})
    # Read streamed bytes with an upper cap: no huge hidden output.
    with urlopen(request, timeout=120) as response, filename.open("wb") as out:
        total = 0
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > 90 * 1024 * 1024:
                filename.unlink(missing_ok=True)
                raise RuntimeError("VIDEO_EXCEEDS_90MB_LIMIT")
            out.write(chunk)
    if filename.stat().st_size < 2048:
        filename.unlink(missing_ok=True)
        raise RuntimeError("RETURNED_VIDEO_TOO_SMALL")
    return filename


def run(confirmed):
    request_payload = build_request()
    state = {
        "model": MODEL, "reference_sha256": SOURCE_SHA,
        "source_commit": IMAGE_REVISION, "video_requested_seconds": 5,
        "public_publish": False, "existing_e01_shots_unchanged": True,
        "post_requests_attempted": 0, "status": "PREPARED_NOT_SUBMITTED",
    }
    save(state)
    if confirmed is None:
        print("AGNES_EMBER_PREPARED_NO_VIDEO_GENERATION")
        return state
    key = os.getenv("AGNES_API_KEY", "")
    try:
        eligibility(key, confirmed)
        if os.getenv("GITHUB_EVENT_NAME") != "workflow_dispatch":
            raise RuntimeError("ONLY_MANUAL_DISPATCH_MAY_CREATE_ONE_VIDEO")
        headers = {"Authorization": "Bearer " + key, "Content-Type": "application/json",
                   "Accept": "application/json"}
        state["status"] = "SUBMISSION_MAY_HAVE_OCCURRED_DO_NOT_RETRY"
        state["post_requests_attempted"] = 1
        save(state)
        create = Request(CREATE_URL,
                         data=json.dumps(request_payload).encode("utf-8"),
                         headers=headers, method="POST")
        # Exactly one POST. Any HTTP/timeout error is uncertain, never auto-retry.
        created = read_json(create, timeout=75)
        vid = created.get("video_id")
        if not isinstance(vid, str) or not vid or len(vid) > 150:
            raise RuntimeError("NO_VALID_VIDEO_ID_DO_NOT_RETRY")
        state["video_id"] = vid
        state["status"] = "ACCEPTED_WAITING_FOR_VIDEO"
        save(state)
        until = time.monotonic() + 900
        while time.monotonic() < until:
            poll = Request(CHECK_URL + "?" + urlencode({
                "video_id": vid, "model_name": MODEL
            }), headers={"Authorization": "Bearer " + key,
                         "Accept": "application/json"}, method="GET")
            try:
                result = read_json(poll, timeout=35)
            except (HTTPError, URLError, TimeoutError):
                # Only GET is retried. POST is never repeated.
                time.sleep(15)
                continue
            status = result.get("status")
            if status == "failed":
                raise RuntimeError("AGNES_VIDEO_TASK_FAILED")
            if status == "completed":
                url = result.get("url")
                if not isinstance(url, str):
                    raise RuntimeError("COMPLETED_VIDEO_MISSING_URL")
                path = save_video(url)
                state["status"] = "REAL_VIDEO_CREATED_UNAPPROVED"
                state["video_file"] = path.name
                state["bytes"] = path.stat().st_size
                save(state)
                print("AGNES_EMBER_REAL_MP4_CREATED_UNAPPROVED")
                return state
            time.sleep(15)
        state["status"] = "TASK_SUBMITTED_PENDING_DO_NOT_RESUBMIT"
        save(state)
        print("AGNES_EMBER_PENDING_NO_NEW_POST_ALLOWED")
        return state
    except Exception as exc:
        state["status"] = ("BLOCKED_BEFORE_POST" if state["post_requests_attempted"] == 0
                           else "ERROR_OR_UNCERTAIN_DO_NOT_RESUBMIT")
        state["error_type"] = type(exc).__name__
        state["error_code"] = str(exc) if isinstance(exc, RuntimeError) else type(exc).__name__
        save(state)
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("prepare", "run"), default="prepare")
    args = parser.parse_args()
    # 'prepare' never touches a model endpoint or any paid API.
    confirmation = (os.getenv("AGNES_OWNER_CONFIRMS_DEFAULT_FREE_TRIAL")
                    if args.mode == "run" else None)
    result = run(confirmation)
    print(json.dumps({"status": result["status"],
                      "submitted_count": result["post_requests_attempted"],
                      "public_publish": result["public_publish"]}))


if __name__ == "__main__":
    main()
