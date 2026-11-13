"""Nightfall four-platform release safety / official account status.

Never equate an API token, a YouTube PRIVATE copy or TikTok INBOX draft
with an accepted PUBLIC post. No output is uploaded in 'preflight' mode.
A complete original 120-180s film, all 36 real AI clips, all 14 voices,
explicit real motion/lip-sync QA, official app and platform approvals are
mandatory before any all-platform publishing attempt.
"""
import argparse
import json
import os
from pathlib import Path

from pilot import e01_free_resume as resume
from pilot.official_platform_preflight import PLATFORMS, credential_probe
from studio.continuity import sha256
from studio.quality_gate import check_media
from studio.restore import ROOT

OUTPUT = ROOT / "output/e01_resumable/four_platform_readiness.json"
PUBLISH_SETTINGS = ROOT / "studio/production_settings.json"
CONFIG = ROOT / "config.json"
TARGETS = ("youtube", "facebook", "instagram", "tiktok")
FILM = "S01_the_last_little_fox_E01_full_unapproved.mp4"


def _safe_bool(value):
    return value is True


def film_readiness():
    """Read-only immutable checks; never assume video exists from CI success."""
    status = {
        "episode": "S01_the_last_little_fox_E01",
        "full_120_to_180_second_video_verified": False,
        "all_36_real_motion_clips": False,
        "all_14_kokoro_voices": False,
        "genuine_lipsync_approved": False,
        "cinematic_motion_approved": False,
        "all_four_platforms_verified": False,
        "can_publish_publicly": False,
    }
    try:
        _, plan = resume.film.scene_plan()
        progress = resume.load_state(plan)
        status["all_36_real_motion_clips"] = resume.next_unfinished(progress, plan) is None
        status["all_14_kokoro_voices"] = len(progress.get("voices", [])) == 14
        if progress.get("technical_full_mp4"):
            movie = resume.OUT / FILM
            if movie.is_file() and sha256(movie) == progress.get("assembled_video_sha256"):
                info = check_media(movie, mode="full")
                status["full_120_to_180_second_video_verified"] = _safe_bool(
                    info.get("technical_check_passed"))
    except (OSError, ValueError, RuntimeError, KeyError) as exc:
        status["film_error_type"] = type(exc).__name__
    settings = json.loads(PUBLISH_SETTINGS.read_text(encoding="utf-8"))
    status["genuine_lipsync_approved"] = _safe_bool(settings.get("voice_lipsync_verified"))
    status["cinematic_motion_approved"] = _safe_bool(settings.get("cinematic_video_approved"))
    return status


def account_report():
    """Actual official read-only GETs with credentials from Actions Secrets."""
    results = {}
    for name in TARGETS:
        results[name] = credential_probe(name)
        results[name]["public_release_approved"] = False
        results[name]["public_video_id_verified"] = False
        results[name]["mode_if_unapproved"] = (
            "private_review_only" if name == "youtube" else
            "unpublished_Page_video_requires_review" if name == "facebook" else
            "no_private_draft_supported_in_current_Graph_flow" if name == "instagram" else
            "inbox_draft_requires_creator_to_publish"
        )
    return results


def release_blockers(film, platforms):
    """No public upload until every prerequisite is explicitly evidenced."""
    settings = json.loads(PUBLISH_SETTINGS.read_text(encoding="utf-8"))
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    blockers = []
    for field in ("full_120_to_180_second_video_verified", "all_36_real_motion_clips",
                  "all_14_kokoro_voices", "genuine_lipsync_approved",
                  "cinematic_motion_approved"):
        if not film[field]:
            blockers.append("film:" + field)
    for key in ("production_enabled", "renderer_verified", "cinematic_video_approved",
                "voice_lipsync_verified", "youtube_verified", "facebook_verified",
                "instagram_verified", "tiktok_verified", "publishing_implemented"):
        if settings.get(key) is not True:
            blockers.append("release_approval:" + key)
    if cfg.get("public_publish_enabled") is not True:
        blockers.append("release_approval:public_publish_enabled")
    for name in TARGETS:
        if not platforms[name]["read_only_identity_verified"]:
            blockers.append("account_identity:" + name)
        if not platforms[name]["publishing_permission_verified"]:
            blockers.append("actual_publish_scope:" + name)
    # A private TikTok or INBOX transfer is NOT a public posted video. This
    # can be enabled only after TikTok's app audit plus creator-account consent.
    if os.getenv("TIKTOK_APP_AUDITED") != "true":
        blockers.append("tiktok:APP_AUDIT_NOT_VERIFIED")
    if os.getenv("TIKTOK_CREATOR_POSTING_CONSENT") != "true":
        blockers.append("tiktok:CREATOR_POSTING_CONSENT_NOT_VERIFIED")
    if os.getenv("FB_EXPECTED_PAGE_ID", "") == "":
        blockers.append("facebook:EXPECTED_PAGE_ID_NOT_CONFIGURED")
    if os.getenv("YOUTUBE_EXPECTED_CHANNEL_ID", "") == "":
        blockers.append("youtube:EXPECTED_CHANNEL_ID_NOT_CONFIGURED")
    return blockers


def report_all():
    film = film_readiness()
    accounts = account_report()
    blockers = release_blockers(film, accounts)
    return {
        "episode": film["episode"],
        "purpose": "Four official accounts and truthful whole-film release gates",
        "platform_order": list(TARGETS),
        "film": film,
        "accounts": accounts,
        "release_blockers": blockers,
        "public_release_permitted": False if blockers else True,
        "real_uploads_attempted_in_this_report": 0,
        "public_posts_created": 0,
        "private_youtube_copy_is_not_publication": True,
        "tiktok_inbox_draft_is_not_publication": True,
        "instagram_reels_is_public_upload_not_private_draft": True,
    }


def save_report(report, target=OUTPUT):
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", default=str(OUTPUT))
    args = p.parse_args()
    report = report_all()
    save_report(report, args.output)
    for name in TARGETS:
        print("OFFICIAL_DESTINATION", name, report["accounts"][name]["status"])
    print("CAN_POST_E01_PUBLICLY:", report["public_release_permitted"])
    print("RELEASE_BLOCKER_COUNT:", len(report["release_blockers"]))
    print("NO_PUBLIC_POSTS_OR_MEDIA_UPLOADS_PERFORMED")
    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write("\n## Nightfall — all four platforms readiness\n\n")
            f.write("| Platform | Official account check | Public upload test |\n")
            f.write("|---|---|---|\n")
            for name in TARGETS:
                row = report["accounts"][name]
                f.write("| " + name.title() + " | " + row["status"] +
                        " | Not performed (film/QA incomplete) |\n")
            f.write("\n- **Full film verified:** " +
                    str(report["film"]["full_120_to_180_second_video_verified"]) +
                    "\n- **Safe public release:** " + str(report["public_release_permitted"]) +
                    "\n- **Media sent:** No\n")


if __name__ == "__main__":
    main()
