"""Nightfall E01 director's cut V2, CPU-only real animated scenes, original voices.

Repairs old E01's 216s / 97.5s dialogue padding with measured, intentional
180-second storyline: 14 distinct art-directed environments, genuine motion
and atmosphere under each scene, without black frames or silent filler.
The original canonical story and Kokoro WAVs remain SHA-verified/unmodified.
No paid video APIs, no misleading CGI/lip-sync claim, no public posting.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import random
import struct
import subprocess
import wave

from pilot import e01_cpu_film as original
from studio.e01_v2_art_direction import SETS, frame
from studio.continuity import sha256
from studio.quality_gate import check_media

ROOT=original.ROOT
OUT=ROOT/"output/nightfall_e01_director_v2"
STATE=OUT/"progress.json"
FINAL=OUT/"Nightfall_S01_E01_Directors_Cut_Story_Sets_180s_REVIEW.mp4"
FPS=12
MIN_SECONDS=180
VERSION="nightfall-e01-v2-canon-finale-moss-forest-20261116"
# Story weights correspond to physical action rather than a generic hold.
ACTION_WEIGHTS=(8,5,4,4,3,4,3,7,8,8,7,7,5,7)


def cmd(args,timeout=1800):
    done=subprocess.run(args,text=True,capture_output=True,timeout=timeout)
    if done.returncode:
        raise RuntimeError("FFMPEG_NONZERO_RETURN:"+done.stderr[-480:])
    return done


def voice_seconds(path):
    with wave.open(str(path),"rb") as f:
        if f.getnchannels()!=1 or f.getsampwidth()!=2 or f.getframerate()!=24000:
            raise RuntimeError("ORIGINAL_NEURAL_VOICE_WAV_FORMAT_CHANGED")
        return f.getnframes()/f.getframerate()


def frame_budget(voices):
    """Total exactly 180 seconds: immediate dialogue then purposeful action.

    No scene can be artificially slowed down, looped, or frozen; this function
    defines how many original ACTING and moving-environment frames to render.
    """
    times=[voice_seconds(voices[n]) for n in range(1,15)]
    if len(times)!=14 or sum(times)<85 or sum(times)>140:
        raise RuntimeError("VOICE_DURATIONS_UNEXPECTED_NO_FORCED_TIMELINE")
    voiceframes=[math.ceil(d*FPS) for d in times]
    total=180*FPS
    rest=total-sum(voiceframes)
    weights=ACTION_WEIGHTS
    share=[rest*w/sum(weights) for w in weights]
    extra=[int(s) for s in share]
    remainder=rest-sum(extra)
    # Largest remainder, deterministic, no narration modification.
    for i in sorted(range(14),key=lambda i:(-(share[i]-int(share[i])),i))[:remainder]:
        extra[i]+=1
    allframes=[a+b for a,b in zip(voiceframes,extra)]
    if sum(allframes)!=total or not all(f>=math.ceil(d*FPS) for f,d in zip(allframes,times)):
        raise RuntimeError("CONTINUITY_DURATION_BUDGET_INVALID")
    if not all(7*FPS<=f<=21*FPS for f in allframes):
        raise RuntimeError("EXCESSIVE_SINGLE_SCENE_GAP")
    return allframes,times


def sound_bed(scene,frames,dest):
    """Audible, original continuous atmospheric design with action accents."""
    secs=frames/FPS
    rate=24000
    seed=random.Random(scene*991)
    kind=SETS[scene][0]
    fire=scene<=11
    blue=scene>=12 or scene in (3,4,5)
    with wave.open(str(dest),"wb") as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(rate)
        data=bytearray()
        # Scene-specific wind, rustle, fire/stone crackles, feather chimes.
        for n in range(round(secs*rate)):
            t=n/rate
            wind=165*math.sin(t*.76+scene)+95*math.sin(t*1.98)
            drone=105*math.sin(2*math.pi*(62 if fire else 79)*t)
            hiss=seed.randint(-310,310)*(0.70 if fire else .25)
            sparks=(seed.randint(-1550,1550) if (n%(rate//4)<140) else 0)*.16
            water=(100*math.sin(2*math.pi*176*t)) if scene in (8,9,10,11) else 0
            glow=130*math.sin(2*math.pi*196*t)*math.sin(t*1.3)**2 if blue else 0
            value=int(max(-32760,min(32760,4.2*(wind+drone+hiss+sparks+water+glow))))
            data.extend(struct.pack("<h",value))
            if len(data)>=48000:
                f.writeframesraw(data);data.clear()
        if data:f.writeframesraw(data)


def levels(wav,total):
    return original.audio_levels(wav,total)


def render_scene(scene,frames,meta,voice,dest):
    seconds=frames/FPS
    wavsec=voice_seconds(voice)
    if wavsec>seconds-.15:raise RuntimeError("VOICE_CANNOT_FIT_REAL_ANIMATION")
    raw=OUT/f"scene_{scene:02d}_raw.mp4"
    # Both animated frames and audio MUST be real; no stills/slideshow.
    if not raw.is_file():
        ff=["ffmpeg","-hide_banner","-nostdin","-loglevel","error","-y",
            "-f","rawvideo","-pix_fmt","rgb24","-s:v","360x640",
            "-r",str(FPS),"-i","pipe:0","-an","-c:v","libx264",
            "-preset","veryfast","-crf","19","-pix_fmt","yuv420p",str(raw)]
        audio_levels=levels(voice,frames)
        with subprocess.Popen(ff,stdin=subprocess.PIPE,stderr=subprocess.PIPE) as proc:
            for i in range(frames):
                t=i/FPS
                img=frame(scene,t,audio_levels[i],wavsec,
                          meta["script_text"],meta["speaker"],
                          meta["visible"],meta["direction"])
                if i==frames//2:
                    img.save(OUT/f"scene_{scene:02d}_still.png")
                try:proc.stdin.write(img.tobytes())
                except BrokenPipeError:
                    raise RuntimeError("RENDER_FFMPEG_BROKEN_PIPE")
            proc.stdin.close()
            err=proc.stderr.read()
            code=proc.wait(timeout=480)
            if code:raise RuntimeError("ANIMATED_RENDER_FFMPEG_FAIL:"+err.decode(errors="replace")[-400:])
    ambience=OUT/f"scene_{scene:02d}_environment.wav"
    if not ambience.is_file():sound_bed(scene,frames,ambience)
    cmd(["ffmpeg","-hide_banner","-nostdin","-loglevel","error","-y",
         "-i",str(raw),"-i",str(voice),"-i",str(ambience),
         "-filter_complex","[1:a]apad,volume=1.0[voice];"
         "[2:a]volume=0.55[fx];[voice][fx]"
         "amix=inputs=2:duration=longest:normalize=0[a]",
         "-map","0:v:0","-map","[a]","-c:v","copy",
         "-c:a","aac","-ar","24000","-b:a","128k",
         "-t",f"{seconds:.6f}",str(dest)],timeout=900)
    if not dest.is_file() or dest.stat().st_size<10000:
        raise RuntimeError("NO_REAL_ANIMATED_SCENE_MP4")
    return seconds


def save(data):
    OUT.mkdir(parents=True,exist_ok=True)
    p=STATE.with_suffix(".tmp")
    p.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    p.replace(STATE)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--mode",choices=("sample","full"),default="sample")
    args=parser.parse_args()
    old,oldplan,voices,oldbudgets=original.load_inputs()
    frames,times=frame_budget(voices)
    vhash={str(i):sha256(voices[i]) for i in range(1,15)}
    core={"schema":VERSION,"episode":oldplan["episode"],
          "canon_plan_sha256":oldplan["plan_sha256"],"scene_ids":list(range(1,15)),
          "scene_set_keys":[SETS[i][0] for i in range(1,15)],
          "voice_sha256":vhash,"scene_frame_counts":frames,
          "total_frames":sum(frames),"target_seconds":180,
          "render_style":"painted_illustrated_2_5d_not_ai_video"}
    digest=hashlib.sha256(json.dumps(core,sort_keys=True).encode()).hexdigest()
    OUT.mkdir(parents=True,exist_ok=True)
    if STATE.exists():
        state=json.loads(STATE.read_text())
        if state.get("input_sha256")!=digest:
            raise RuntimeError("CHECKPOINT_MISMATCH_NO_DESTRUCTIVE_RESTART")
    else:
        state={**core,"input_sha256":digest,"completed":[],
               "status":"RENDERING","public_posts_created":False,
               "visual_owner_approved":False,"phoneme_lipsync_approved":False}
        save(state)
    targets=[1] if args.mode=="sample" else list(range(1,15))
    for n in targets:
        dest=OUT/f"scene_{n:02d}_v2.mp4"
        done=next((x for x in state["completed"] if x["scene"]==n),None)
        if done and dest.is_file() and sha256(dest)==done["sha256"]:
            continue
        if done:raise RuntimeError("MISSING_OR_WRONG_SHA_SCENE_NO_SILENT_REGENERATION")
        sec=render_scene(n,frames[n-1],old["scenes"][n-1],voices[n],dest)
        state["completed"].append({"scene":n,"sha256":sha256(dest),
                                   "file":dest.name,"seconds":round(sec,3),
                                   "set":SETS[n][0]})
        save(state)
        print("NIGHTFALL_V2_REAL_SCENE",n,"/14",SETS[n][0],round(sec,3),flush=True)
    if args.mode=="sample":
        state["status"]="SAMPLE_REVIEW_NO_UPLOAD"
        save(state)
        return
    if len(state["completed"])!=14:
        raise RuntimeError("CANNOT_ASSEMBLE_INCOMPLETE_EPISODE")
    playlist=OUT/"concat.txt"
    playlist.write_text("".join(
        "file '"+str((OUT/f"scene_{i:02d}_v2.mp4").resolve())+"'\n"
        for i in range(1,15)),encoding="utf-8")
    cmd(["ffmpeg","-hide_banner","-nostdin","-loglevel","error","-y",
         "-f","concat","-safe","0","-i",str(playlist),
         "-vf","fps=24,scale=720:1280:flags=lanczos",
         "-c:v","libx264","-preset","veryfast","-crf","19",
         "-pix_fmt","yuv420p","-c:a","aac","-ar","48000","-b:a","160k",
         "-movflags","+faststart",str(FINAL)],timeout=2100)
    qa=check_media(FINAL,mode="cinematic_episode")
    if abs(qa["duration_seconds"]-180)>1.5:
        raise RuntimeError("NO_GAP_180_SECOND_TIMELINE_FAILED")
    state["status"]="COMPLETE_V2_REVIEW_UNPUBLISHED"
    state["film_sha256"]=sha256(FINAL)
    state["film_seconds"]=qa["duration_seconds"]
    state["public_posts_created"]=False
    save(state)
    (OUT/"quality_report.json").write_text(
        json.dumps({**qa,"old_film_seconds":216.08,
                    "old_dialogue_seconds":round(sum(times),3),
                    "new_timeline_seconds":qa["duration_seconds"],
                    "14_original_voices_SHA_verified":True,
                    "14_story_backgrounds":{str(k):v[0] for k,v in SETS.items()},
                    "moss_visual_upgrade":"custom_painterly_shaded_shell_face_scutes",
                    "real_mp4":FINAL.name,"new_public_uploads":False,
                    "phoneme_lipsync_verified":False,
                    "owner_visual_approval":False},indent=2)+"\n")
    print("NIGHTFALL_E01_V2_REAL_FINISHED",qa,flush=True)


if __name__=="__main__":
    main()
