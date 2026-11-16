"""One-time user-authorized E01 painterly release; exact film, exact destinations.

Publishes only to the uniquely verified 'Nightfall Diaries' Facebook Page and
the exact authorized Instagram business account. YouTube/TikTok are explicitly
blocked until account ID / creator consent can be verified.

GitHub receipts are committed BEFORE each remote POST to prevent duplicates.
Never auto-retry an uncertain POST, never expose tokens, never claim public
visibility just because the upload API accepted a video.
"""
import base64
import json
import os
from pathlib import Path
import time

import requests

from pilot.facebook_page_auth import resolve_nightfall_page
from pilot.official_platform_preflight import credential_probe

REPO = "FadyIasaad/Nightfall-Diaries"
SRC_SHA = "6a41bf8978e84c3df1c76b355b8b92e32796836ade92dc24e484d86b2472c1da"
RECEIPT_PATH = "published/S01_the_last_little_fox_E01_painterly_v2.json"
FILM = Path("output/painterly_release/Nightfall_S01_E01_Painterly_2p5D_216s_PUBLIC.mp4")
TAG = "nightfall-e01-painterly-2p5d-20261116"
RELEASE_URL = (
    "https://github.com/" + REPO + "/releases/download/" + TAG + "/" + FILM.name
)
GH_API = "https://api.github.com/repos/" + REPO + "/contents/" + RECEIPT_PATH
GRAPH = "https://graph.facebook.com/v25.0"
GRAPH_VIDEO = "https://graph-video.facebook.com/v25.0"
TITLE = "The Last Little Fox | Episode 01 — The Night the Forest Burned"
DESCRIPTION = (
    "The Last Little Fox — Episode 01: The Night the Forest Burned. "
    "An original Nightfall Diaries illustrated 2.5D animated drama with "
    "Ember and Moss. Voice performances by Kokoro. "
    "Art direction: painterly cutout animation. #NightfallDiaries #AnimatedStory "
    "#TheLastLittleFox #2DAnimation"
)


def headers():
    token = os.getenv("GH_TOKEN", "")
    if not token:
        raise RuntimeError("GITHUB_WRITE_TOKEN_NOT_AVAILABLE")
    return {
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def read_receipt():
    response = requests.get(GH_API, headers=headers(), timeout=30)
    if response.status_code == 404:
        return {
            "schema": 1, "film_source_sha256": SRC_SHA,
            "format": "illustrated_2_5d_not_cinematic_3d",
            "public_upload_requested_by_owner": True,
            "facebook": {"phase": "not_attempted"},
            "instagram": {"phase": "not_attempted"},
            "youtube": {"phase": "blocked_expected_channel_unverified"},
            "tiktok": {"phase": "blocked_no_api_token_or_creator_consent"},
        }, None
    response.raise_for_status()
    payload = response.json()
    doc = json.loads(base64.b64decode(payload["content"]).decode("utf-8"))
    if doc.get("film_source_sha256") != SRC_SHA:
        raise RuntimeError("WRONG_FILM_RECEIPT_MUST_NOT_OVERWRITE")
    return doc, payload["sha"]


def save_receipt(report, previous):
    # Every receipt write is a fresh GitHub commit; this is the durable lock.
    body = {
        "message": "Nightfall E01 exact-video upload receipt: no duplicate remote posts",
        "content": base64.b64encode(
            (json.dumps(report, indent=2, ensure_ascii=False) + "\n").encode()
        ).decode("ascii"),
        "branch": "main",
    }
    if previous:
        body["sha"] = previous
    response = requests.put(GH_API, headers=headers(), json=body, timeout=45)
    response.raise_for_status()
    return response.json()["content"]["sha"]


def clean_error(exc):
    # Never output raw API URLs, headers, token values, Facebook or IG body.
    response = getattr(exc, "response", None)
    code = getattr(response, "status_code", None)
    return {"failure_type": type(exc).__name__, "http_status": code}


def verified_source():
    import hashlib
    import subprocess
    if not FILM.is_file() or FILM.stat().st_size < 10_000:
        raise RuntimeError("RELEASED_MP4_NOT_FOUND")
    data = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate",
         "-of", "json", str(FILM)],
        check=True, capture_output=True, text=True, timeout=30,
    )
    media = json.loads(data.stdout)
    seconds = float(media["format"]["duration"])
    video = next((s for s in media["streams"] if s["codec_type"] == "video"), {})
    audio = next((s for s in media["streams"] if s["codec_type"] == "audio"), {})
    fps_n, fps_d = (int(x) for x in video["r_frame_rate"].split("/"))
    fps = fps_n/fps_d
    if (not 180 <= seconds <= 360 or video.get("codec_name") != "h264"
        or audio.get("codec_name") != "aac"
        or int(video.get("width") or 0) != 720
        or int(video.get("height") or 0) != 1280
        or not 23 <= fps <= 60):
        raise RuntimeError("RELEASE_MP4_NOT_IG_META_COMPATIBLE")
    src_path = Path("output/painterly_release/original_original_approved_E01.mp4")
    if not src_path.is_file():
        raise RuntimeError("ORIGINAL_SOURCE_NOT_RESTORED")
    digest = hashlib.sha256(src_path.read_bytes()).hexdigest()
    if digest != SRC_SHA:
        raise RuntimeError("ORIGINAL_PAINTED_E01_SHA_MISMATCH")
    return {"duration": round(seconds,2), "width":720,"height":1280, "fps":fps}


