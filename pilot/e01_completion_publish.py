"""Immediate event-driven E01 cross-platform release after real final-film approval.

The release step runs in the SAME workflow run as 36/36 scene assembly,
NOT on a fixed publication schedule. If any safety/account prerequisite is
missing, report the named blocker and do not post partial or unapproved clips.

No paid APIs, no user-PC dependency, and NO unapproved publishing.
One durable remote receipt per platform is written BEFORE any network upload.
Ambiguous send failures never auto-retry (could duplicate a public post).
"""
import argparse
import json
import os
from pathlib import Path

from pilot import e01_free_resume as resume
from pilot import e01_private_youtube as youtube_preview
from pilot.official_platform_preflight import credential_probe
from studio.continuity import sha256
from studio.quality_gate import check_media
from studio.restore import ROOT

EPISODE = "S01_the_last_little_fox_E01"
TARGETS = ("youtube", "facebook", "instagram", "tiktok")
SETTINGS = ROOT / "studio/production_settings.json"
CONFIG = ROOT / "config.json"
OUT = resume.OUT / "four_platform_completion_status.json"
MOVIE = resume.OUT / youtube_preview.FULL_VIDEO


def _flags():
    return json.loads(SETTINGS.read_text()), json.loads(CONFIG.read_text())


def film_gate():
    """Exact real MP4 + quality evidence; no slideshow/approval shortcuts."""
    result = {
        "episode": EPISODE, "film_ready_for_public": False,
        "shots_verified": 0, "kokoro_voices_verified": 0,
        "technical_mp4_passed": False, "real_lipsync_approved": False,
        "cinematic_motion_approved": False, "blockers": [],
    }
    _, plan = resume.film.scene_plan()
    state = resume.load_state(plan)  # authentic MP4 and WAV SHA-256 checks
    result["shots_verified"] = len(state["completed"])
    result["kokoro_voices_verified"] = len(state.get("voices", []))
    if resume.next_unfinished(state, plan) is not None:
        result["blockers"].append("FILM_NOT_36_OF_36_GENUINE_SHOTS")
    if len(state.get("voices", [])) != 14:
        result["blockers"].append("FILM_NOT_14_KOKORO_VOICES")
    if not state.get("technical_full_mp4") or not MOVIE.is_file():
        result["blockers"].append("FILM_MP4_NOT_ASSEMBLED")
    elif state.get("assembled_video_sha256") != sha256(MOVIE):
        result["blockers"].append("FILM_MP4_SHA256_MISMATCH")
    else:
        media = check_media(MOVIE, mode="full")
        result["technical_mp4_passed"] = media["technical_check_passed"]
        result["duration_seconds"] = media["duration_seconds"]
    settings, cfg = _flags()
    result["owner_auto_public_release_authorized"] = (
        settings.get("owner_auto_public_release_authorized") is True
        and settings.get("owner_approval_per_episode_required") is False
    )
    if not result["owner_auto_public_release_authorized"]:
        result["blockers"].append("OWNER_AUTO_RELEASE_NOT_AUTHORIZED")
    result["real_lipsync_approved"] = (
        state.get("true_lipsync_verified") is True
        and settings.get("voice_lipsync_verified") is True)
    result["cinematic_motion_approved"] = (
        state.get("human_cinematic_approved") is True
        and settings.get("cinematic_video_approved") is True
        and settings.get("renderer_verified") is True)
    if not result["real_lipsync_approved"]:
        result["blockers"].append("REAL_CHARACTER_LIPSYNC_NOT_APPROVED")
    if not result["cinematic_motion_approved"]:
        result["blockers"].append("REAL_CINEMATIC_ACTING_NOT_APPROVED")
    for setting in ("production_enabled", "publishing_implemented",
                    "youtube_verified", "facebook_verified",
                    "instagram_verified", "tiktok_verified"):
        if settings.get(setting) is not True:
            result["blockers"].append("UNVERIFIED_RELEASE_FLAG_" + setting)
    if cfg.get("public_publish_enabled") is not True:
        result["blockers"].append("PUBLIC_RELEASE_NOT_ENABLED")
    result["film_ready_for_public"] = not result["blockers"]
    return result


