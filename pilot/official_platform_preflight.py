"""Read-only official OAuth identity preflight for Nightfall publication targets.

This does not upload video, allocate media containers, create drafts, or publish.
Google OAuth refresh needs a token POST; all destination probes use GET only.
Even a successful identity check NEVER proves video.publish/content_publish scopes.
"""
import argparse
import json
import os
from pathlib import Path

OUT = Path("output/e01_full_real_attempt/platform_identity_report.json")
GRAPH = "https://graph.facebook.com/v25.0"
TIKTOK = "https://open.tiktokapis.com/v2/user/info/"
GOOGLE_TOKEN = "https://oauth2.googleapis.com/token"
YOUTUBE = "https://www.googleapis.com/youtube/v3/channels"
PLATFORMS = ("youtube", "facebook", "instagram", "tiktok")


def present(name):
    return bool(os.getenv(name))


def redacted_id(value):
    if not value:
        return None
    value = str(value)
    return "***" + value[-4:]


def official_get(url, *, token, params=None, session=None):
    if session is None:
        import requests
        session = requests
    response = session.get(
        url, headers={"Authorization": "Bearer " + token},
        params=params, timeout=25,
    )
    response.raise_for_status()
    return response.json()


def credential_probe(platform, session=None):
    if session is None:
        import requests
        session = requests
    if platform == "youtube":
        keys = ("YOUTUBE_REFRESH_TOKEN", "YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET")
    elif platform == "facebook":
        keys = ("FB_PAGE_ACCESS_TOKEN",)
    elif platform == "instagram":
        keys = ("INSTAGRAM_ACCESS_TOKEN", "INSTAGRAM_ACCOUNT_ID")
    elif platform == "tiktok":
        keys = ("TIKTOK_ACCESS_TOKEN",)
    else:
        raise ValueError("Unexpected platform")
    out = {
        "platform": platform, "status": "NOT_CONFIGURED",
        "required_credentials_present": {k: present(k) for k in keys},
        "read_only_identity_verified": False,
        "publishing_permission_verified": False,
        "official_video_upload_tested": False,
        "public_post_created": False,
        "media_container_created": False,
    }
    if not all(out["required_credentials_present"].values()):
        out["missing_secret_names"] = [k for k in keys if not present(k)]
        return out
    try:
        if platform == "youtube":
            # OAuth token exchange uses a POST but never uploads or alters YouTube content.
            resp = session.post(GOOGLE_TOKEN, data={
                "grant_type": "refresh_token",
                "refresh_token": os.environ["YOUTUBE_REFRESH_TOKEN"],
                "client_id": os.environ["YOUTUBE_CLIENT_ID"],
                "client_secret": os.environ["YOUTUBE_CLIENT_SECRET"],
            }, timeout=25)
            resp.raise_for_status()
            access = resp.json().get("access_token")
            if not access:
                raise ValueError("No access token after refresh")
            result = official_get(YOUTUBE, token=access, params={
                "part": "id,snippet", "mine": "true", "maxResults": "1"
            }, session=session)
            items = result.get("items") or []
            if not items:
                raise ValueError("OAuth token does not identify an accessible channel")
            out["account_id_redacted"] = redacted_id(items[0].get("id"))
        elif platform == "facebook":
            result = official_get(GRAPH + "/me", token=os.environ["FB_PAGE_ACCESS_TOKEN"],
                                  params={"fields": "id,name"}, session=session)
            if not result.get("id"):
                raise ValueError("Page identity GET returned no id")
            out["account_id_redacted"] = redacted_id(result["id"])
        elif platform == "instagram":
            account = os.environ["INSTAGRAM_ACCOUNT_ID"]
            result = official_get(GRAPH + "/" + account,
                                  token=os.environ["INSTAGRAM_ACCESS_TOKEN"],
                                  params={"fields": "id,username,account_type"},
                                  session=session)
            if str(result.get("id")) != account:
                raise ValueError("IG account ID mismatch")
            out["account_id_redacted"] = redacted_id(account)
            out["account_type"] = result.get("account_type") or "unknown"
        else:
            result = official_get(TIKTOK, token=os.environ["TIKTOK_ACCESS_TOKEN"],
                                  params={"fields": "open_id,display_name"}, session=session)
            if (result.get("error") or {}).get("code") not in ("ok", 0):
                raise ValueError("TikTok identity API rejected request")
            uid = (result.get("data") or {}).get("user", {}).get("open_id")
            if not uid:
                raise ValueError("TikTok API returned no open_id")
            out["account_id_redacted"] = redacted_id(uid)
        out["status"] = "IDENTITY_GET_OK_UPLOAD_SCOPE_UNVERIFIED"
        out["read_only_identity_verified"] = True
    except Exception as exc:
        # Avoid any raw exception/response string: it can contain URL credentials.
        status = getattr(getattr(exc, "response", None), "status_code", None)
        out["status"] = ("BLOCKED_AUTH_OR_SCOPE_HTTP" if status
                         else "BLOCKED_READ_ONLY_PROBE")
        if status:
            out["http_status"] = status
        out["failure_type"] = type(exc).__name__
    return out


def report_all():
    result = {
        "purpose": "official OAuth/account identity checks only; no media upload",
        "all_four_uploads_verified": False,
        "any_content_uploaded": False,
        "publication_executed": False,
        "upload_required_next": "Full approved 120-180s cinematic MP4 with real lipsync",
        "platforms": {name: credential_probe(name) for name in PLATFORMS},
    }
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(OUT))
    args = parser.parse_args()
    report = report_all()
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for name, detail in report["platforms"].items():
        print("OFFICIAL_PLATFORM_IDENTITY", name, detail["status"])
    print("MEDIA_UPLOADS_ATTEMPTED: False")
    print("UPLOAD_SCOPES_VERIFIED: False")
    print("PUBLIC_POSTS_CREATED: False")


if __name__ == "__main__":
    main()