def check_public_github_asset():
    # HEAD can be rate limited on github.com; use GET stream and verify a
    # genuine media response (not GitHub HTML login or not found).
    response = requests.get(RELEASE_URL, allow_redirects=True, stream=True, timeout=35)
    try:
        if not response.ok or response.headers.get("Content-Type", "").startswith("text/html"):
            raise RuntimeError("PUBLIC_GITHUB_RELEASE_VIDEO_NOT_REACHABLE_FOR_INSTAGRAM")
    finally:
        response.close()


def upload_fb(page):
    with FILM.open("rb") as stream:
        resp = requests.post(
            GRAPH_VIDEO + "/" + page["id"] + "/videos",
            headers={"Authorization": "Bearer " + page["access_token"]},
            data={"title":TITLE,"description":DESCRIPTION,"published":"true"},
            files={"source": (FILM.name,stream,"video/mp4")},
            timeout=400,
        )
    resp.raise_for_status()
    result = resp.json()
    if not result.get("id"):
        raise RuntimeError("FACEBOOK_DID_NOT_RETURN_AN_ACCEPTED_VIDEO_ID")
    return {"id":str(result["id"]), "phase":"accepted_processing",
            "url":"https://www.facebook.com/" + str(result["id"])}


def instagram_upload(ig_id,token):
    headers={"Authorization":"Bearer " + token}
    body={
        "media_type":"REELS", "video_url":RELEASE_URL,
        "caption":DESCRIPTION, "share_to_feed":"true",
    }
    response = requests.post(
        GRAPH + "/" + ig_id + "/media",data=body,headers=headers,timeout=75)
    response.raise_for_status()
    result=response.json()
    container_id=result.get("id")
    if not container_id:
        raise RuntimeError("INSTAGRAM_MEDIA_CONTAINER_NOT_ACCEPTED")
    # Record container immediately after successful creation. If processing
    # fails or times out, future runs must RESUME GETs and never create again.
    return str(container_id)


def poll_ig_container(ig_id,token,container_id):
    hdr={"Authorization":"Bearer " + token}
    for _ in range(24):
        response=requests.get(GRAPH + "/" + container_id,
                              params={"fields":"status_code,status"},
                              headers=hdr,timeout=30)
        response.raise_for_status()
        code=response.json().get("status_code")
        if code=="FINISHED":
            return True
        if code in ("ERROR","EXPIRED"):
            raise RuntimeError("INSTAGRAM_MEDIA_CONTAINER_FAILED")
        time.sleep(10)
    return False


