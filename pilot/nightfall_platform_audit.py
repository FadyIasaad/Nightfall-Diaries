"""Read-only, secret-safe diagnosis of four Nightfall publishing connections.

No public post, media container, upload, secret value, or payment is created.
A successful diagnosis job does NOT mean any platform is ready to publish.
"""
import json
import os
from pathlib import Path

from pilot.e01_completion_publish import token_preflight
from pilot.official_platform_preflight import credential_probe

TARGETS = ("youtube", "facebook", "instagram", "tiktok")
OUT = Path("output/platform_readiness_diagnostic.json")
GRAPH = "https://graph.facebook.com/" + os.getenv("META_API_VERSION", "v25.0")


def _safe_call(fn):
    try:
        return fn(), None
    except Exception as exc:
        response = getattr(exc, "response", None)
        status = getattr(response, "status_code", None)
        return None, {"failure_type": type(exc).__name__, "http_status": status}


def _youtube_matches_expected():
    import requests
    expected = os.getenv("YOUTUBE_EXPECTED_CHANNEL_ID")
    if not expected:
        return {"expected_account_configured": False, "expected_account_matches": False}
    token = requests.post(
        "https://oauth2.googleapis.com/token",
        data={"grant_type": "refresh_token",
              "refresh_token": os.environ["YOUTUBE_REFRESH_TOKEN"],
              "client_id": os.environ["YOUTUBE_CLIENT_ID"],
              "client_secret": os.environ["YOUTUBE_CLIENT_SECRET"]},
        timeout=25)
    token.raise_for_status()
    access = token.json()["access_token"]
    channel = requests.get(
        "https://www.googleapis.com/youtube/v3/channels",
        headers={"Authorization": "Bearer " + access},
        params={"part": "id", "mine": "true", "maxResults": 1},
        timeout=25)
    channel.raise_for_status()
    items = channel.json().get("items", [])
    return {"expected_account_configured": True,
            "expected_account_matches": len(items) == 1 and items[0].get("id") == expected}


def _facebook_matches_expected():
    import requests
    expected = os.getenv("FB_EXPECTED_PAGE_ID")
    page = requests.get(
        GRAPH + "/me",
        params={"fields": "id,name", "access_token": os.environ["FB_PAGE_ACCESS_TOKEN"]},
        timeout=25)
    page.raise_for_status()
    who = page.json()
    return {"expected_account_configured": bool(expected),
            "expected_account_matches": (
                str(who.get("id")) == expected if expected else
                bool(who.get("id")) and who.get("name") == "Nightfall Diaries"),
            "exact_page_name_matches": who.get("name") == "Nightfall Diaries"}


def _tiktok_public_options():
    import requests
    resp = requests.post(
        "https://open.tiktokapis.com/v2/post/publish/creator_info/query/",
        headers={"Authorization": "Bearer " + os.environ["TIKTOK_ACCESS_TOKEN"],
                 "Content-Type": "application/json"},
        json={}, timeout=25)
    resp.raise_for_status()
    data = resp.json()
    error = (data.get("error") or {}).get("code")
    if error not in ("ok", 0):
        return {"creator_info_accepted": False,
                "official_error_code": error if error in (
                    "scope_not_authorized", "access_token_invalid",
                    "rate_limit_exceeded", "unaudited_client_can_only_post_to_private_accounts"
                ) else "OTHER_PLATFORM_ERROR"}
    info = data.get("data") or {}
    return {"creator_info_accepted": True,
            "public_option_offered": "PUBLIC_TO_EVERYONE" in
                (info.get("privacy_level_options") or []),
            "max_video_post_duration_sec": info.get("max_video_post_duration_sec")}


def _instagram_alternative():
    """Identify an Instagram Login token without creating content."""
    import requests
    resp = requests.get(
        "https://graph.instagram.com/v25.0/me",
        headers={"Authorization": "Bearer " + os.environ["INSTAGRAM_ACCESS_TOKEN"]},
        params={"fields": "user_id,username,account_type"}, timeout=25)
    if not resp.ok:
        return {"instagram_login_graph_http_status": resp.status_code,
                "instagram_login_graph_verified": False}
    user = resp.json()
    ident = str(user.get("user_id") or user.get("id") or "")
    return {"instagram_login_graph_verified": bool(ident) and
            ident == os.environ["INSTAGRAM_ACCOUNT_ID"],
            "instagram_login_graph_http_status": resp.status_code,
            "instagram_login_account_type": user.get("account_type", "unknown")}


