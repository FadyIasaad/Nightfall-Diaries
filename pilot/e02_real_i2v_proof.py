"""E02 single-shot LTX-2.3 I2V experiment. Strictly free, isolated, unpublished.

This is NOT a complete episode, does not certify face acting or character identity,
and intentionally never falls back to rejected 2.5D cutouts or slide motion.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

SPACE = "Lightricks/LTX-2-3"
API = "/generate_video"
REFERENCE = Path("assets/cinematic_refs/ember_approved_candidate_2026-11-13.webp")
REFERENCE_SHA256 = "c6cfda4f199c13d5fdf6d4e5057026d718787a495aefc29125c06779eb662432"
OUT = Path("output/e02_real_i2v_proof")
TARGET = OUT / "E02_Ember_Real_AI_Scene_UNAPPROVED.mp4"
PROMPT = (
    "Continue this exact approved fox cub's appearance and colors in one "
    "unbroken portrait cinematic animation shot. Ember has a white-tipped "
    "LEFT ear, amber eyes, russet fur, cream chest, teal scarf with exactly "
    "ONE embroidered golden star. A realistic richly detailed smoke-filled "
    "forest village gate at dawn; weathered wood, moss-covered tree roots, "
    "volumetric ash, drifting sunlight and moving foliage. The entire forest "
    "exists in the same three-dimensional perspective as the fox. Ember runs "
    "toward the creaking gate, braces himself against uneven muddy earth, "
    "turns back with frightened expressive eyes as the gate shuts; scarf and "
    "fur respond naturally to wind, paws visibly land, ground shadows change "
    "as he moves. Camera tracks smoothly beside him, actual full-body "
    "movement not an image pan. No text, logo, fake social interface, "
    "black bars, subtitles, dialogue boxes, split screen, or synthetic "
    "lettering. No spoken dialogue in this motion-only proof."
)

def fp(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(65536),b""):
            h.update(block)
    return h.hexdigest()

def verify_video(path):
    result=subprocess.run(
        ["ffprobe","-v","error","-of","json",
         "-show_entries","format=duration:stream=codec_type,codec_name,width,height",
         str(path)],capture_output=True,text=True,check=True,timeout=30)
    data=json.loads(result.stdout)
    d=float(data["format"]["duration"])
    v=next((x for x in data["streams"] if x["codec_type"]=="video"),None)
    if not v or not (3.0<=d<=6.0) or int(v["height"])<=int(v["width"]):
        raise RuntimeError("NOT_VALID_4S_PORTRAIT_REAL_VIDEO")
    if int(v["width"])<384 or int(v["height"])<576:
        raise RuntimeError("BELOW_MINIMUM_TECHNICAL_RESOLUTION")
    return {"duration_seconds":round(d,3),"width":v["width"],"height":v["height"],
            "video_codec":v["codec_name"],"sha256":fp(path)}

def run(mode):
    OUT.mkdir(parents=True,exist_ok=True)
    report={
        "episode":"S01_the_last_little_fox_E02",
        "source":str(REFERENCE),
        "source_sha256":REFERENCE_SHA256,
        "output_status":"PREPARING",
        "ai_real_motion_verified":False,
        "human_visual_approval":False,
        "lip_sync_verified":False,
        "complete_episode_180s":False,
        "public_publishing_allowed":False,
        "provider_paid":False,
        "free_quota_guaranteed":False,
        "legacy_2d_fallback":False,
    }
    try:
        if any(os.environ.get(k) for k in
               ("HF_TOKEN","AGNES_API_KEY","EVERYPIXEL_API_KEY","RUNWAY_API_KEY")):
            raise RuntimeError("REFUSE_PROVIDER_KEY_TO_AVOID_UNVERIFIED_CHARGES")
        if not REFERENCE.is_file() or fp(REFERENCE)!=REFERENCE_SHA256:
            raise RuntimeError("LOCKED_EMBER_REFERENCE_MISSING_OR_CHANGED")
        if mode=="generate":
            from gradio_client import Client,handle_file
            c=Client(SPACE,verbose=False)
            available={str(e.api_name) for e in c.endpoints.values()}
            if API not in available:
                raise RuntimeError("OFFICIAL_FREE_DEMO_ENDPOINT_CHANGED")
            result=c.predict(handle_file(str(REFERENCE.resolve())),PROMPT,
                             4.0,False,20261118,False,768,512,api_name=API)
            movie=result[0] if isinstance(result,(list,tuple)) else result
            if isinstance(movie,dict):
                movie=movie.get("video") or movie.get("path")
            if not isinstance(movie,str) or not Path(movie).is_file():
                raise RuntimeError("ZERO_GPU_NO_MP4_RETURNED")
            shutil.copyfile(movie,TARGET)
            if TARGET.stat().st_size<10000:
                raise RuntimeError("INVALID_TINY_VIDEO")
            report["technical_media"]=verify_video(TARGET)
            report["output_status"]="REAL_MOTION_TECHNICALLY_PLAYABLE_ART_REVIEW_PENDING"
        else:
            report["output_status"]="SOURCE_LOCK_AND_ZERO_CHARGE_CHECK_PASS"
    except Exception as exc:
        report["output_status"]="BLOCKED_NO_APPROVED_EPISODE"
        report["error_type"]=type(exc).__name__
        report["reason"]=str(exc)[:250]
    (OUT/"report.json").write_text(json.dumps(report,indent=2)+"\n")
    print("E02_REAL_VIDEO_TEST",report["output_status"])
    if report["output_status"]=="BLOCKED_NO_APPROVED_EPISODE":
        raise SystemExit(1)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--mode",choices=("source-check","generate"),default="source-check")
    args=p.parse_args()
    run(args.mode)
