"""Stage E01 to the owner's authenticated YouTube channel PRIVATE only.

This is an optional, automatically executed *private review copy* after all
36 genuine shots, 14 locked Kokoro WAVs and 120-180s H.264/AAC QC succeed.
Never publishes publicly and never calls Meta/TikTok endpoints.
No duplicate automatic upload if an API call was possibly accepted.
"""
import json
import os
from pathlib import Path

from pilot import e01_free_resume as resume
from studio.continuity import sha256
from studio.quality_gate import check_media

FULL_VIDEO = "S01_the_last_little_fox_E01_full_unapproved.mp4"
UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"


def _save_progress(state):
    resume._save(state)


def _event_allowed():
    return (
        os.getenv("GITHUB_EVENT_NAME") in ("schedule", "workflow_dispatch")
        and os.getenv("GITHUB_REF") == "refs/heads/main"
        and os.getenv("GITHUB_RUN_ATTEMPT") == "1"
        and os.getenv("NIGHTFALL_PRIVATE_YOUTUBE_STAGE") == "YES"
    )


def _verify_film():
    _, plan = resume.film.scene_plan()
    state = resume.load_state(plan)
    if resume.next_unfinished(state, plan) is not None:
        raise RuntimeError("E01_INCOMPLETE_36_REAL_SHOTS")
    if not state.get("technical_full_mp4"):
        raise RuntimeError("E01_FULL_MP4_NOT_TECHNICALLY_APPROVED")
    if len(state.get("voices", [])) != 14:
        raise RuntimeError("E01_REQUIRES_ALL_FOURTEEN_REAL_KOKORO_VOICES")
    video = resume.OUT / FULL_VIDEO
    if (not video.is_file() or
            not state.get("assembled_video_sha256") or
            sha256(video) != state["assembled_video_sha256"]):
        raise RuntimeError("E01_ASSEMBLED_MP4_SHA256_MISMATCH")
    # Technical check does not assert true cinematic acting or lip sync.
    media = check_media(video, mode="full")
    if not media.get("technical_check_passed"):
        raise RuntimeError("E01_FAILED_TECHNICAL_MP4_CHECK")
    return state, video, media


def _channel_preflight():
    """Official OAuth and channel selection are read-only; no upload yet."""
    required = ("YOUTUBE_REFRESH_TOKEN", "YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET")
    if not all(os.getenv(x) for x in required):
        return None, "BLOCKED_MISSING_YOUTUBE_OAUTH"
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    creds = Credentials(
        token=None,
        refresh_token=os.environ["YOUTUBE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["YOUTUBE_CLIENT_ID"],
        client_secret=os.environ["YOUTUBE_CLIENT_SECRET"],
        scopes=[UPLOAD_SCOPE, "https://www.googleapis.com/auth/youtube.readonly"],
    )
    try:
        creds.refresh(Request())
        service = build("youtube", "v3", credentials=creds, cache_discovery=False)
        data = service.channels().list(part="id", mine=True).execute()
    except Exception as exc:
        return None, "BLOCKED_YOUTUBE_OAUTH_OR_CHANNEL_SCOPE_" + type(exc).__name__
    ids = [item.get("id") for item in (data.get("items") or []) if item.get("id")]
    expected = os.getenv("YOUTUBE_EXPECTED_CHANNEL_ID", "").strip()
    if len(ids) != 1 or (expected and ids[0] != expected):
        return None, "BLOCKED_YOUTUBE_CHANNEL_ID_MISMATCH_OR_AMBIGUITY"
    return ids[0], None


def stage_private_youtube(*, uploader=None, preflight=None):
    """One private account upload attempt, with durable ambiguous-result guard."""
    if not _event_allowed():
        raise RuntimeError("PRIVATE_YOUTUBE_STAGE_NOT_AUTHORIZED")
    state, video, media = _verify_film()
    if state.get("youtube_private_receipt"):
        return {"status": "ALREADY_UPLOADED_PRIVATE", "video_id": state["youtube_private_receipt"]["id"],
                "publicly_published": False, "duplicate_upload": False}
    if state.get("youtube_private_attempt_started"):
        return {"status": "STOP_POSSIBLE_PREVIOUS_YOUTUBE_UPLOAD_REVIEW_ACCOUNT",
                "publicly_published": False, "duplicate_upload": False}
    channel_id, problem = (preflight or _channel_preflight)()
    if problem:
        state["youtube_private_status"] = problem
        _save_progress(state)
        return {"status": problem, "publicly_published": False,
                "channel_identity_verified": False, "upload_attempted": False}
    state["youtube_verified_channel_id"] = channel_id
    state["youtube_private_status"] = "PRIVATE_UPLOAD_ATTEMPT_STARTED"
    # Save BEFORE calling YouTube: a network failure can mean the video was
    # accepted but receipt never returned. Avoid duplicate automatic posting.
    state["youtube_private_attempt_started"] = True
    _save_progress(state)
    try:
        if uploader is None:
            from studio.crosspost import publish_youtube
            uploader = publish_youtube
        os.environ["YOUTUBE_VISIBILITY"] = "private"
        upload = uploader(
            video,
            "The Last Little Fox — Episode 01 (Nightfall Diaries · PRIVATE review)",
            "Original Nightfall Diaries animated episode E01. PRIVATE technical "
            "review copy, AI generated, voice-mouth synchronization and final "
            "cinematic quality are NOT approved for public release.",
        )
        if not upload.get("id"):
            raise RuntimeError("YouTube returned no accepted video ID")
    except Exception as exc:
        state["youtube_private_status"] = ("UPLOAD_OUTCOME_UNCERTAIN_DO_NOT_AUTO_RETRY_"
                                          + type(exc).__name__)
        _save_progress(state)
        return {"status": state["youtube_private_status"],
                "upload_attempted": True, "publicly_published": False,
                "requires_review_to_avoid_duplicate": True}
    state["youtube_private_receipt"] = {
        "id": str(upload["id"]), "channel_id": channel_id,
        "visibility": "private", "film_sha256": state["assembled_video_sha256"],
    }
    state["youtube_private_status"] = "UPLOADED_PRIVATE_UNAPPROVED_NOT_PUBLIC"
    state["published_anywhere"] = False  # this field means PUBLIC publication
    _save_progress(state)
    return {"status": state["youtube_private_status"],
            "video_id": str(upload["id"]),
            "video_url": "https://www.youtube.com/watch?v=" + str(upload["id"]),
            "publicly_published": False, "channel_identity_verified": True}


def main():
    result = stage_private_youtube()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write("\n## Nightfall E01 — YouTube private review staging\n\n")
            f.write("- **Status:** " + result["status"] + "\n")
            f.write("- **Public upload:** NEVER attempted\n")
            if result.get("video_url"):
                f.write("- **Private watch link (owner only):** " +
                        result["video_url"] + "\n")


if __name__ == "__main__":
    main()
