"""Render real original Kokoro E02 scene-dialogue WAVs on free Github CPU.

One independent voice per canonical character. No robo fallback, no speech
speed-up, no public uploads, and no claims of a completed movie.
"""
import json
import os
import subprocess
from pathlib import Path
from studio.continuity import sha256

ROOT=Path(__file__).resolve().parents[1]
SCREENPLAY=ROOT/"seasons/S01_the_last_little_fox/revised_screenplays/E02_2026-11-18.json"
CAST=ROOT/"seasons/S01_the_last_little_fox/characters/character_registry.json"
OUT=ROOT/"output/e02_kokoro_original_voice_cues"

def seconds(path):
    p=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                       "-of","default=noprint_wrappers=1:nokey=1",str(path)],
                     capture_output=True,text=True,check=True,timeout=30)
    return float(p.stdout)

def run():
    if any(os.getenv(name) for name in ("ELEVENLABS_API_KEY","OPENAI_API_KEY",
                                           "RUNWAY_API_KEY","AGNES_API_KEY")):
        raise RuntimeError("NO_PAID_TTS_PROVIDER_KEYS_ALLOWED")
    screenplay=json.loads(SCREENPLAY.read_text(encoding="utf-8"))
    actors={x["id"]:x for x in json.loads(CAST.read_text(encoding="utf-8"))["characters"]}
    if screenplay["episode_id"]!="S01_the_last_little_fox_E02" or len(screenplay["scenes"])!=15:
        raise RuntimeError("INCORRECT_E02_REVISION")
    OUT.mkdir(parents=True,exist_ok=True)
    from studio.neural_audio import render_kokoro
    records=[]
    for scene in screenplay["scenes"]:
        no=scene["scene_no"]
        person=actors[scene["character_id"]]
        voice=person["voice"]
        if voice["engine"]!="kokoro" or voice["voice_id"]!=scene["voice_id"]:
            raise RuntimeError("VOICE_CAST_IDENTITY_DRIFT")
        destination=OUT/f"scene_{no:02d}_{scene['character_id']}.wav"
        if not destination.is_file():
            render_kokoro(scene["script_text"],person,destination)
        duration=seconds(destination)
        if not .3<duration<=scene["seconds"]:
            raise RuntimeError(f"SCENE_{no:02d}_VOICE_OVERFLOW_{duration:.2f}_s")
        records.append({"scene":no,"speaker":scene["character_id"],
                        "voice_id":voice["voice_id"],"file":destination.name,
                        "sha256":sha256(destination),
                        "duration":round(duration,3),"scene_window":scene["seconds"],
                        "remaining_seconds_reserved_for_animated_action":
                            round(scene["seconds"]-duration,3)})
        print("REAL_NEURAL_VOICE",no,round(duration,2),flush=True)
    report={"episode":screenplay["episode_id"],"engine":"local_Kokoro_CPU_0_dollar",
            "scene_count":len(records),"records":records,
            "voice_quality_owner_approved":False,
            "actual_lipsync_generated":False,
            "full_episode_completed":False,
            "public_upload_attempted":False}
    (OUT/"voice_cue_manifest.json").write_text(json.dumps(report,indent=2)+"\n")
    return report

if __name__=="__main__":
    run()