def token_preflight():
    names = {
        "youtube": ("YOUTUBE_REFRESH_TOKEN", "YOUTUBE_CLIENT_ID",
                    "YOUTUBE_CLIENT_SECRET", "YOUTUBE_EXPECTED_CHANNEL_ID"),
        "facebook": ("FB_PAGE_ACCESS_TOKEN", "FB_EXPECTED_PAGE_ID"),
        "instagram": ("INSTAGRAM_ACCESS_TOKEN", "INSTAGRAM_ACCOUNT_ID"),
        "tiktok": ("TIKTOK_ACCESS_TOKEN",),
    }
    out = {}
    for platform in TARGETS:
        missing = [name for name in names[platform] if not os.getenv(name)]
        out[platform] = {
            "credentials_configured": not missing,
            "missing_names": missing,
            "official_identity_verified": False,
            "permission_to_publicly_publish_tested": False,
            "public_post_created": False,
        }
    if os.getenv("TIKTOK_APP_AUDITED") != "true":
        out["tiktok"]["missing_names"].append("TIKTOK_APP_AUDITED")
        out["tiktok"]["credentials_configured"] = False
    if os.getenv("TIKTOK_CREATOR_POSTING_CONSENT") != "true":
        out["tiktok"]["missing_names"].append("TIKTOK_CREATOR_POSTING_CONSENT")
        out["tiktok"]["credentials_configured"] = False
    return out


def _read_only_platform_probe(report):
    """Do not turn a successful identity GET into a claim of publish permission."""
    for name in TARGETS:
        if report[name]["credentials_configured"]:
            verified = credential_probe(name)
            report[name]["official_identity_verified"] = (
                verified.get("read_only_identity_verified") is True)
            report[name]["identity_status"] = verified.get("status")
    return report


def _youtube_public(video, title, description, state):
    # Prior private review copy must be promoted, not re-uploaded as a duplicate.
    channel, problem = youtube_preview._channel_preflight()
    if problem or channel != os.environ["YOUTUBE_EXPECTED_CHANNEL_ID"]:
        raise RuntimeError("YouTube channel identity or OAuth scope not verified")
    private = state.get("youtube_private_receipt")
    # A prior private upload can have reached YouTube without returning an ID.
    # In that case a second public upload might create a duplicate. Stop.
    if state.get("youtube_private_attempt_started") and not private:
        raise RuntimeError("Uncertain prior YouTube private upload: no duplicate")
    if private:
        if private.get("channel_id") != channel:
            raise RuntimeError("Private video was uploaded to a different channel")
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        creds = Credentials(
            token=None, refresh_token=os.environ["YOUTUBE_REFRESH_TOKEN"],
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.environ["YOUTUBE_CLIENT_ID"],
            client_secret=os.environ["YOUTUBE_CLIENT_SECRET"],
            scopes=["https://www.googleapis.com/auth/youtube"],
        )
        creds.refresh(Request())
        client = build("youtube", "v3", credentials=creds, cache_discovery=False)
        updated = client.videos().update(
            part="status",
            body={"id": private["id"],
                  "status": {"privacyStatus": "public",
                             "selfDeclaredMadeForKids": False}}
        ).execute()
        if updated.get("id") != private["id"]:
            raise RuntimeError("YouTube did not return the existing video ID")
        return {"id": updated["id"], "status": "public_status_requested"}
    os.environ["YOUTUBE_VISIBILITY"] = "public"
    from studio import crosspost
    return crosspost.publish_youtube(video, title, description)


def _facebook_full_page_video(video, title, description):
    """150s film goes to Page Videos, not the shorter Reel upload path."""
    import requests
    version = os.getenv("META_API_VERSION", "v25.0")
    page_id = os.environ["FB_EXPECTED_PAGE_ID"]
    token = os.environ["FB_PAGE_ACCESS_TOKEN"]
    base = "https://graph.facebook.com/" + version
    who = requests.get(
        base + "/me", params={"fields": "id", "access_token": token},
        timeout=30)
    who.raise_for_status()
    if str(who.json().get("id")) != page_id:
        raise RuntimeError("Facebook Page token did not match requested Page")
    url = "https://graph-video.facebook.com/" + version + "/" + page_id + "/videos"
    with open(video, "rb") as media:
        result = requests.post(
            url,
            headers={"Authorization": "Bearer " + token},
            data={"title": title[:255], "description": description,
                  "published": "true"},
            files={"source": (Path(video).name, media, "video/mp4")},
            timeout=600)
    result.raise_for_status()
    obj = result.json()
    if not obj.get("id"):
        raise RuntimeError("Facebook Page Video API did not accept the full video")
    return {"id": obj["id"], "status": "page_video_accepted_processing"}


