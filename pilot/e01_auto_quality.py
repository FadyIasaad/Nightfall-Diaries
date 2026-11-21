"""Free, deterministic evidence-based scoring for Nightfall REAL AI clips.

NO vision-model/semantic guarantee: these measures catch blank/frozen frames,
low motion, excessive crops and weak texture. Fire, identity, captions and
convincing lip-sync require a separate semantic verifier (NOT YET IMPLEMENTED).
Scores rank REAL candidates only and never authorize public publishing.
"""
from __future__ import annotations
import json
import math
import statistics
import subprocess
from pathlib import Path

WIDTH, HEIGHT = 96, 144
FRAME_TIMES = (0.25, 1.25, 2.25, 3.25)
PIXELS=WIDTH*HEIGHT


def frames(path:Path):
    results=[]
    for t in FRAME_TIMES:
        proc=subprocess.run([
          "ffmpeg","-nostdin","-hide_banner","-loglevel","error",
          "-ss",str(t),"-i",str(path),"-vf",f"scale={WIDTH}:{HEIGHT}:flags=bicubic,format=rgb24",
          "-frames:v","1","-f","rawvideo","pipe:1"],
          capture_output=True,timeout=35,check=True)
        frame=proc.stdout
        if len(frame)!=PIXELS*3:
            raise RuntimeError("MISSING_REAL_VIDEO_SAMPLE_FRAME")
        results.append(frame)
    return results


def measure(samples):
    if len(samples)!=4 or any(len(x)!=PIXELS*3 for x in samples):
        raise RuntimeError("REQUIRES_FOUR_REAL_VIDEO_FRAMES")
    framechanges=[]
    sharpness=[]
    blackratio=[]
    orange_edges=[]
    for frame in samples:
        # Work at low 96x144 resolution, without expensive GPU packages.
        grayscale=[]
        blacks=0
        warm_edge=0
        for i in range(PIXELS):
            k=3*i
            r,g,b=frame[k],frame[k+1],frame[k+2]
            lum=(299*r+587*g+114*b)//1000
            grayscale.append(lum)
            if lum<12:
                blacks+=1
            x=i%WIDTH
            y=i//WIDTH
            if (x<5 or x>WIDTH-6) and 39<y<133 and r>g*1.22 and g>b*1.13 and r>85:
                warm_edge+=1
        blackratio.append(blacks/PIXELS)
        orange_edges.append(warm_edge/(10*93))
        edge_sum=0
        for y in range(1,HEIGHT-1,2):
            base=y*WIDTH
            for x in range(1,WIDTH-1,2):
                v=grayscale[base+x]
                edge_sum+=abs(v-grayscale[base+x+1])+abs(v-grayscale[base+WIDTH+x])
        sharpness.append(edge_sum/((HEIGHT//2)*(WIDTH//2)*2*255))
    for prev,nxt in zip(samples,samples[1:]):
        altered=0
        mean_diff=0
        for i in range(0,len(prev),3):
            a=(299*prev[i]+587*prev[i+1]+114*prev[i+2])//1000
            b=(299*nxt[i]+587*nxt[i+1]+114*nxt[i+2])//1000
            delta=abs(a-b)
            mean_diff+=delta
            altered+=delta>15
        framechanges.append({"changed_pixel_fraction":altered/PIXELS,
                             "luma_difference_fraction":mean_diff/(PIXELS*255)})
    motion=statistics.mean(x["changed_pixel_fraction"] for x in framechanges)
    motion_mean=statistics.mean(x["luma_difference_fraction"] for x in framechanges)
    clarity=statistics.mean(sharpness)
    black=statistics.mean(blackratio)
    orange_border=statistics.mean(orange_edges)
    motion_score=min(1, motion/.38)
    sharpness_score=min(1,clarity/.085)
    framing_proxy=max(0,min(1,1-orange_border*.52))
    black_score=max(0,1-black*4)
    weighted=(.40*motion_score+.27*sharpness_score+.18*framing_proxy+.15*black_score)
    flags=[]
    if motion<.13:flags.append("WEAK_FRAME_MOTION")
    if clarity<.024:flags.append("SOFT_LOW_DETAIL_FRAMES")
    if black>.08:flags.append("LARGE_DARK_SCREEN_FRACTION")
    if orange_border>.65:flags.append("POSSIBLE_ACTOR_AT_FRAME_EDGE")
    return {
        "score_0_to_100":round(weighted*100,2),
        "frame_motion_changed_pixel_fraction":round(motion,4),
        "frame_motion_mean_luma_difference":round(motion_mean,4),
        "sharpness_texture_proxy":round(clarity,4),
        "mean_near_black_fraction":round(black,4),
        "possible_orange_subject_border_proxy":round(orange_border,4),
        "machine_flags":flags,
        "passes_basic_machine_motion_gate":not flags and weighted>=.60,
        "source_framing_or_background_story_semantics_verified":False,
        "characters_and_accessories_verified":False,
        "no_text_or_ui_artifacts_semantically_verified":False,
        "natural_animal_lip_sync_verified":False,
        "public_publish_approved":False,
        "explanation":"Automatic ranking of low-level visual evidence only; no VLM/semantic QA, no mouth verification."
    }


def score_clip(path):
    return measure(frames(Path(path)))


if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("video",type=Path)
    args=parser.parse_args()
    print(json.dumps(score_clip(args.video),indent=2))
