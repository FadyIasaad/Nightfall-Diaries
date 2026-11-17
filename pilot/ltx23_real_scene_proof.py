"""One non-publishing REAL generated scene experiment on public LTX 2.3 ZeroGPU.

Not a 2.5D puppet, pan/zoom slideshow, paid API or finished episode.
Tests the *concept* of a full environment shot. Identity and dialogue remain
unapproved until a locked-character reference and an audio-driven talking proof.
"""
import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path

SPACE = "Lightricks/LTX-2-3"
ENDPOINT = "/generate_video"
OUT = Path("output/real_ai_scene_proof")
PROMPT = (
    "A single seamless four-second shot from a premium stylized 3D animated "
    "adventure film. A small russet orange fox cub named Ember has a white tip "
    "on HIS LEFT ear, large expressive amber eyes, a soft cream muzzle and "
    "chest and richly detailed groomed fur. Around his neck is a fluttering "
    "turquoise woven scarf embroidered with EXACTLY ONE small golden star. "
    "The entire scene takes place in an immersive, highly detailed burning "
    "forest at twilight: enormous gnarled trunks, ferns, scorched moss, dark "
    "layered hills, thick volumetric smoke, firelight spilling across the soil "
    "and sparks drifting between foreground and background. The camera gently "
    "tracks beside the cub as he actually runs across the uneven forest floor, "
    "plants his paws, stops and looks back in fear; full body movement, tail "
    "and scarf following the wind with believable inertia. There is visible "
    "depth, atmospheric perspective, expressive eye motion and warm orange "
    "rim lighting integrated with the environment. Cinematic composition and "
    "believable environmental motion from the first to last frame. Original "
    "animated family adventure aesthetic. Natural forest and fire ambience, "
    "no narration in this proof. Absolutely NO dialogue box, subtitles, text, "
    "interface elements, blue icons, black screen, cuts, frozen frame, "
    "flat silhouette trees, pasted sprites, repeated frames or montage."
)

def technical_check(path):
    data = json.loads(subprocess.run(
        ["ffprobe","-v","error","-of","json",
         "-show_entries","format=duration:stream=codec_type,codec_name,width,height",
         str(path)], check=True, capture_output=True, text=True, timeout=30
    ).stdout)
    duration = float(data["format"]["duration"])
    video = next((s for s in data["streams"] if s["codec_type"]=="video"),None)
    if not video or video.get("codec_name") not in ("h264","hevc","av1","vp9"):
        raise RuntimeError("MODEL_DID_NOT_PRODUCE_PLAYABLE_VIDEO")
    w,h = int(video["width"]),int(video["height"])
    if not 3 <= duration <= 5.5 or w < 384 or h < 576 or h <= w:
        raise RuntimeError("VIDEO_PROOF_DURATION_OR_PORTRAIT_RESOLUTION_INVALID")
    return {"seconds":round(duration,3),"width":w,"height":h,
            "video_codec":video["codec_name"],
            "audio_stream_exists":any(s["codec_type"]=="audio" for s in data["streams"])}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--mode",choices=["probe","generate"],default="probe")
    args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    status={
        "model_space":SPACE, "endpoint":ENDPOINT,
        "provider_type":"public_HF_ZeroGPU_without_token",
        "paid_requests_or_tokens_used":False,
        "source_character_reference_applied":False,
        "canon_character_identity_verified":False,
        "dialogue_or_lipsync_verified":False,
        "human_cinematic_quality_approved":False,
        "episode_ready":False, "public_publishing_allowed":False,
        "old_2_5D_renderer_used":False,
        "prompt":PROMPT, "status":"PREFLIGHT"
    }
    try:
        # Guard against accidentally charging an account with a saved paid quota.
        if os.getenv("HF_TOKEN") or os.getenv("AGNES_API_KEY"):
            raise RuntimeError("REFUSE_CONNECTED_PAID_OR_AUTHENTICATED_PROVIDER_TOKENS")
        from gradio_client import Client
        client=Client(SPACE, verbose=False)
        endpoints = {str(e.api_name) for e in client.endpoints.values()}
        if ENDPOINT not in endpoints:
            raise RuntimeError("LTX_PUBLIC_GRADIO_ENDPOINT_UNAVAILABLE_OR_CHANGED")
        status["status"]="PUBLIC_ZERO_GPU_ENDPOINT_FOUND"
        if args.mode=="generate":
            # Exactly one short free anonymous demo job. No automatic fallback,
            # retry storm, paid provider or multi-scene generation.
            result=client.predict(None,PROMPT,4.0,False,9021,False,768,512,
                                  api_name=ENDPOINT)
            path=result[0] if isinstance(result,(list,tuple)) else result
            if isinstance(path,dict):
                path=path.get("video") or path.get("path")
            if not isinstance(path,str) or not Path(path).is_file():
                raise RuntimeError("ZERO_GPU_RETURNED_NO_REAL_MP4")
            movie=OUT/"ltx23_full_scene_4s_UNAPPROVED.mp4"
            shutil.copyfile(path,movie)
            if movie.stat().st_size < 10000:
                raise RuntimeError("ZERO_GPU_RETURNED_TINY_INVALID_FILE")
            status["technical_media"]=technical_check(movie)
            status["status"]="REAL_GENERATED_VIDEO_PROOF_READY_FOR_HUMAN_REVIEW"
    except Exception as e:
        status["status"]="BLOCKED_OR_FAILED_NO_QUALITY_CLAIM"
        status["error_type"]=type(e).__name__
        status["reason_redacted"]=str(e)[:240]
    (OUT/"report.json").write_text(json.dumps(status,indent=2)+"\n",encoding="utf-8")
    print("NEW_REAL_SCENE_PROOF_STATUS:",status["status"])
    if status["status"]=="BLOCKED_OR_FAILED_NO_QUALITY_CLAIM":
        raise SystemExit(1)

if __name__=="__main__":
    main()
