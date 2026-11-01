"""Generate reusable character/voice/shot jobs automatically for an original episode.
This is a PREPRODUCTION pack. It cannot fake a cinematic MP4.
"""
import argparse
import json
import re
from pathlib import Path
from .restore import ROOT, validate_stories

VALID_ID = re.compile(r"^(S0[12]_[a-z_]+)_E(\d\d)$")
ALLOWED = {"S01_the_last_little_fox", "S02_the_boy_who_forgot_tomorrow"}

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def prepare(episode_id, root=ROOT):
    m = VALID_ID.fullmatch(episode_id)
    if not m or m.group(1) not in ALLOWED:
        raise ValueError("Invalid or unapproved series/episode")
    validate_stories(root)
    series, number = m.groups()
    season = root / "seasons" / series
    script = read(season / "scripts" / ("E" + number + ".json"))
    registry = read(season / "characters" / "character_registry.json")
    if script["episode_id"] != episode_id:
        raise ValueError("Wrong episode script")
    characters = {c["id"]: c for c in registry["characters"]}
    visuals = []
    voices = []
    for character in registry["characters"]:
        cid = character["id"]
        if character.get("type") != "narrator":
            visuals.append({
                "character_id": cid,
                "prompt": "Cinematic expressive animated character, consistent front, three-quarter and side views. " +
                          character["visual"] + " Keep every identity marking identical. " +
                          "Personality: " + character.get("personality", ""),
                "identity_locks": character.get("never_change", []),
                "views": ["front", "three_quarter", "side"],
                "status": "AWAITING_AUTOMATED_IMAGE_GENERATION",
            })
        voice = character.get("voice", {})
        if voice.get("voice_id"):
            voices.append({
                "character_id": cid, "engine": voice.get("engine"),
                "voice_id": voice["voice_id"], "language": voice.get("lang"),
                "speed": voice.get("speed", 1), "direction": voice.get("voice_direction", ""),
                "status": "AWAITING_AUTOMATED_VOICE_SYNTHESIS",
            })
    proof_file = root / "studio" / "proofs" / "ember_E01_proof_plan.json"
    proof = read(proof_file) if episode_id == "S01_the_last_little_fox_E01" else None
    shots = []
    if proof:
        for shot in proof["shots"]:
            source = script["scenes"][shot["script_scene_index"]]
            if shot["character_id"] != source["character_id"] or shot["dialogue_excerpt"] not in source["text"]:
                raise ValueError("Original scene proof does not match script")
            shots.append({
                "id": shot["id"], "duration_seconds": shot["seconds"],
                "speaker_id": shot["character_id"], "dialogue": shot["dialogue_excerpt"],
                "visible": shot["visible"], "cinematic_direction": shot["direction"],
                "status": "AWAITING_REAL_AI_VIDEO_GENERATION",
            })
    else:
        for index, scene in enumerate(script["scenes"], 1):
            cid = scene["character_id"]
            shots.append({
                "id": "SH%02d" % index, "duration_seconds": None,
                "speaker_id": cid, "dialogue": scene["text"],
                "visible": [] if characters[cid].get("type") == "narrator" else [cid],
                "cinematic_direction": "Story director must generate expressive, purposeful movement and cinematic staging from original dialogue and series bible.",
                "status": "AWAITING_AI_STORYBOARD_AND_REAL_VIDEO_GENERATION",
            })
    return {
        "episode_id": episode_id, "source": "tracked_original_episode",
        "status": "PREPRODUCTION_ONLY_NO_MP4",
        "automatic_cast_preparation": True,
        "automatic_voice_preparation": True,
        "per_character_manual_approval_required": False,
        "first_actual_cinematic_mp4_requires_owner_approval": True,
        "new_series_requires_owner_selection": True,
        "auto_publish_enabled": False,
        "image_video_provider": None,
        "character_jobs": visuals, "voice_jobs": voices, "shot_jobs": shots,
        "blockers": [
            "Cloud image/video provider must be integrated and tested for cinematic quality and quota",
            "Voice synthesis and sound mixing must be integrated and tested",
            "Actual animated MP4 must pass quality gate before automatic publishing",
            "Public publishing destinations must be independently verified",
        ],
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--episode", default="S01_the_last_little_fox_E01")
    parser.add_argument("--output", default="output/automated_episode_pack.json")
    args = parser.parse_args()
    pack = prepare(args.episode)
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(pack, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("AUTOPREP_READY characters=%d voices=%d shots=%d" % (
        len(pack["character_jobs"]), len(pack["voice_jobs"]), len(pack["shot_jobs"])))
    print("NO_VIDEO_RENDERED; NO_PUBLICATION_ATTEMPTED")

if __name__ == "__main__":
    main()