def _instagram_reel(video, title, description):
    """The official Graph API reads public HTTPS video_url, not local bytes."""
    from studio import crosspost
    hosted_url = crosspost.public_video_release(video, EPISODE)
    return crosspost.publish_instagram(hosted_url, description)


def _tiktok_direct(video, title, description, duration):
    import requests
    token = os.environ["TIKTOK_ACCESS_TOKEN"]
    # Direct Post requires creator info and current creator-approved privacy options.
    response = requests.post(
        "https://open.tiktokapis.com/v2/post/publish/creator_info/query/",
        headers={"Authorization": "Bearer " + token,
                 "Content-Type": "application/json"},
        json={}, timeout=30)
    response.raise_for_status()
    obj = response.json()
    if (obj.get("error") or {}).get("code") != "ok":
        raise RuntimeError("TikTok creator info authorization not approved")
    data = obj.get("data") or {}
    choices = data.get("privacy_level_options") or []
    maximum = int(data.get("max_video_post_duration_sec") or 0)
    if "PUBLIC_TO_EVERYONE" not in choices or duration > maximum:
        raise RuntimeError("TikTok creator's public privacy or duration is not allowed")
    os.environ["TIKTOK_POST_MODE"] = "direct"
    os.environ["TIKTOK_PRIVACY"] = "PUBLIC_TO_EVERYONE"
    from studio import crosspost
    return crosspost.publish_tiktok(video, title)


def _save(receipts):
    """Remote main branch is durable across GitHub runner/cache eviction."""
    from studio import crosspost
    crosspost.receipt_save(EPISODE, receipts)


def _read_receipts(episode):
    from studio import crosspost
    return crosspost.receipts_read(episode)


