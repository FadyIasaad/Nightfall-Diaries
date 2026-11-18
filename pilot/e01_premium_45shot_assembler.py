"""Assemble an E01 cinematic film ONLY when 45 genuinely distinct clips exist.

Strictly no cutout, slideshow, repeated still, stretch, loop, made-up dialogue
or public release. An actual 180-second soundtrack can be attached.
This module is an editor/QA, not a GPU video-generation engine.
"""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STORY = ROOT / "seasons/S01_the_last_little_fox/revised_screenplays/E01_2026-11-18.json"
SHOTS = ROOT / "output/e01_real_45shots"
SOUNDTRACK = ROOT / "output/e01_180s_cinematic_soundtrack/Nightfall_S01_E01_180s_original_soundtrack_REVIEW.wav"
FINAL = ROOT / "output/e01_verified_master/Nightfall_S01_E01_180s_GENUINE_AI_FILM_REVIEW_UNPUBLISHED.mp4"
REVIEW = ROOT / "output/e01_verified_master/verified_shots_report.json"
SHOT_SECONDS = 4
SCENE_COUNT = 15
SHOT_COUNT = 45
FPS = 24


def file_sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(65536),b""):
            h.update(chunk)
    return h.hexdigest()


def run_ffmpeg(args, timeout=260):
    p = subprocess.run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",*map(str,args)],
                       capture_output=True,text=True,timeout=timeout,check=False)
    if p.returncode:
        raise RuntimeError("FFMPEG_CLIP_OPERATION_FAILED: "+(p.stderr or "")[-400:])


def probe(path):
    p = subprocess.run(["ffprobe","-v","error","-of","json",
       "-show_entries","format=duration:stream=codec_type,codec_name,width,height",
       str(path)],capture_output=True,text=True,check=True,timeout=35)
    return json.loads(p.stdout)


def planned():
    data=json.loads(STORY.read_text(encoding="utf-8"))
    scenes=data["scenes"]
    if len(scenes)!=SCENE_COUNT or data["episode_id"]!="S01_the_last_little_fox_E01":
        raise RuntimeError("WRONG_CANON_STORY_PLAN")
    if data["target_duration_seconds"]!=180 or data["planned_distinct_real_video_shots"]!=SHOT_COUNT:
        raise RuntimeError("180S_45_SHOT_TARGET_MISMATCH")
    shots=[]
    for s in scenes:
        if s["shot_seconds"] != [4,4,4] or s["shot_count"]!=3:
            raise RuntimeError("UNSUPPORTED_SCENE_TIMELINE")
        for shot_number in (1,2,3):
            shots.append({
                "scene":s["scene"],"shot":shot_number,
                "beat":s["beat"],
                "character":s["character_id"],
                "time_start":(s["scene"]-1)*12 + (shot_number-1)*4,
                "time_end":(s["scene"]-1)*12 + shot_number*4,
                "file":f"scene_{s['scene']:02d}_shot_{shot_number:02d}.mp4",
                "approval":f"scene_{s['scene']:02d}_shot_{shot_number:02d}.approval.json",
                "voice_speaker":s["character_id"]
            })
    return shots


def sound_ready():
    if not SOUNDTRACK.exists():
        return False
    info=probe(SOUNDTRACK)
    return 179.9<=float(info["format"]["duration"])<=180.1 and any(
        s["codec_type"]=="audio" for s in info["streams"])


def audit_shots(strict=False):
    expected=planned()
    available=[]
    missing=[]
    invalid=[]
    existing_hashes=set()
    for item in expected:
        clip=SHOTS/item["file"]
        approval=SHOTS/item["approval"]
        if not clip.is_file():
            missing.append(item["file"])
            continue
        try:
            media=probe(clip)
            v=next(s for s in media["streams"] if s["codec_type"]=="video")
            seconds=float(media["format"]["duration"])
            if not 3.99<=seconds<=5.5:
                raise RuntimeError("MOTION_CLIP_SHORT_OR_UNEXPECTED_DURATION")
            if int(v.get("width",0))<384 or int(v.get("height",0))<576:
                raise RuntimeError("CINEMATIC_SHOT_RESOLUTION_TOO_LOW")
            if int(v["height"])<=int(v["width"]):
                raise RuntimeError("NOT_PORTRAIT_VIDEO")
            digest=file_sha(clip)
            if digest in existing_hashes:
                raise RuntimeError("DUPLICATE_MP4_REPLAY")
            existing_hashes.add(digest)
            if not approval.is_file():
                raise RuntimeError("MISSING_OWNER_VISUAL_QA_APPROVAL_SIDECAR")
            qa=json.loads(approval.read_text(encoding="utf-8"))
            if qa.get("sha256")!=digest:
                raise RuntimeError("CLIP_CHANGED_AFTER_VISUAL_QA")
            required=("consistent_ember_and_cast","genuine_body_motion",
                      "rich_integrated_background","no_fake_ui_or_black_frames",
                      "natural_dialogue_or_nonvisible_speaker")
            if not all(qa.get(k) is True for k in required):
                raise RuntimeError("HUMAN_VISUAL_REVIEW_NOT_PASSED")
            available.append({**item,"sha256":digest,"seconds":round(seconds,3),
                              "approved":True})
        except (ValueError,KeyError,StopIteration,subprocess.SubprocessError,
                RuntimeError,OSError) as exc:
            invalid.append({"clip":item["file"],"reason":str(exc)[:180]})
    result={
        "episode":"S01_the_last_little_fox_E01",
        "status":"MISSING_OR_UNAPPROVED_VIDEO_SHOTS",
        "expected_unique_clips":SHOT_COUNT,
        "actual_visually_approved_unique_clips":len(available),
        "missing_count":len(missing),
        "invalid_count":len(invalid),
        "soundtrack_available":sound_ready(),
        "missing":missing,
        "invalid":invalid,
        "approved":available,
        "full_cinematic_film_created":False,
        "human_owner_visual_approval_proven":len(available)==SHOT_COUNT,
        "paid_gpu_used":False,
        "public_upload_permitted":False
    }
    REVIEW.parent.mkdir(parents=True,exist_ok=True)
    REVIEW.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    if strict and (missing or invalid or not sound_ready()):
        raise RuntimeError(f"E01_NOT_READY: {len(available)}/{SHOT_COUNT} original approved moving shots, soundtrack={sound_ready()}")
    return result


