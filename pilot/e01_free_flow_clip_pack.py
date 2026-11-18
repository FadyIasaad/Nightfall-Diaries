"""Prepare E01's 30 legal free-Flow browser clip prompts; NO Flow API automation.

Google Flow free web credits cannot be asserted available in GitHub API.
Outputs script prompts and an exact 8+4s plan ONLY. No fake render/cost claim.
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCREENPLAY = ROOT/"seasons/S01_the_last_little_fox/revised_screenplays/E01_2026-11-18.json"
CAST = ROOT/"seasons/S01_the_last_little_fox/characters/character_registry.json"
OUT = ROOT/"output/e01_free_google_flow_pack"
VIDEO_MODEL = "Google Flow Veo 3.1 Lite"
DAILY_FREE_CREDITS = 50
CREDITS_PER_GENERATION = 10
SEGMENTS = (8, 4)
SOURCE = (
    "Google Flow official free 50/day: https://support.google.com/flow/answer/16526234 ; "
    "Egypt supported: https://support.google.com/flow/answer/16353544"
)
STYLE = (
    "Original high-end stylized 3D animated family-drama film. "
    "An immersive real full-scene forest environment: dense layered trunks, "
    "mist and smoke volumetrics, tangible ground cover, cinematic rim light, "
    "detailed tactile bark/soil/ferns, physically grounded shadows. "
    "Maintain a coherent single 3D camera perspective between every actor, "
    "foreground, and background. Character acts naturally with grounded body "
    "movement and emotional micro-gestures, not a still-panned photo."
)
NO_UI = (
    "No captions, lower thirds, letterbox overlays, logos, watermark, fake "
    "phone UI, icons, dialogue cards, subtitles, game interface, repetitive "
    "fake movement, spinning stationary character, black/silent gap, or cutout puppets."
)


def build():
    data=json.loads(SCREENPLAY.read_text(encoding="utf-8"))
    cast={c["id"]:c for c in json.loads(CAST.read_text(encoding="utf-8"))["characters"]}
    scenes=data["scenes"]
    if data["episode_id"]!="S01_the_last_little_fox_E01":
        raise RuntimeError("ONLY_ORIGINAL_REVISED_E01_ALLOWED")
    if len(scenes)!=15 or data["target_duration_seconds"]!=180:
        raise RuntimeError("SCENES_NOT_FINAL_15x12S")
    shots=[]
    for scene in scenes:
        if scene["shot_seconds"] != [4,4,4] or scene["target_seconds"]!=12:
            raise RuntimeError("ORIGINAL_45_SHOT_CANON_TIMELINE_CHANGED")
        visible=scene["visible"]
        appearances=" ".join(cast[x]["visual"] for x in visible if x in cast)
        if not appearances or not scene["direction"]:
            raise RuntimeError("MISSING_SCENE_VISUALS")
        speaking=scene["character_id"]!="s01_narrator"
        for subidx, secs in enumerate(SEGMENTS,1):
            phase=("Start with the complete cinematic setting, then enact the "
                   "physical action and a motivated camera move across this shot."
                   if subidx==1 else
                   "Start from the FINAL real frame of the previous 8-second shot "
                   "when the Flow interface supports frames-to-video, and complete "
                   "the physical action with a meaningful reaction or reveal. "
                   "Do not reset position or replay the opening. ")
            spoken=(f"Scene's exact script line (for voice/muzzle performance guidance only): "
                    f"{scene['text']!r}. The original Kokoro cast WAV is authoritative; "
                    "Flow has NOT been verified to accept or match the external WAV. "
                    "Do not claim accurate audio-to-mouth synchronization before review."
                    if speaking else
                    "Only natural environment sound, no invented narrator talking. "
                    "The original Kokoro narration soundtrack will be attached in editing.")
            prompt=(f"{STYLE} Characters: {appearances} "
                    f"Scene {scene['scene']:02d}, {scene['beat']}. "
                    f"Directed story action: {scene['direction']} "
                    f"{phase} {spoken} {NO_UI} "
                    "Preserve Ember white-tipped LEFT ear, teal scarf and EXACTLY "
                    "ONE gold star whenever Ember is visible; Moss has NO glasses "
                    "and the correct weathered shell spiral/crack when he appears. "
                    "No sudden character redesign, extra limbs, swapped clothing "
                    "or arbitrary new props.")
            shots.append({
                "scene":scene["scene"],
                "part":subidx,
                "seconds":secs,
                "clip_id":f"scene_{scene['scene']:02d}_flow_{subidx:02d}",
                "scene_beat":scene["beat"],
                "actor_ids":visible,
                "speaker":scene["character_id"],
                "required_original_dialogue":scene["text"],
                "voice_synchronization_verified":False,
                "scene_description":scene["direction"],
                "prompt":prompt,
                "cost_estimate_in_FREE_FLOW_CREDITS":CREDITS_PER_GENERATION,
                "USD_or_paid_API_charge_allowed":False,
                "rendered":False,
                "visual_approved":False,
                "requires_original_approved_reference":True,
            })
    total=sum(x["seconds"] for x in shots)
    credit_total=len(shots)*CREDITS_PER_GENERATION
    if total!=180 or len(shots)!=30:
        raise RuntimeError("CLIP_PLAN_NOT_180S_OR_30_SHOTS")
    result={
        "project":"Nightfall Diaries S01 E01 original rework",
        "status":"PROMPT_PACK_PREPARED_NO_VIDEO_GENERATED",
        "official_free_flow_help":SOURCE,
        "model":VIDEO_MODEL,
        "engine_input_type":"Flow website; NOT a verified GitHub-compatible free API",
        "fully_unattended_generation":False,
        "supported_in_Egypt":True,
        "assumed_free_credits_per_day":DAILY_FREE_CREDITS,
        "credits_per_clip":CREDITS_PER_GENERATION,
        "planned_clips":len(shots),
        "planned_duration_seconds":total,
        "total_free_credits_single_successful_pass":credit_total,
        "optimistic_minimum_days_without_retakes":math.ceil(credit_total/DAILY_FREE_CREDITS),
        "actual_account_credits_unverified":True,
        "requires_flow_account_signin_and_web_operation":True,
        "recurring_cost_usd":0,
        "public_upload_permitted":False,
        "original_kokoro_soundtrack_complete":True,
        "accurate_character_lipsync_UNVERIFIED":True,
        "voice_must_be_checked_against_original_Kokoro":True,
        "actual_Flow_videos_generated":0,
        "shots":shots,
    }
    return result


def main():
    pack=build()
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"e01_30shot_free_flow_plan.json").write_text(
        json.dumps(pack,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    lines=["# Nightfall E01 — 30 Google Flow Free Veo 3.1 Lite clip prompts",
           "", "This is a PROMPT PACK, not generated video. 15 scenes × (8s+4s) = 180s.",
           "Veo 3.1 Lite is 10 FREE Flow credits per generation, free accounts 50 daily,",
           "so 30 generations theoretically require 6 days without retakes.",
           "No Flow free API has been verified; manual website or authorized Cloud Browser is required.",
           "Original cast Kokoro WAVs must still be synced and reviewed. No automatic posting.",
           ""]
    for item in pack["shots"]:
        lines += [f"## {item['clip_id']} — {item['scene_beat']} ({item['seconds']}s)",
                  "", item["prompt"],""]
    (OUT/"e01_30shot_promptbook.md").write_text(
        "\n".join(lines)+"\n",encoding="utf-8")
    print("E01_FLOW_PROMPT_PACK_PREPARED_30_SHOTS_180_SECONDS_0_PAID_API_CALLS")
    print("No video clips produced, no free-flow browser automation claimed.")
    return pack


if __name__=="__main__":
    main()