def release_once(*, adapters=None, receipt_read=None, receipt_write=None):
    """No schedule filter: immediately called on film completion in same job."""
    result = {
        "episode": EPISODE, "mode": "ON_FILM_COMPLETION_NO_PUBLICATION_TIMER",
        "public_posts_verified": 0, "requests_submitted": 0,
        "platforms": token_preflight(), "status": "NOT_READY",
    }
    if (os.getenv("GITHUB_REF") != "refs/heads/main" or
        os.getenv("GITHUB_EVENT_NAME") not in ("workflow_dispatch", "schedule") or
        os.getenv("GITHUB_RUN_ATTEMPT") != "1"):
        result["status"] = "BLOCKED_NOT_AUTHORIZED_MAIN_WORKFLOW"
        return result
    film = film_gate()
    result["film"] = film
    if not film["film_ready_for_public"]:
        result["status"] = "WAITING_REAL_FILM_AND_LIPSYNC_APPROVAL"
        return result
    _read_only_platform_probe(result["platforms"])
    eligible = tuple(name for name in TARGETS
                     if result["platforms"][name]["credentials_configured"]
                     and result["platforms"][name]["official_identity_verified"])
    # One unavailable destination must NOT block unrelated authorized ones.
    # Failed/missing platforms remain explicit, and the Telegram four-platform
    # success message is withheld until all FOUR are officially public.
    for name in TARGETS:
        if not result["platforms"][name]["credentials_configured"]:
            result["platforms"][name]["status"] = "BLOCKED_MISSING_CREDENTIALS_OR_APP_APPROVAL"
        elif not result["platforms"][name]["official_identity_verified"]:
            result["platforms"][name]["status"] = "BLOCKED_OFFICIAL_ACCOUNT_AUTH"
    if not eligible:
        result["status"] = "BLOCKED_NO_AUTHORIZED_DESTINATIONS"
        return result
    read = receipt_read or _read_receipts
    write = receipt_write or _save
    try:
        receipts, _etag = read(EPISODE)
    except Exception as exc:
        result["status"] = "BLOCKED_DURABLE_RECEIPT_READ_" + type(exc).__name__
        return result
    receipts.setdefault("episode_id", EPISODE)
    receipts.setdefault("destinations", {})
    receipts["film_sha256"] = sha256(MOVIE)
    descriptions = {
        "youtube": "Original Nightfall Diaries — The Last Little Fox, Episode 01. #AIanimation",
        "facebook": "Original animated story Nightfall Diaries — The Last Little Fox E01.",
        "instagram": "Nightfall Diaries | The Last Little Fox E01 #AIanimation",
        "tiktok": "Nightfall Diaries | The Last Little Fox E01 #AIanimation",
    }
    title = "Nightfall Diaries — The Last Little Fox | Episode 01"
    # Inspect verified private YouTube receipts to reuse an existing private copy.
    progress = resume.load_state(resume.film.scene_plan()[1])
    routes = adapters or {
        "youtube": lambda: _youtube_public(MOVIE, title, descriptions["youtube"], progress),
        "facebook": lambda: _facebook_full_page_video(MOVIE, title, descriptions["facebook"]),
        "instagram": lambda: _instagram_reel(MOVIE, title, descriptions["instagram"]),
        "tiktok": lambda: _tiktok_direct(MOVIE, title, descriptions["tiktok"],
                                       film["duration_seconds"]),
    }
    for name in TARGETS:
        if name not in eligible:
            # Do not write a media-upload receipt for a platform that was
            # never authenticated and to which no network upload was sent.
            continue
        previous = receipts["destinations"].get(name, {})
        if previous.get("phase") in ("initiated", "accepted", "confirmed_public", "ambiguous"):
            result["platforms"][name]["status"] = "NO_DUPLICATE_" + previous["phase"].upper()
            continue
        receipts["destinations"][name] = {
            "phase": "initiated", "film_sha256": receipts["film_sha256"],
            "public_confirmed": False,
        }
        try:
            # Durable remote record must be accepted BEFORE opening media session.
            write(receipts)
        except Exception as exc:
            result["platforms"][name]["status"] = (
                "RECEIPT_WRITE_FAILED_NO_UPLOAD_" + type(exc).__name__)
            continue
        try:
            posted = routes[name]()
            if not posted.get("id"):
                raise RuntimeError("Official destination returned no upload ID")
            receipts["destinations"][name].update({
                "phase": "accepted", "id": str(posted["id"]),
                "platform_status": str(posted.get("status", "processing")),
                "public_confirmed": False,
            })
            result["requests_submitted"] += 1
            result["platforms"][name]["status"] = "ACCEPTED_PROCESSING_NOT_VERIFIED_PUBLIC"
        except Exception as exc:
            receipts["destinations"][name].update({
                "phase": "ambiguous", "failure_type": type(exc).__name__,
                "public_confirmed": False,
            })
            result["platforms"][name]["status"] = (
                "MAY_HAVE_UPLOADED_REVIEW_ACCOUNT_BEFORE_RETRY")
        finally:
            try:
                write(receipts)
            except Exception:
                result["platforms"][name]["status"] = "DURABLE_RECEIPT_UPDATE_FAILED_REVIEW"
    result["status"] = (
        "UPLOAD_REQUESTS_SENT_PROCESSING_NOT_PUBLICATION_CONFIRMED"
        if result["requests_submitted"] else
        "ALL_PLATFORMS_BLOCKED_OR_ALREADY_ATTEMPTED"
    )
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("on-completion",), default="on-completion")
    args = parser.parse_args()
    report = release_once()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print("E01_CROSS_PLATFORM_RESULT", report["status"])
    print("UPLOAD_REQUESTS_SUBMITTED", report["requests_submitted"])
    for name, item in report["platforms"].items():
        print("DESTINATION", name, item.get("status", "UNVERIFIED"))
    print("PUBLIC_POSTS_CONFIRMED", report["public_posts_verified"])
    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write("\n## E01 immediate four-platform completion delivery\n\n")
            f.write("- **Execution:** immediately after full assembly; no release clock\n")
            f.write("- **Status:** " + report["status"] + "\n")
            f.write("- **Public posts confirmed:** 0 unless verified separately\n")
            for name, item in report["platforms"].items():
                f.write("- **" + name.title() + ":** " +
                        item.get("status", "not attempted") + "\n")


if __name__ == "__main__":
    main()
