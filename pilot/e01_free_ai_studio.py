"""Nightfall E01 Free AI Studio — one genuine moving shot per day, checkpoint forever.

This is a *real* cloud production queue using the public free LTX-2.3 ZeroGPU
Gradio Space, not a slideshow, cutout renderer, fallback model, or paid API.
It persists every actual media clip in a PRIVATE-DRAFT GitHub release, so
nightly ephemeral GitHub runner disks never lose accumulated video.

One legitimate anonymous GPU request per Africa/Cairo calendar day, max.
Quota exhaustion pauses until the next day. All visual results require human
art review before release; none are automatically called beautiful or approved.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "seasons/S01_the_last_little_fox/revised_screenplays/E01_2026-11-18.json"
CAST = ROOT / "seasons/S01_the_last_little_fox/characters/character_registry.json"
EMBER = ROOT / "assets/cinematic_refs/ember_approved_candidate_2026-11-13.webp"
EMBER_SHA = "c6cfda4f199c13d5fdf6d4e5057026d718787a495aefc29125c06779eb662432"
FIRE_REFERENCE = ROOT / "assets/cinematic_refs/ember_firestorm_E01_owner_approved_20261121.png"
FIRE_REFERENCE_SHA = "0dd125b3d4953a76f1704666b526559e371c80faa019cb41bbb57f86ba162d1e"
OUT = ROOT / "output/e01_free_ai_studio"
VISUAL_REJECTIONS = ROOT / "docs/E01_RAW_AI_VISUAL_REJECTIONS_2026-11-19.json"
RELEASE_TAG = "nightfall-s01-e01-real-ai-draft-2026"
SPACE = "Lightricks/LTX-2-3"
API = "/generate_video"
REPO = "FadyIasaad/Nightfall-Diaries"
SCENES = 15
SHOTS_PER_SCENE = 3
TOTAL = SCENES * SHOTS_PER_SCENE
SECONDS_PER_SHOT = 4
PAID_KEYS = (
    "AGNES_API_KEY","EVERYPIXEL_API_KEY","RUNWAY_API_KEY",
    "ELEVENLABS_API_KEY","OPENAI_API_KEY","DASHSCOPE_API_KEY",
    "HF_TOKEN","HUGGING_FACE_HUB_TOKEN",
)
QUOTA_ERRORS = (
    "exceeded your zerogpu runs limit",
    "zerogpu quota",
    "not enough gpu quota",
    "your daily quota",
    "rate limit",
    "queue is full",
)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(128 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def now_cairo():
    return datetime.now(ZoneInfo("Africa/Cairo"))


def exec_cli(args, *, allowed_fail=False):
    result=subprocess.run(args, text=True, capture_output=True, timeout=90)
    if result.returncode and not allowed_fail:
        raise RuntimeError("GITHUB_DRAFT_RELEASE_OPERATION_FAILED: " +
                           (result.stderr or "")[-240:])
    return result


def guarantee_zero_paid_inference():
    if any(os.environ.get(k) for k in PAID_KEYS):
        raise RuntimeError("BILLABLE_OR_ACCOUNT_AUTH_PROVIDER_KEY_NOT_ALLOWED")
    if os.getenv("GITHUB_REF") not in ("refs/heads/main", None):
        raise RuntimeError("PRODUCTION_ONLY_ON_MAIN")
    if not EMBER.is_file() or sha(EMBER) != EMBER_SHA:
        raise RuntimeError("EMBER_ORIGINAL_IMAGE_HASH_MISMATCH")
    if not FIRE_REFERENCE.is_file() or sha(FIRE_REFERENCE) != FIRE_REFERENCE_SHA:
        raise RuntimeError("APPROVED_E01_BURNING_FOREST_REFERENCE_MISSING_OR_CHANGED")


def plan():
    story = json.loads(SCRIPT.read_text(encoding="utf-8"))
    cast = {x["id"]: x for x in json.loads(CAST.read_text(encoding="utf-8"))["characters"]}
    if (story["episode_id"] != "S01_the_last_little_fox_E01" or
        len(story["scenes"]) != SCENES or
        story["target_duration_seconds"] != 180):
        raise RuntimeError("LOCKED_E01_SCRIPT_UNEXPECTED")
    shots=[]
    for scene in story["scenes"]:
        if (scene["target_seconds"] != 12 or scene["shot_seconds"] != [4,4,4]
            or scene["shot_count"] != SHOTS_PER_SCENE):
            raise RuntimeError("SCENE_TIMING_UNEXPECTED")
        for idx in range(1,4):
            visible = scene["visible"]
            identity = ". ".join(cast[c]["visual"] for c in visible if c in cast)
            source_kind = ("ember" if visible == ["s01_ember"] else
                           "moss_reference_not_approved")
            phase = (
                "The foreground and forest establish real depth. The characters "
                "ENTER the environment and react naturally to the crisis."
                if idx==1 else
                "Advance the scene's physical action, with natural paws and "
                "body inertia. Track smoothly with convincing camera motion."
                if idx==2 else
                "Show the physical outcome and a believable character reaction. "
                "Cut after the action without freezing or repeating it."
            )
            # Avoid putting literal screenplay words into the video prompt:
            # the first real LTX E01 clip hallucinated subtitle text and had
            # almost-static body motion, despite a detailed environment.
            fire_setting = (
                "A clearly BURNING FOREST with large visible flames racing "
                "through real blackened tree trunks and billowing thick dark "
                "smoke behind the actor. Flying orange sparks and scorched "
                "forest floor. Not a green waterfall, peaceful lake or twilight "
                "flower garden. A real active fire must be visually obvious."
                if scene["scene"] <= 6 else
                "The charred forest aftermath with smoke, embers, damaged "
                "roots and the correct story-specific location, NOT a pleasant "
                "decorative meadow or unrelated scenery."
            )
            # The previous model retake let Ember leave the camera frame and
            # hallucinated the wrong peaceful forest. Camera framing is now
            # specified independently from how much the actor moves.
            prompt = (
                "An original premium stylized animated feature-film scene, "
                "one CONTINUOUS genuine four-second moving shot. The supplied "
                "APPROVED IMAGE is the actual scene image to be animated. "
                "Preserve its full three-dimensional burning-forest background, "
                "flames and smoke; do not substitute a healthy green forest. "
                "Ember is a russet fox cub with white-tipped LEFT ear, amber "
                "eyes, teal scarf and exactly ONE golden star. No redesign. "
                f"Required story world: {fire_setting} "
                f"Required actual action: {scene['direction']} "
                f"Motion beat: {phase} "
                "Natural paw/body movement and expressive physical acting; "
                "running actions translate at least one body length across "
                "the environment, while quieter actions show intentional "
                "facial and body reactions, not a zoom of a still. "
                "The tracking camera must KEEP THE COMPLETE FOX INSIDE THE "
                "FRAME for every moment. Full ears, tail and paws stay at "
                "least ten percent clear of picture edges; camera follows "
                "at matching speed rather than letting the actor run offscreen. "
                "Real continuous parallax: foreground roots, midground tree "
                "trunks and background fire all move in three-dimensional "
                "depth. No cuts, no letterboxing. Absolutely NO text, fake "
                "captions, subtitles, typography, social UI, icons, cards "
                "or logos. No dialogue; original studio voice supplied separately."
            )
            shots.append({
                "scene":scene["scene"],
                "shot":idx,
                "id":f"scene_{scene['scene']:02d}_shot_{idx:02d}",
                "seconds":SECONDS_PER_SHOT,
                "expected_speaker":scene["character_id"],
                "prompt":prompt,
                "seed":20261119 + 101*scene["scene"] + idx,
                "source_kind":source_kind,
                "reference_source":("approved_firestorm" if scene["scene"] <= 6 else "original_ember"),

            })
    if len(shots)!=TOTAL:
        raise RuntimeError("SHOT_COUNT_INCONSISTENT")
    return shots


def empty_state():
    return {
        "schema":"nightfall-real-AI-draft-queue-v1",
        "episode":"S01_the_last_little_fox_E01",
        "status":"NOT_STARTED",
        "model":SPACE,
        "api":API,
        "draft_release_tag":RELEASE_TAG,
        "target_shots":TOTAL,
        "completed_technical_shots":[],
        "rejected_raw_shots":[],
        "visual_owner_approved_shots":[],
        "automatic_best_candidates":{},
        "last_attempt_cairo_date":None,
        "last_attempt_result":None,
        "one_time_manual_extra_ids":[],
        "attempts_this_run":0,
        "only_free_anonymous_ZeroGPU":True,
        "paid_inference_requests":0,
        "completed_original_soundtrack_available":True,
        "lip_sync_verified":False,
        "film_180s_complete":False,
        "public_uploads":False,
    }


def draft_release_available():
    result=exec_cli(["gh","release","view",RELEASE_TAG,"--repo",REPO,
                     "--json","isDraft","--jq",".isDraft"],allowed_fail=True)
    if result.returncode:
        return False
    if result.stdout.strip().lower()!="true":
        raise RuntimeError("REFUSE_NON_DRAFT_RELEASE_PUBLIC_EXPOSURE")
    return True


def ensure_private_draft():
    if draft_release_available():
        return
    exec_cli(["gh","release","create",RELEASE_TAG,
              "--repo",REPO,"--target","main","--draft",
              "--title","Nightfall E01 — PRIVATE unapproved real AI motion dailies",
              "--notes","Draft staging only: each clip is unapproved 4s genuine "
                        "AI scene footage. No public release, no owner approval."])
    if not draft_release_available():
        raise RuntimeError("FAILED_TO_CREATE_PRIVATE_GITHUB_DRAFT_RELEASE")


def state_path():
    OUT.mkdir(parents=True,exist_ok=True)
    return OUT/"studio_state.json"


def read_state():
    state=empty_state()
    if not draft_release_available():
        return state
    local=state_path()
    if local.exists():
        local.unlink()
    r=exec_cli(["gh","release","download",RELEASE_TAG,
                "--repo",REPO,"--pattern","studio_state.json",
                "--dir",str(OUT)],allowed_fail=True)
    if not local.exists():
        return state
    remote=json.loads(local.read_text(encoding="utf-8"))
    if remote.get("episode")!=state["episode"] or remote.get("schema")!=state["schema"]:
        raise RuntimeError("DRAFT_STATE_SCHEMA_OR_EPISODE_MISMATCH")
    if remote.get("paid_inference_requests")!=0 or remote.get("public_uploads") is not False:
        raise RuntimeError("DRAFT_STATE_BUDGET_OR_PUBLICATION_VIOLATION")
    seen=set()
    for shot in remote.get("completed_technical_shots",[]):
        if shot["id"] in seen or not shot.get("sha256"):
            raise RuntimeError("DUPLICATE_OR_HASHLESS_DRAFT_STATE")
        seen.add(shot["id"])
    return remote


def persist_state(state):
    if not draft_release_available():
        raise RuntimeError("CANNOT_PERSIST_TO_NON_DRAFT_RELEASE")
    p=state_path()
    p.write_text(json.dumps(state,indent=2)+"\n",encoding="utf-8")
    exec_cli(["gh","release","upload",RELEASE_TAG,str(p),
              "--clobber","--repo",REPO])



def reconcile_visual_rejections(state):
    """Preserve a visibly bad raw clip as evidence, but never call it progress.

    Review notes are exact-shot SHA-locked and checked into this repo.
    This doesn't grant approval and doesn't permit another attempt today.
    """
    if not VISUAL_REJECTIONS.is_file():
        return False
    items=json.loads(VISUAL_REJECTIONS.read_text(encoding="utf-8"))
    changed=False
    for rejection in items.get("rejections",[]):
        cid=rejection["clip_id"]
        digest=rejection["sha256"]
        for clip in list(state["completed_technical_shots"]):
            if clip["id"] != cid:
                continue
            if clip["sha256"] != digest:
                # Same scene ID can have multiple versions. A rejection of
                # v1 must never abort v2 or v3 daily production; match on BOTH
                # logical shot and exact SHA, and ignore unrelated versions.
                continue
            state["completed_technical_shots"].remove(clip)
            entry=dict(clip)
            entry["visual_review"]="REJECTED"
            entry["reasons"]=rejection["reasons"]
            state.setdefault("rejected_raw_shots",[]).append(entry)
            changed=True
    return changed


def media_metadata(path):
    raw=subprocess.run(["ffprobe","-v","error","-of","json",
       "-show_entries","format=duration:stream=codec_type,codec_name,width,height",
       str(path)],capture_output=True,text=True,check=True,timeout=30)
    j=json.loads(raw.stdout)
    v=next((s for s in j["streams"] if s.get("codec_type")=="video"),None)
    if not v:
        raise RuntimeError("OUTPUT_NOT_A_VIDEO")
    d=float(j["format"]["duration"])
    if not (3.90<=d<=5.25):
        raise RuntimeError("REAL_MODEL_SHOT_DURATION_NOT_FOUR_SECONDS")
    w=int(v["width"]);h=int(v["height"])
    if w<384 or h<576 or h<=w:
        raise RuntimeError("REAL_MODEL_SHOT_NOT_PORTRAIT_OR_TOO_SMALL")
    return {"seconds":round(d,3),"width":w,"height":h,
            "codec":v["codec_name"],"sha256":sha(path)}


def motion_qa(path):
    result=subprocess.run(
        ["ffmpeg","-nostdin","-hide_banner","-i",str(path),
         "-vf","blackdetect=d=0.28:pix_th=0.12,freezedetect=n=-55dB:d=1.35",
         "-an","-f","null","-"],
        capture_output=True,text=True,timeout=95
    )
    if result.returncode or "black_start:" in result.stderr or "freeze_start:" in result.stderr:
        raise RuntimeError("RENDERED_CLIP_HAS_BLACK_OR_FROZEN_GAPS")
    return True


def generate_once(shot):
    # LTX-2.3 model is confirmed available through this one no-fee public Space;
    # if access/credits have changed, fail CLOSED without trying paid providers.
    from gradio_client import Client,handle_file
    client=Client(SPACE,verbose=False)
    exposed={str(e.api_name) for e in client.endpoints.values()}
    if API not in exposed:
        raise RuntimeError("LTX_PUBLIC_ZERO_GPU_ENDPOINT_CHANGED")
    result=client.predict(
        handle_file(str((FIRE_REFERENCE if shot.get("reference_source")=="approved_firestorm" else EMBER).resolve())),shot["prompt"],
        4.0,False,shot["seed"],False,768,512,api_name=API
    )
    candidate=result[0] if isinstance(result,(tuple,list)) else result
    if isinstance(candidate,dict):
        candidate=candidate.get("video") or candidate.get("path")
    if not isinstance(candidate,str) or not Path(candidate).is_file():
        raise RuntimeError("FREE_PROVIDER_RETURNED_NO_REAL_VIDEO")
    stem=shot.get("asset_stem",shot["id"])
    media=OUT/(stem+".mp4")
    shutil.copyfile(candidate,media)
    if media.stat().st_size < 10000:
        raise RuntimeError("FREE_PROVIDER_RETURNED_EMPTY_VIDEO")
    technical=media_metadata(media)
    motion_qa(media)
    # A frame-contact sheet is an EVIDENCE artifact, not cinematic approval.
    sheet=OUT/(stem+"_4frames.jpg")
    subprocess.run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error",
      "-y","-i",str(media),"-vf","fps=1,scale=256:-1,tile=4x1",
      "-frames:v","1",str(sheet)],check=True,timeout=75)
    return media,sheet,technical


def clip_in_draft(name):
    r=exec_cli(["gh","release","view",RELEASE_TAG,"--repo",REPO,
             "--json","assets","--jq",".assets[].name"])
    return name in set(r.stdout.splitlines())


def run(mode):
    shots=plan()
    OUT.mkdir(parents=True,exist_ok=True)
    if mode=="audit":
        state=empty_state()
        state["status"]="LOCAL_STORY_AND_45_SHOT_PLAN_VALIDATED_NO_GPU_CALLED"
        state_path().write_text(json.dumps(state,indent=2)+"\n")
        print("NIGHTFALL_STUDIO_AUDIT_ONLY",len(shots),flush=True)
        return state
    guarantee_zero_paid_inference()
    if not os.getenv("GH_TOKEN") and not os.getenv("GITHUB_TOKEN"):
        raise RuntimeError("GH_TOKEN_REQUIRED_FOR_PRIVATE_DRAFT_STORAGE")
    ensure_private_draft()
    state=read_state()
    state.setdefault("automatic_best_candidates",{})
    state.setdefault("rejected_raw_shots",[])
    if reconcile_visual_rejections(state):
        persist_state(state)
        print("REJECTED_UNAPPROVED_BAD_VIDEO_NOT_COUNTED_AS_PROGRESS",flush=True)
    valid_ids={s["id"] for s in shots}
    rejected_ids={x["id"] for x in state.get("rejected_raw_shots",[])}
    for shot_id,record in list(state["automatic_best_candidates"].items()):
        if not any(x["id"]==shot_id and x.get("sha256")==record.get("sha256")
                   for x in state["completed_technical_shots"]):
            state["automatic_best_candidates"].pop(shot_id,None)
    completed={s["id"] for s in state["completed_technical_shots"]}
    if not completed.issubset(valid_ids):
        raise RuntimeError("DRAFT_CONTAINS_UNRECOGNIZED_SHOTS")
    remaining=[s for s in shots if s["id"] not in completed]
    # A fox source image must NEVER be used to pretend a tortoise has
    # identity consistency. Continue the Ember-only shots, but leave
    # original Moss scenes blocked until a proper approved Moss reference.
    eligible=[s for s in remaining if s["source_kind"]=="ember"]
    if remaining and not eligible:
        state["status"]="BLOCKED_MOSS_APPROVED_REFERENCE_REQUIRED"
        persist_state(state)
        print("NO_FALSE_MOSS_REFERENCE_SUBSTITUTION",flush=True)
        return state
    if not remaining:
        state["status"]="ALL_RAW_SHOTS_CAPTURED_OWNER_QA_AND_LIPSYNC_PENDING"
        print("ALL_45_RAW_MOTION_CLIPS_ACQUIRED_FINAL_APPROVAL_PENDING",flush=True)
        persist_state(state)
        return state
    today=now_cairo().date().isoformat()
    owner_extra_id=os.getenv("SINGLE_USE_OWNER_EXTRA_ID","")
    owner_authorized_extra=(
        owner_extra_id=="owner_2026_11_19_one_extra_4s"
        and today=="2026-11-19"
        and os.getenv("GITHUB_EVENT_NAME")=="push"
        and owner_extra_id not in state.get("one_time_manual_extra_ids",[])
    )
    if state.get("last_attempt_cairo_date")==today and not owner_authorized_extra:
        state["status"]="ALREADY_TRIED_ONE_FREE_GPU_CALL_TODAY"
        print("NO_UNAUTHORIZED_SECOND_FREE_QUOTA_ATTEMPT_TODAY",flush=True)
        return state
    current=dict(eligible[0])
    rejected_count=sum(1 for x in state.get("rejected_raw_shots",[])
                       if x["id"]==current["id"])
    current["asset_stem"]=(current["id"] if rejected_count==0 else
                           current["id"]+f"_revision_{rejected_count+1}")
    if clip_in_draft(current["asset_stem"]+".mp4"):
        raise RuntimeError("DRAFT_HAS_ORPHAN_CLIP_MANUAL_RECONCILIATION_REQUIRED")
    state["last_attempt_cairo_date"]=today
    state["attempts_this_run"]=1
    if owner_authorized_extra:
        # Explicit one-time owner request: allow ONE additional anonymous,
        # non-billable trial on this exact Cairo date. Never retry automatically
        # or renew the extra authorization on future days.
        state.setdefault("one_time_manual_extra_ids",[]).append(owner_extra_id)
    state["status"]=("ONE_TIME_OWNER_EXTRA_FREE_GPU_REQUEST_SUBMITTED" if owner_authorized_extra
                     else "FREE_GPU_REQUEST_SUBMITTED")
    persist_state(state)  # Persist nonce BEFORE network inference.
    try:
        movie,sheet,metadata=generate_once(current)
        from pilot.e01_auto_quality import score_clip
        quality=score_clip(movie)
        item={k:current[k] for k in ("scene","shot","id","seconds")}
        item.update(metadata)
        item["asset_stem"]=current["asset_stem"]
        item.update({"human_visual_approval":False,
                     "original_Kokoro_speech_lipsync_approved":False,
                     "source_ember_sha256":EMBER_SHA,
                     "actual_i2v_source_sha256":(FIRE_REFERENCE_SHA if current.get("reference_source")=="approved_firestorm" else EMBER_SHA),
                     "actual_i2v_source_type":current.get("reference_source"),
                     "made_by_real_video_model":True,
                     "no_public_post":True,
                     "automatic_quality":quality})
        proof=OUT/(current["asset_stem"]+".json")
        proof.write_text(json.dumps(item,indent=2)+"\n",encoding="utf-8")
        # Capture genuine media even if automated evidence-based metrics are
        # poor; rejected candidates are retained in the owner-only draft.
        for path in (movie,sheet,proof):
            exec_cli(["gh","release","upload",RELEASE_TAG,str(path),"--repo",REPO])
        if quality["passes_basic_machine_motion_gate"]:
            state["status"]="AUTO_SHORTLISTED_TECHNICAL_MOTION_NOT_SEMANTICALLY_APPROVED"
            state["last_attempt_result"]="REAL_MP4_SAVED_AND_AUTO_RANKED"
            best=state.setdefault("automatic_best_candidates",{})
            prior=best.get(current["id"])
            if not prior or quality["score_0_to_100"]>prior.get("score",0):
                best[current["id"]]={"asset_stem":current["asset_stem"],
                       "sha256":metadata["sha256"],
                       "score":quality["score_0_to_100"],
                       "public_approved":False,
                       "lip_sync_verified":False}
            state["completed_technical_shots"].append(item)
        else:
            state["status"]="AUTO_REJECTED_WEAK_MOTION_OR_FRAMING"
            state["last_attempt_result"]="MP4_REJECTED_BY_TECHNICAL_QA"
            rejected=dict(item)
            rejected["visual_review"]="AUTO_REJECTED_NON_SEMANTIC_QA"
            rejected["reasons"]=quality["machine_flags"] or ["QUALITY_SCORE_BELOW_MINIMUM"]
            state.setdefault("rejected_raw_shots",[]).append(rejected)
    except Exception as e:
        reason=str(e).lower()
        denied=any(pattern in reason for pattern in QUOTA_ERRORS)
        state["status"]=("BLOCKED_FREE_ZEROGPU_QUOTA_NEXT_DAY"
                         if denied else "PROVIDER_OR_MEDIA_FAILURE_NO_FALLBACK")
        state["last_attempt_result"]=type(e).__name__
        state["last_error_redacted"]=str(e)[:250]
        print("::warning title=No cinema video uploaded::"
              +state["status"]+"; no GPU retry or paid service",flush=True)
    state["paid_inference_requests"]=0
    state["public_uploads"]=False
    state["film_180s_complete"]=False
    persist_state(state)
    print("NIGHTFALL_E01_REAL_AI_STUDIO_STATUS",state["status"],
          "raw_shots",len(state["completed_technical_shots"]),"of",TOTAL,flush=True)
    return state


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--mode",choices=("audit","generate"),default="audit")
    cfg=parser.parse_args()
    run(cfg.mode)
