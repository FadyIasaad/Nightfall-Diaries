"""Official-platform uploads with durable per-destination receipts.

No private tokens in source, no 'uploaded everywhere' claim for an inbox draft.
Requires valid OAuth tokens and correct API authorization from each platform.
"""
import base64
import json
import os
import subprocess
import time
from pathlib import Path
from urllib.parse import quote
import requests

REPO = "FadyIasaad/Nightfall-Diaries"
GRAPH = "https://graph.facebook.com/" + os.getenv("META_API_VERSION", "v25.0")
TIKTOK = "https://open.tiktokapis.com"
KEYS = ("youtube", "facebook", "instagram", "tiktok")

def required(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing GitHub Actions secret: {name}")
    return value

def post_json(url, **kwargs):
    resp = requests.post(url, timeout=90, **kwargs)
    resp.raise_for_status()
    data = resp.json()
    if data.get("error"):
        raise RuntimeError(f"Platform returned error: {data['error']}")
    return data

def get_json(url, **kwargs):
    r = requests.get(url, timeout=60, **kwargs)
    r.raise_for_status()
    return r.json()

def github_headers():
    return {"Authorization": "Bearer " + required("GH_TOKEN"),
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"}

def receipts_read(episode_id):
    url = f"https://api.github.com/repos/{REPO}/contents/published/{quote(episode_id)}.json"
    response = requests.get(url, headers=github_headers(), params={"ref": "main"}, timeout=40)
    if response.status_code == 404:
        return {}, None
    response.raise_for_status()
    data = response.json()
    return json.loads(base64.b64decode(data["content"])), data["sha"]

def receipt_save(episode_id, state):
    url = f"https://api.github.com/repos/{REPO}/contents/published/{quote(episode_id)}.json"
    _, sha = receipts_read(episode_id)
    content = base64.b64encode((json.dumps(state, indent=2) + "\n").encode()).decode()
    body = {"message": f"Track publishing receipt {episode_id}",
            "content": content, "branch": "main"}
    if sha: body["sha"] = sha
    r = requests.put(url, headers=github_headers(), json=body, timeout=60)
    r.raise_for_status()

def public_video_release(video, episode_id):
    """Public GitHub release hosts original MP4 for Meta's remote fetch."""
    tag = "nightfall-" + episode_id.lower().replace("_", "-")
    env = dict(os.environ, GH_TOKEN=required("GH_TOKEN"))
    subprocess.run(
        ["gh", "release", "view", tag, "--repo", REPO],
        env=env, capture_output=True, check=False
    )
    check = subprocess.run(["gh", "release", "view", tag, "--repo", REPO],
                           env=env, capture_output=True)
    if check.returncode != 0:
        subprocess.run(["gh", "release", "create", tag, str(video),
                        "--repo", REPO, "--title", f"Nightfall {episode_id}",
                        "--notes", "Original Nightfall Diaries animated episode. #AIgenerated"],
                       env=env, check=True)
    else:
        # Only upload if the filename was not already attached.
        assets = subprocess.check_output(
            ["gh", "release", "view", tag, "--json", "assets", "--repo", REPO],
            env=env, text=True)
        if Path(video).name not in [x["name"] for x in json.loads(assets)["assets"]]:
            subprocess.run(["gh", "release", "upload", tag, str(video), "--repo", REPO],
                           env=env, check=True)
    owner, repo = REPO.split("/")
    return (f"https://github.com/{owner}/{repo}/releases/download/{tag}/"
            + quote(Path(video).name))

def publish_youtube(video, title, description):
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    creds = Credentials(
        token=None, refresh_token=required("YOUTUBE_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=required("YOUTUBE_CLIENT_ID"),
        client_secret=required("YOUTUBE_CLIENT_SECRET"),
        scopes=["https://www.googleapis.com/auth/youtube.upload"]
    )
    service = build("youtube", "v3", credentials=creds, cache_discovery=False)
    req = service.videos().insert(part="snippet,status",
        body={"snippet": {"title": title[:100], "description": description,
                          "categoryId": "24"},
              "status": {"privacyStatus": os.getenv("YOUTUBE_VISIBILITY", "public"),
                         "selfDeclaredMadeForKids": False}},
        media_body=MediaFileUpload(str(video), chunksize=5*1024*1024,
                                   resumable=True, mimetype="video/mp4"))
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    if not resp or not resp.get("id"):
        raise RuntimeError("YouTube never returned video ID")
    return {"id": resp["id"], "status": "upload_accepted",
            "url": "https://www.youtube.com/watch?v=" + resp["id"]}

def publish_facebook(video, title, description):
    token = required("FB_PAGE_ACCESS_TOKEN")
    headers = {"Authorization": "Bearer " + token}
    start = post_json(GRAPH + "/me/video_reels",
                      params={"upload_phase": "start"}, headers=headers)
    video_id = start.get("video_id")
    upload_url = start.get("upload_url")
    if not video_id or not upload_url:
        raise RuntimeError("Facebook Reel upload initialization missing ID or URL")
    size = Path(video).stat().st_size
    with open(video, "rb") as f:
        response = requests.post(upload_url, data=f, timeout=300,
            headers={"Authorization": "OAuth " + token, "offset": "0",
                     "file_size": str(size), "Content-Type": "application/octet-stream"})
        response.raise_for_status()
    finish = post_json(GRAPH + "/me/video_reels", headers=headers,
        params={"upload_phase": "finish", "video_id": video_id,
                "video_state": "PUBLISHED", "title": title,
                "description": description})
    if not finish.get("success"):
        raise RuntimeError("Facebook did not accept Reel publishing request")
    return {"id": video_id, "status": "publish_processing"}

def publish_instagram(video_url, description):
    token = required("INSTAGRAM_ACCESS_TOKEN")
    ig_id = required("INSTAGRAM_ACCOUNT_ID")
    headers = {"Authorization": "Bearer " + token}
    c = post_json(GRAPH + f"/{ig_id}/media", headers=headers,
        data={"media_type": "REELS", "video_url": video_url, "caption": description,
              "share_to_feed": "false"})
    container_id = c.get("id")
    if not container_id:
        raise RuntimeError("Instagram media container missing ID")
    for _ in range(24):
        state = get_json(GRAPH + "/" + container_id,
            params={"fields": "status_code,status"}, headers=headers)
        if state.get("status_code") == "FINISHED":
            break
        if state.get("status_code") in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Instagram rejected video container: {state.get('status')}")
        time.sleep(10)
    else:
        raise RuntimeError("Instagram processing timed out; check media container before reattempt")
    posted = post_json(GRAPH + f"/{ig_id}/media_publish", headers=headers,
                       data={"creation_id": container_id})
    if not posted.get("id"):
        raise RuntimeError("Instagram publishing returned no media ID")
    return {"id": posted["id"], "status": "publish_accepted"}

def publish_tiktok(video, title):
    token = required("TIKTOK_ACCESS_TOKEN")
    size = Path(video).stat().st_size
    if size <= 0 or size > 64*1024*1024:
        raise RuntimeError("TikTok single-chunk upload requires video <=64 MB")
    # Inbox is the documented fallback when direct public posting is unauthorized.
    mode = os.getenv("TIKTOK_POST_MODE", "inbox")
    direct = mode == "direct"
    url = (TIKTOK + "/v2/post/publish/video/init/" if direct else
           TIKTOK + "/v2/post/publish/inbox/video/init/")
    body = {"source_info": {"source": "FILE_UPLOAD", "video_size": size,
                            "chunk_size": size, "total_chunk_count": 1}}
    if direct:
        body["post_info"] = {
            "title": title[:150], "privacy_level": os.getenv("TIKTOK_PRIVACY", "SELF_ONLY"),
            "disable_duet": False, "disable_comment": False,
            "disable_stitch": False, "is_aigc": True
        }
    data = post_json(url, json=body,
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"})
    if data.get("error", {}).get("code") != "ok":
        raise RuntimeError("TikTok rejected upload: " + str(data.get("error", {})))
    info = data.get("data", {})
    if not info.get("upload_url") or not info.get("publish_id"):
        raise RuntimeError("TikTok upload session missing URL or publish ID")
    with open(video, "rb") as f:
        response = requests.put(info["upload_url"], data=f, timeout=300,
            headers={"Content-Type": "video/mp4",
                     "Content-Range": f"bytes 0-{size-1}/{size}"})
        response.raise_for_status()
    return {"id": info["publish_id"],
            "status": "publish_processing" if direct else "inbox_draft_requires_user_post"}

def deliver(video, episode_id, title, description):
    """Track receipts immediately after each accepted upload to limit duplicates."""
    state, _sha = receipts_read(episode_id)
    state.setdefault("episode_id", episode_id)
    state.setdefault("destinations", {})
    destinations = state["destinations"]
    video_url = None
    tasks = [
        ("youtube", lambda: publish_youtube(video, title, description)),
        ("facebook", lambda: publish_facebook(video, title, description)),
        ("instagram", lambda: publish_instagram(video_url, description)),
        ("tiktok", lambda: publish_tiktok(video, title))
    ]
    problems = []
    for name, perform in tasks:
        if destinations.get(name, {}).get("id"):
            print(f"SKIP_{name.upper()}: earlier accepted upload receipt exists")
            continue
        try:
            if name == "instagram" and video_url is None:
                video_url = public_video_release(video, episode_id)
            result = perform()
            destinations[name] = result
            receipt_save(episode_id, state)
            print(f"{name.upper()}_UPLOAD_ACCEPTED: {result['status']}")
        except Exception as exc:
            problems.append(f"{name}: {type(exc).__name__}: {str(exc)[:250]}")
            print("PLATFORM_BLOCKED:", problems[-1])
    state["all_destinations_accepted"] = all(
        destinations.get(name, {}).get("id") for name in KEYS)
    if state["all_destinations_accepted"]:
        receipt_save(episode_id, state)
    if problems:
        raise RuntimeError("; ".join(problems))
    return state