def _instagram_facebook_error():
    """Meta numeric error only; never disclose token or Graph response message."""
    import requests
    resp = requests.get(
        GRAPH + "/" + os.environ["INSTAGRAM_ACCOUNT_ID"],
        headers={"Authorization": "Bearer " + os.environ["INSTAGRAM_ACCESS_TOKEN"]},
        params={"fields": "id,username,account_type"}, timeout=25)
    if resp.ok:
        return {"facebook_graph_identity_recheck_ok": True}
    error = (resp.json() or {}).get("error") or {}
    return {"facebook_graph_identity_recheck_ok": False,
            "meta_graph_http_status": resp.status_code,
            "meta_error_code": error.get("code") if
                 isinstance(error.get("code"), int) else None,
            "meta_error_subcode": error.get("error_subcode") if
                 isinstance(error.get("error_subcode"), int) else None}


def _youtube_oauth_error():
    """Return only OAuth's finite diagnostic error category; never credentials."""
    import requests
    resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data={"grant_type": "refresh_token",
              "refresh_token": os.environ["YOUTUBE_REFRESH_TOKEN"],
              "client_id": os.environ["YOUTUBE_CLIENT_ID"],
              "client_secret": os.environ["YOUTUBE_CLIENT_SECRET"]},
        timeout=25)
    if resp.ok:
        access = resp.json()["access_token"]
        check = requests.get(
            "https://www.googleapis.com/youtube/v3/channels",
            headers={"Authorization": "Bearer " + access},
            params={"part": "id", "mine": "true", "maxResults": 1},
            timeout=25)
        if check.ok:
            return {"oauth_refresh_succeeded": True,
                    "youtube_channels_read_succeeded": True}
        error = (check.json() or {}).get("error") or {}
        reasons = error.get("errors") or []
        reason = reasons[0].get("reason", "") if reasons else ""
        if reason not in ("insufficientPermissions", "accessNotConfigured",
                          "quotaExceeded", "dailyLimitExceeded",
                          "channelForbidden", "forbidden", "authError",
                          "youtubeSignupRequired", "keyInvalid"):
            reason = "OTHER_CHANNELS_API_ERROR"
        return {"oauth_refresh_succeeded": True,
                "youtube_channels_read_succeeded": False,
                "youtube_channels_http_status": check.status_code,
                "youtube_channels_api_reason": reason}
    reason = (resp.json() or {}).get("error", "")
    if reason not in ("invalid_grant", "invalid_client", "unauthorized_client",
                      "invalid_scope", "access_denied", "unsupported_grant_type"):
        reason = "OTHER_OAUTH_ERROR"
    return {"oauth_refresh_succeeded": False,
            "oauth_error_category": reason, "oauth_http_status": resp.status_code}


