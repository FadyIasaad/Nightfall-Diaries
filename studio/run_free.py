"""One online free production entrypoint; never substitutes still images for video."""
import argparse
import json
import os
from .restore import ROOT, validate_stories
from .production import SERIES
from .real_film import generate, ROOT_IMAGE
from .crosspost import receipts_read, deliver

REQUIRED_SECRETS = (
    "YOUTUBE_REFRESH_TOKEN", "YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET",
    "FB_PAGE_ACCESS_TOKEN", "INSTAGRAM_ACCESS_TOKEN", "INSTAGRAM_ACCOUNT_ID",
    "TIKTOK_ACCESS_TOKEN", "GH_TOKEN",
)

def next_to_deliver():
    for series, _ in SERIES:
        tracker = json.loads((ROOT / "seasons" / series / "episodes" / "episodes.json").read_text())
        for episode in tracker["episodes"]:
            state, _ = receipts_read(episode["id"])
            if not state.get("all_destinations_accepted"):
                return episode["id"]
    return None

def problems(upload=False):
    missing = []
    if not ROOT_IMAGE.is_file():
        missing.append("The approved Ember image is not in studio/assets/ember_approved.jpg")
    if upload:
        for key in REQUIRED_SECRETS:
            if not os.getenv(key):
                missing.append("Missing GitHub secret " + key)
    return missing

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", choices=(
        "check_setup", "free_test", "generate_only", "generate_and_upload", "scheduled"
    ), required=True)
    parser.add_argument("--episode", default="auto")
    args = parser.parse_args()
    validate_stories()
    uploading = args.action in ("generate_and_upload", "scheduled")
    print("NIGHTFALL: All original scripts valid.")
    if args.action == "check_setup":
        print("MISSING:", json.dumps(problems(upload=True)))
        print("HF Space:", os.getenv("HF_VIDEO_SPACE") or "JCisHERE/wan2-2-i2v-v3")
        print("HF auth:", "free user token present" if os.getenv("HF_TOKEN") else "unauthenticated free quota")
        print("LIVE:", os.getenv("NIGHTFALL_LIVE", "false"))
        return
    live = os.getenv("NIGHTFALL_LIVE", "").lower() == "true"
    if args.action == "scheduled" and not live:
        print("SAFE_STANDBY: 10AM Cairo automation configured; awaiting validated video and credentials.")
        return
    if uploading and not live:
        raise SystemExit("UPLOAD_NOT_ARMED: Set NIGHTFALL_LIVE=true only after testing a real MP4 and publisher permissions.")
    missing = problems(upload=uploading)
    if missing:
        raise SystemExit("SETUP_REQUIRED: " + "; ".join(missing))
    episode = "S01_the_last_little_fox_E01" if args.action == "free_test" else args.episode
    if uploading and episode == "auto":
        episode = next_to_deliver()
    if episode is None:
        print("INITIAL_SERIES_DELIVERED; next series requires owner selection.")
        return
    mode = "proof" if args.action == "free_test" else "full"
    video = generate(episode, mode=mode)
    print("REAL_MP4_PRODUCED:", video)
    if not uploading:
        print("PREVIEW_ONLY: watch video artifact; no publishing attempted.")
        return
    series, _ = episode.rsplit("_E", 1)
    tracker = json.loads((ROOT / "seasons" / series / "episodes" / "episodes.json").read_text())
    title = next(e["title"] for e in tracker["episodes"] if e["id"] == episode)
    description = f"{title} | Original Nightfall Diaries AI-animated short. #NightfallDiaries #Shorts #AIgenerated"
    state = deliver(video, episode, title, description)
    print("DELIVERY_RECEIPTS:", json.dumps(state["destinations"], sort_keys=True))
    print("TikTok inbox draft requires an in-app post; it is not public publication.")

if __name__ == "__main__":
    main()
