"""Read-only official per-platform public-post verification for Nightfall E01.

Accepted processing/upload ID is NOT public availability. Use official APIs,
persist actual confirmation receipts, then Telegram may truthfully announce
four-platform public completion. Never resend video here.
"""
import argparse
import json
import os
import time
from pathlib import Path

from pilot.e01_telegram_notify import EPISODE, TARGETS


def _google_token():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    creds = Credentials(
        token=None, refresh_token=os.environ["YOUTUBE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["YOUTUBE_CLIENT_ID"],
        client_secret=os.environ["YOUTUBE_CLIENT_SECRET"],
        scopes=["https://www.googleapis.com/auth/youtube.readonly"],
    )
    creds.refresh(Request())
    return creds.token


def youtube_public(entry, session):
    token = _google_token()
    response = session.get(
        "https://www.googleapis.com/youtube/v3/videos",
        params={"part": "status,snippet", "id": entry["id"]},
        headers={"Authorization": "Bearer " + token}, timeout=25)
    response.raise_for_status()
    rows = (response.json() or {}).get("items") or []
    if len(rows) != 1 or str(rows[0].get("id")) != str(entry["id"]):
        return None
    row = rows[0]
    expected = os.getenv("YOUTUBE_EXPECTED_CHANNEL_ID", "")
    if not expected or (row.get("snippet") or {}).get("channelId") != expected:
        return None
    status = row.get("status") or {}
    if status.get("privacyStatus") != "public":
        return None
    if status.get("uploadStatus") in ("failed", "rejected", "deleted"):
        return None
    return {"id": entry["id"],
            "public_url": "https://www.youtube.com/watch?v=" + str(entry["id"])}


def facebook_public(entry, session):
    # Facebook Page Video is confirmed only if the API exposes published=true
    # and a permalink for the expected Page; no made-up page URL or status.
    if not os.getenv("FB_EXPECTED_PAGE_ID"):
        return None
    response = session.get(
        "https://graph.facebook.com/" + os.getenv("META_API_VERSION", "v25.0")
        + "/" + str(entry["id"]),
        params={"fields": "id,published,permalink_url,from",
                "access_token": os.environ["FB_PAGE_ACCESS_TOKEN"]},
        timeout=25)
    response.raise_for_status()
    media = response.json() or {}
    author = media.get("from") or {}
    permalink = media.get("permalink_url")
    if (str(media.get("id")) != str(entry["id"])
            or media.get("published") is not True
            or str(author.get("id")) != os.environ["FB_EXPECTED_PAGE_ID"]
            or not isinstance(permalink, str)
            or not permalink.startswith("https://www.facebook.com/")):
        return None
    return {"id": str(entry["id"]), "public_url": permalink}


def instagram_public(entry, session):
    response = session.get(
        "https://graph.facebook.com/" + os.getenv("META_API_VERSION", "v25.0")
        + "/" + str(entry["id"]),
        params={"fields": "id,media_type,media_product_type,permalink,owner",
                "access_token": os.environ["INSTAGRAM_ACCESS_TOKEN"]},
        timeout=25)
    response.raise_for_status()
    media = response.json() or {}
    link = media.get("permalink")
    owner = media.get("owner")
    if isinstance(owner, dict):
        owner = owner.get("id")
    if (str(media.get("id")) != str(entry["id"])
            or media.get("media_type") != "VIDEO"
            or media.get("media_product_type") != "REELS"
            or str(owner) != os.getenv("INSTAGRAM_ACCOUNT_ID", "")
            or not isinstance(link, str) or
            not link.startswith("https://www.instagram.com/")):
        return None
    return {"id": str(entry["id"]), "public_url": link}


def tiktok_public(entry, session):
    response = session.post(
        "https://open.tiktokapis.com/v2/post/publish/status/fetch/",
        json={"publish_id": entry["id"]},
        headers={"Authorization": "Bearer " + os.environ["TIKTOK_ACCESS_TOKEN"],
                 "Content-Type": "application/json"},
        timeout=25)
    response.raise_for_status()
    data = response.json() or {}
    if (data.get("error") or {}).get("code") != "ok":
        return None
    body = data.get("data") or {}
    ids = body.get("publicaly_available_post_id") or []
    if body.get("status") != "PUBLISH_COMPLETE" or not ids:
        return None
    # TikTok public IDs are returned only after moderation and public viewability.
    # Do not invent a username-based URL.
    return {"id": str(entry["id"]), "public_post_id": str(ids[0])}


CHECKS = {
    "youtube": youtube_public,
    "facebook": facebook_public,
    "instagram": instagram_public,
    "tiktok": tiktok_public,
}


def reconcile_once(*, receipts, session=None):
    if session is None:
        import requests
        session = requests
    outcomes = {}
    changed = False
    for name in TARGETS:
        entry = (receipts.get("destinations") or {}).get(name, {})
        if entry.get("phase") == "confirmed_public" and entry.get("public_confirmed") is True:
            outcomes[name] = "ALREADY_CONFIRMED_PUBLIC"
            continue
        if entry.get("phase") != "accepted" or not entry.get("id"):
            outcomes[name] = "NOT_ACCEPTED_OR_NEEDS_MANUAL_REVIEW"
            continue
        try:
            status = CHECKS[name](entry, session)
        except Exception as exc:
            # No raw OAuth or Graph response body is printed or persisted.
            outcomes[name] = "VERIFICATION_ERROR_" + type(exc).__name__
            continue
        if status:
            entry["phase"] = "confirmed_public"
            entry["public_confirmed"] = True
            entry["public_url"] = status.get("public_url")
            if status.get("public_post_id"):
                entry["public_post_id"] = status["public_post_id"]
            outcomes[name] = "CONFIRMED_PUBLIC"
            changed = True
        else:
            outcomes[name] = "NOT_CONFIRMED_PUBLIC_YET"
    return outcomes, changed


def poll_public_status(*, max_seconds=0, sleep_seconds=20, receipts=None,
                       reader=None, writer=None, session=None, sleeper=time.sleep):
    if reader is None:
        from studio.crosspost import receipts_read
        reader = receipts_read
    if writer is None:
        from studio.crosspost import receipt_save
        writer = lambda state: receipt_save(EPISODE, state)
    if receipts is None:
        receipts, _ = reader(EPISODE)
    attempts = max(1, int(max_seconds / max(sleep_seconds, 1)) + 1)
    attempts = min(attempts, 20)
    results = {}
    for i in range(attempts):
        results, changed = reconcile_once(receipts=receipts, session=session)
        if changed:
            writer(receipts)
        if all((receipts.get("destinations") or {}).get(name, {}).get("public_confirmed")
               is True for name in TARGETS):
            break
        # There is no point waiting when no platform is still processing an
        # accepted upload (e.g. missing OAuth or true-lipsync QA blocked it).
        awaiting = any(
            (receipts.get("destinations") or {}).get(name, {}).get("phase") == "accepted"
            for name in TARGETS
        )
        if not awaiting:
            break
        if i < attempts - 1:
            sleeper(sleep_seconds)
    return {
        "episode": EPISODE, "platforms": results,
        "public_confirmed": [
            name for name in TARGETS if
            (receipts.get("destinations") or {}).get(name, {}).get("public_confirmed") is True
        ],
        "all_four_confirmed_public": all(
            (receipts.get("destinations") or {}).get(name, {}).get("public_confirmed") is True
            for name in TARGETS
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wait-seconds", type=int, default=0)
    args = parser.parse_args()
    report = poll_public_status(max_seconds=max(0, min(args.wait_seconds, 180)))
    print("NIGHTFALL_OFFICIAL_PUBLIC_POST_CHECK", json.dumps(report, ensure_ascii=False))
    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write("\n## Nightfall E01 — official public-post verification\n\n")
            for name in TARGETS:
                f.write("- **" + name + ":** " + report["platforms"].get(name, "") + "\n")
            f.write("- **ALL FOUR CONFIRMED PUBLIC:** " +
                    str(report["all_four_confirmed_public"]) + "\n")


if __name__ == "__main__":
    main()
