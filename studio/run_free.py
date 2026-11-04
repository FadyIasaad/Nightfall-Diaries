"""Single cloud entrypoint. Read-only checks never import optional video/TTS libraries."""
import argparse
import json
import os
import re
from pathlib import Path

from .restore import ROOT, validate_stories
from .production import SERIES
from .screenplay import load_screenplay

SETTINGS = ROOT / "studio" / "production_settings.json"
CONFIG = ROOT / "config.json"
EMBER_REFERENCE = ROOT / "seasons/S01_the_last_little_fox/characters/s01_ember/cloud_reference.png"
REQUIRED_SECRETS = (
    "YOUTUBE_REFRESH_TOKEN", "YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET",
    "FB_PAGE_ACCESS_TOKEN", "INSTAGRAM_ACCESS_TOKEN", "INSTAGRAM_ACCOUNT_ID",
    "TIKTOK_ACCESS_TOKEN", "GH_TOKEN",
)
REQUIRED_APPROVALS = (
    "production_enabled", "renderer_verified", "cinematic_video_approved",
    "voice_lipsync_verified", "youtube_verified", "facebook_verified",
    "instagram_verified", "tiktok_verified", "publishing_implemented",
)

def selected_episode(requested):
    if requested != "auto":
        if not re.fullmatch(r"S0[12]_[a-z_]+_E\d{2}", requested):
            raise ValueError("Invalid episode ID")
        series, num = requested.rsplit("_E", 1)
        if series not in dict(SERIES) or int(num) not in range(1, dict(SERIES)[series] + 1):
            raise ValueError("Episode not in the approved original archive")
        return requested
    # A persistent upload receipt is authoritative, not an optimistic queue index.
    from .crosspost import receipts_read
    for series, _count in SERIES:
        tracker = json.loads((ROOT / "seasons" / series / "episodes/episodes.json").read_text())
        for episode in tracker["episodes"]:
            receipt, _sha = receipts_read(episode["id"])
            if not receipt.get("all_destinations_public", False):
                return episode["id"]
    return None

def screenplay_word_count(episode_id):
    data = load_screenplay(episode_id)
    return sum(len(scene["text"].split()) for scene in data["scenes"])

def publish_blockers():
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    issues = []
    if os.getenv("NIGHTFALL_LIVE", "").lower() != "true":
        issues.append("NIGHTFALL_LIVE must be true after proof and account verification")
    issues += ["Unverified production gate: " + name for name in REQUIRED_APPROVALS
               if settings.get(name) is not True]
    if config.get("public_publish_enabled") is not True:
        issues.append("config.json public_publish_enabled is false")
    issues += ["Missing secret: " + name for name in REQUIRED_SECRETS if not os.getenv(name)]
    return issues

def setup_report():
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    first = "S01_the_last_little_fox_E01"
    wc = screenplay_word_count(first)
    return {
        "status": "BLOCKED_UNTIL_PROVEN",
        "time": "10:00 Africa/Cairo",
        "original_scripts": validate_stories(),
        "existing_ember_reference": EMBER_REFERENCE.is_file(),
        "reference_is_approved_motion": False,
        "episode_one_original_script_words": wc,
        "episode_one_full_screenplay_ready": 240 <= wc <= 430,
        "max_episode_seconds": 180,
        "manual_same_day_episodes": True,
        "video_provider_configured": True,
        "candidate_free_video_space": "zerogpu-aoti/wan2-2-fp8da-aoti-faster",
        "video_provider_verified": bool(settings.get("renderer_verified")),
        "live_variable": os.getenv("NIGHTFALL_LIVE", "").lower() == "true",
        "publication_blockers": publish_blockers(),
        "notes": [
            "An approved still image is not a verified moving animation.",
            "No under-three-minute episode or lip-synced character action has passed visual review.",
            "Missing account authorizations and publishing proof must not be bypassed.",
            "Tests and this report never upload or render media.",
        ],
    }