def assemble():
    state=audit_shots(strict=True)
    FINAL.parent.mkdir(parents=True,exist_ok=True)
    clips=[]
    for item in state["approved"]:
        clip=SHOTS/item["file"]
        normalized=FINAL.parent/(Path(item["file"]).stem+"_normalized.mp4")
        # 4.0s of genuine filmed frames. Never artificially extend a short clip.
        run_ffmpeg(["-i",clip,"-vf",
          "scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,"
          "fps=24,trim=duration=4,setpts=PTS-STARTPTS,format=yuv420p",
          "-an","-c:v","libx264","-crf","20","-preset","medium","-t","4",normalized])
        m=probe(normalized)
        if not 3.95<=float(m["format"]["duration"])<=4.05:
            raise RuntimeError("SCENE_NORMALIZATION_CREATED_TIMELINE_GAP")
        # A full frozen sequence fails even when metadata and duration pass.
        check=subprocess.run(["ffmpeg","-hide_banner","-nostdin","-i",str(normalized),
                 "-vf","blackdetect=d=0.35:pix_th=0.12,freezedetect=n=-55dB:d=1.4",
                 "-an","-f","null","-"],capture_output=True,text=True,timeout=90)
        if check.returncode!=0 or "black_start:" in check.stderr or "freeze_start:" in check.stderr:
            raise RuntimeError("GAP_BLACK_SCREEN_OR_STATIC_CAMERA_IN_"+item["file"])
        clips.append(normalized)
    if len(clips)!=SHOT_COUNT:
        raise RuntimeError("NOT_ALL_DISTINCT_RENDERED_VIDEO_CLIPS")
    concat=FINAL.parent/"approved_45shot_concat.txt"
    concat.write_text("".join("file '"+str(p.resolve()).replace("'","")+"'\n" for p in clips))
    visual=FINAL.parent/"genuine_motion_silent_180s.mp4"
    run_ffmpeg(["-f","concat","-safe","0","-i",concat,"-c:v","copy",visual],timeout=540)
    if not 179.6<=float(probe(visual)["format"]["duration"])<=180.4:
        raise RuntimeError("VISUAL_TIMELINE_NOT_180_SECONDS")
    run_ffmpeg(["-i",visual,"-i",SOUNDTRACK,"-map","0:v:0","-map","1:a:0",
       "-c:v","copy","-c:a","aac","-b:a","192k","-t","180","-movflags","+faststart",FINAL],timeout=480)
    from studio.quality_gate import check_media
    technical=check_media(FINAL,mode="cinematic_episode")
    # This is an internal 180s review cut. Final owner's release approval is
    # deliberately still separate, even when per-shot approvals were signed.
    state["status"]="180S_GENUINE_VISUAL_CUT_TECHNICAL_PASS_FINAL_OWNER_REVIEW_REQUIRED"
    state["film_sha256"]=file_sha(FINAL)
    state["technical_media"]=technical
    state["full_cinematic_film_created"]=True
    state["public_upload_permitted"]=False
    REVIEW.write_text(json.dumps(state,indent=2)+"\n",encoding="utf-8")
    return state


if __name__=="__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("--mode",choices=("audit","assemble"),default="audit")
    args=cli.parse_args()
    data=audit_shots() if args.mode=="audit" else assemble()
    print("E01_REAL_MOVING_FILM",data["status"],
          data["actual_visually_approved_unique_clips"],"/45")