def publish_ig_container(ig_id,token,container_id):
    resp=requests.post(GRAPH + "/" + ig_id + "/media_publish",
                       headers={"Authorization":"Bearer " + token},
                       data={"creation_id":container_id},timeout=75)
    resp.raise_for_status()
    result=resp.json()
    if not result.get("id"):
        raise RuntimeError("INSTAGRAM_MEDIA_PUBLISH_DID_NOT_RETURN_ID")
    permalink=None
    try:
        v=requests.get(GRAPH + "/" + str(result["id"]),
                       params={"fields":"id,permalink"},
                       headers={"Authorization":"Bearer " + token},timeout=25)
        if v.ok:
            permalink=v.json().get("permalink")
    except requests.RequestException:
        pass
    return {"id":str(result["id"]), "phase":"accepted_processing",
            "url":permalink}


def execute():
    if os.getenv("OWNER_AUTHORIZED_E01_PUBLIC_UPLOAD") != "YES":
        raise RuntimeError("EXPLICIT_USER_APPROVAL_MISSING")
    meta=verified_source()
    result, previous=read_receipt()
    result["technical_mp4"] = meta
    result["public_github_asset"] = RELEASE_URL
    previous=save_receipt(result,previous)
    # Select only the exact Nightfall Diaries Page; no publishing to user profile.
    if result["facebook"]["phase"]=="not_attempted":
        if credential_probe("facebook")["read_only_identity_verified"]:
            page=resolve_nightfall_page()
            result["facebook"]={"phase":"initiated_no_auto_retry"}
            previous=save_receipt(result,previous)
            try:
                result["facebook"]=upload_fb(page)
            except Exception as exc:
                result["facebook"]={"phase":"ambiguous_do_not_retry",**clean_error(exc)}
            previous=save_receipt(result,previous)
        else:
            result["facebook"]={"phase":"blocked_identity_not_verified"}
            previous=save_receipt(result,previous)
    # Public video hosting needed for IG. Never post IG to a random account.
    if result["instagram"]["phase"]=="not_attempted":
        if credential_probe("instagram")["read_only_identity_verified"]:
            try:
                check_public_github_asset()
            except Exception as exc:
                result["instagram"]={"phase":"blocked_hosted_video_not_reachable",
                                    **clean_error(exc)}
                previous=save_receipt(result,previous)
            else:
                ig_id=os.environ["INSTAGRAM_ACCOUNT_ID"]
                ig_key=os.environ["INSTAGRAM_ACCESS_TOKEN"]
                result["instagram"]={"phase":"creation_initiated_no_auto_retry"}
                previous=save_receipt(result,previous)
                try:
                    container=instagram_upload(ig_id,ig_key)
                    result["instagram"]={"phase":"container_accepted",
                                         "container_id":container}
                    previous=save_receipt(result,previous)
                except Exception as exc:
                    result["instagram"]={"phase":"ambiguous_do_not_retry",**clean_error(exc)}
                    previous=save_receipt(result,previous)
        else:
            result["instagram"]={"phase":"blocked_identity_not_verified"}
            previous=save_receipt(result,previous)
    if result["instagram"]["phase"]=="container_accepted":
        item=result["instagram"]
        key=os.environ.get("INSTAGRAM_ACCESS_TOKEN","")
        ident=os.environ.get("INSTAGRAM_ACCOUNT_ID","")
        try:
            if poll_ig_container(ident,key,item["container_id"]):
                item["phase"]="publish_initiated_no_auto_retry"
                result["instagram"]=item
                previous=save_receipt(result,previous)
                result["instagram"]=publish_ig_container(
                    ident,key,item["container_id"])
            else:
                item["phase"]="container_still_processing"
                result["instagram"]=item
        except Exception as exc:
            result["instagram"]["phase"]="ambiguous_do_not_retry"
            result["instagram"].update(clean_error(exc))
        previous=save_receipt(result,previous)
    report=Path("output/painterly_release/social_upload_result.json")
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print("NIGHTFALL_E01_SOCIAL_UPLOAD",json.dumps({
        "facebook":result["facebook"]["phase"],
        "instagram":result["instagram"]["phase"],
        "youtube":result["youtube"]["phase"],
        "tiktok":result["tiktok"]["phase"],
        "mp4_seconds":meta["duration"],
        "public_visibility_verification":"NOT_YET_CONFIRMED",
    }))
    return result


if __name__=="__main__":
    execute()