def report_setup():
    report = setup_report()
    out = ROOT / "output" / "nightfall_setup_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("NIGHTFALL_SETUP_REPORT:", str(out))
    print("ORIGINAL_SCRIPTS:", report["original_scripts"])
    print("EMBER_REFERENCE_PRESENT:", report["existing_ember_reference"])
    print("E01_WORDS:", report["episode_one_original_script_words"])
    print("PUBLIC_PUBLISHING: BLOCKED until all proof and publisher gates pass")
    for issue in report["publication_blockers"]:
        print("BLOCKER:", issue)
    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write("## Nightfall cloud preflight\n\n")
            f.write(f"- Original story files validated: {report['original_scripts']}\n")
            f.write(f"- Tracked Ember reference: {report['existing_ember_reference']}\n")
            f.write(f"- E01 archived script words: {report['episode_one_original_script_words']}\n")
            f.write(f"- Full-screenplay gate: {report['episode_one_full_screenplay_ready']}\n")
            f.write(f"- Public publishing: BLOCKED pending verified approvals\n\n")
    return report

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", choices=(
        "check_setup", "free_test", "render_quality_proof", "generate_only",
        "generate_full_episode", "generate_another_episode", "generate_and_upload", "retry_missing_platforms",
        "scheduled", "resume_pending"
    ), required=True)
    parser.add_argument("--episode", default="auto")
    args = parser.parse_args()
    validate_stories()

    if args.action == "check_setup":
        report_setup()
        return

    if args.action == "scheduled" and os.getenv("NIGHTFALL_LIVE", "").lower() != "true":
        print("SAFE_STANDBY: 10 AM Cairo check; no video produced or published.")
        report_setup()
        return

    if args.action == "retry_missing_platforms":
        raise SystemExit("RETRY_NOT_READY: durable MP4 recovery and per-platform public-status reconciliation are not implemented; refusing to duplicate posts.")

    uploading = args.action in ("generate_and_upload", "scheduled")
    if uploading:
        issues = publish_blockers()
        if issues:
            raise SystemExit("PUBLISH_BLOCKED: " + "; ".join(issues))

    if args.action == "generate_another_episode" and args.episode == "auto":
        raise SystemExit("EPISODE_REQUIRED: select an explicit original episode, e.g. S01_the_last_little_fox_E02")
    from .pending import enqueue, next_due, set_status, write_report
    pending_item = next_due() if args.action == "resume_pending" else None
    if args.action == "resume_pending" and pending_item is None:
        print("NO_PENDING_RENDER_DUE: no queued episode eligible for retry; no GPU or upload")
        return
    proof = (pending_item["mode"] == "proof" if pending_item else
             args.action in ("free_test", "render_quality_proof"))
    episode = (pending_item["episode_id"] if pending_item else
               "S01_the_last_little_fox_E01" if proof else selected_episode(args.episode))
    if episode is None:
        print("ORIGINAL_SERIES_COMPLETE: no new series starts before a quality-locked canon exists.")
        return
    if not EMBER_REFERENCE.is_file():
        raise SystemExit("RENDER_BLOCKED: tracked Ember reference missing")
    from .continuity import locked_cast
    season_id, _ = episode.rsplit("_E",1)
    locked_cast(season_id)
    mode = "proof" if proof else "full"
    if args.action != "resume_pending" and not uploading:
        enqueue(episode, mode)
    from .motion_provider import probe
    provider = probe()
    provider_path = ROOT / "output" / "motion_provider_report.json"
    provider_path.parent.mkdir(parents=True, exist_ok=True)
    provider_path.write_text(json.dumps(provider, indent=2) + "\n", encoding="utf-8")
    print("MOTION_PROVIDER_CHECK:", json.dumps(provider, sort_keys=True))
    if provider["state"] != "READY_FOR_ONE_QUOTA_LIMITED_TEST":
        note = "Free provider not ready: " + provider["notes"]
        if not uploading:
            state = set_status(episode, mode, "PAUSED_PROVIDER",
                               retry_seconds=21600, details=note)
            write_report(episode, mode, state["status"], note,
                         state["retry_after_utc"])
            print("NOT_RENDERED_PROVIDER_PAUSED:", note)
            return
        raise SystemExit("RENDER_BLOCKED: " + note)

    if not proof and screenplay_word_count(episode) < 240:
        raise SystemExit(f"SCREENPLAY_TOO_SHORT: {episode} has fewer than 240 dialogue/narration words. Prepare an under-three-minute screenplay BEFORE using any free GPU quota.")

    # Heavy dependencies are intentionally loaded only in a real render job.
    from .real_film import generate
    from .free_video import QuotaExhausted, VideoUnavailable
    try:
        video = generate(episode, mode=mode)
    except QuotaExhausted as exc:
        state = set_status(episode, mode, "PAUSED_FREE_QUOTA",
                           retry_seconds=exc.retry_seconds, details=str(exc))
        write_report(episode, mode, state["status"], str(exc),
                     state["retry_after_utc"])
        print("NOT_COMPLETE_QUOTA_PAUSE:", episode, state["retry_after_utc"])
        return
    except VideoUnavailable as exc:
        state = set_status(episode, mode, "PAUSED_PROVIDER",
                           retry_seconds=21600, details=str(exc))
        write_report(episode, mode, state["status"], str(exc),
                     state["retry_after_utc"])
        print("NOT_COMPLETE_PROVIDER_PAUSE:", episode)
        return
    from .quality_gate import check_media
    metrics = check_media(video, mode=mode)
    print("REAL_MOTION_CANDIDATE:", str(video))
    print("TECHNICAL_QA:", json.dumps(metrics, sort_keys=True))
    if not uploading:
        state=set_status(episode, mode, "RENDERED_NOT_VISUALLY_APPROVED",
                         details="Technical MP4 check passed; acting, identity, lip sync and public publishing remain unverified")
        write_report(episode, mode, state["status"], state["last_note"])

        print("REVIEW_ONLY: no public publishing attempted; cinematic acting and lip sync remain unverified.")
        return

    # Technical validation cannot establish cinematic visuals or lip sync; the
    # independent approval gates above must remain false until real review.
    from .crosspost import deliver
    series, _ = episode.rsplit("_E", 1)
    tracker = json.loads((ROOT / "seasons" / series / "episodes/episodes.json").read_text())
    title = next(x["title"] for x in tracker["episodes"] if x["id"] == episode)
    description = f"{title} | Original Nightfall Diaries animated drama. AI-assisted creation."
    outcome = deliver(video, episode, title, description)
    print("PLATFORM_UPLOAD_STATUS:", json.dumps(outcome.get("destinations", {}), sort_keys=True))
    if not outcome.get("all_destinations_public"):
        print("NOT_COMPLETE: API upload tickets or private drafts do not prove public posting.")

if __name__ == "__main__":
    main()