def audit():
    setup = token_preflight()
    result = {"mode": "READ_ONLY_NO_UPLOAD", "actual_public_uploads_tested": False,
              "accounts": {}}
    for name in TARGETS:
        item = setup[name]
        record = {
            "missing_configuration_names": item["missing_names"],
            "identity_checked": False,
            "identity_verified": False,
            "posting_permissions_verified": False,
            "public_video_uploaded": False,
        }
        identity = credential_probe(name)
        record["identity_status"] = identity["status"]
        record["identity_verified"] = identity["read_only_identity_verified"]
        record["identity_checked"] = identity["status"] != "NOT_CONFIGURED"
        if identity.get("http_status"):
            record["identity_http_status"] = identity["http_status"]
        if identity.get("missing_secret_names"):
            record["missing_secret_names"] = identity["missing_secret_names"]
        if name == "youtube" and not record["identity_verified"] and (
                os.getenv("YOUTUBE_REFRESH_TOKEN") and os.getenv("YOUTUBE_CLIENT_ID")
                and os.getenv("YOUTUBE_CLIENT_SECRET")):
            why, error = _safe_call(_youtube_oauth_error)
            if why:
                record.update(why)
            elif error:
                record["oauth_check_error"] = error
        if name == "instagram" and not record["identity_verified"] and (
                os.getenv("INSTAGRAM_ACCESS_TOKEN") and os.getenv("INSTAGRAM_ACCOUNT_ID")):
            why, error = _safe_call(_instagram_alternative)
            if why:
                record.update(why)
            elif error:
                record["instagram_login_probe_error"] = error
            fb_why, fb_error = _safe_call(_instagram_facebook_error)
            if fb_why:
                record.update(fb_why)
            elif fb_error:
                record["instagram_fb_probe_error"] = fb_error
        if record["identity_verified"]:
            if name in ("youtube", "facebook"):
                details, error = _safe_call(
                    _youtube_matches_expected if name == "youtube" else
                    _facebook_matches_expected)
                if error:
                    record["expected_account_check_error"] = error
                else:
                    record.update(details)
            elif name == "instagram":
                record["expected_account_matches"] = True  # GET matched INSTAGRAM_ACCOUNT_ID
                record["account_type"] = identity.get("account_type", "unknown")
            elif name == "tiktok":
                details, error = _safe_call(_tiktok_public_options)
                if error:
                    record["creator_info_check_error"] = error
                else:
                    record.update(details)
        if name == "facebook" and record.get("exact_page_name_matches") is True:
            record["missing_configuration_names"] = [
                x for x in record["missing_configuration_names"]
                if x != "FB_EXPECTED_PAGE_ID"]
        record["account_configuration_ready"] = (
            not record["missing_configuration_names"]
            and record["identity_verified"]
            and (name == "tiktok" or record.get("expected_account_matches") is True)
            and (name != "tiktok" or (
                record.get("creator_info_accepted") is True
                and record.get("public_option_offered") is True
                and int(record.get("max_video_post_duration_sec") or 0) >= 180))
        )
        if name == "tiktok":
            record["audit_flag_is_claim_only_not_official_approval_evidence"] = True
        result["accounts"][name] = record
    return result


def main():
    report = audit()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    summary = os.getenv("GITHUB_STEP_SUMMARY")
    lines = ["## Nightfall — read-only four-platform diagnostic", "",
             "This did not upload, publish, or create a media container.",
             "A successful identity test is NOT proof of upload permission.", ""]
    for name, item in report["accounts"].items():
        print("NIGHTFALL_PLATFORM_CHECK", name,
              "IDENTITY=" + item["identity_status"],
              "CONFIG_READY=" + str(item["account_configuration_ready"]),
              "MISSING=" + ",".join(item["missing_configuration_names"]),
              "HTTP=" + str(item.get("identity_http_status") or "none"),
              "OAUTH=" + str(item.get("oauth_error_category") or "none"),
              "IG_LOGIN=" + str(item.get("instagram_login_graph_verified", "not_checked")),
              "IG_LOGIN_HTTP=" + str(item.get("instagram_login_graph_http_status") or "none"),
              "IG_META_CODE=" + str(item.get("meta_error_code") or "none"),
              "IG_META_SUBCODE=" + str(item.get("meta_error_subcode") or "none"),
              "YT_API_REASON=" + str(item.get("youtube_channels_api_reason") or "none"),
              "FB_PAGE_NAME_MATCH=" + str(item.get("exact_page_name_matches", "not_checked")))
        lines += ["- **" + name.title() + ":** identity=" + item["identity_status"]
                  + "; configuration_ready=" + str(item["account_configuration_ready"])
                  + "; missing=" + (", ".join(item["missing_configuration_names"]) or "none")]
        if item.get("expected_account_matches") is False:
            lines.append("  - Expected destination is missing or mismatched")
        if item.get("creator_info_check_error"):
            lines.append("  - TikTok creator-info check returned a non-secret error")
        if item.get("official_error_code"):
            lines.append("  - TikTok status: " + item["official_error_code"])
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    print("PUBLIC_POSTS_CREATED false")


if __name__ == "__main__":
    main()
