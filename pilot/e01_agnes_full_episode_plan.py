"""Fresh, canon-locked 3–6 minute E01 Agnes Flash cinematic shot plan.

The original six Hugging Face clips remain archived UNMODIFIED. This is a
completely fresh film, independent of its old 36-shot HF checkpoint/plan hash.
Exactly 18 real 12-second video tasks = 216 seconds before audio integration.

The story, cast, reference image SHA-256 and Kokoro voice IDs are authoritative.
A prepared plan is NEVER evidence of generated video, expressive acting,
true lip-sync, no-charge eligibility, or successful social publishing.
"""
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import quote

from pilot import e01_full_run as film
from studio.continuity import sha256
from studio.real_film import character_image

MODEL = "agnes-video-2.5-flash"
SCHEMA = "nightfall-e01-agnes-fresh-v1"
MIN_DURATION = 180
MAX_DURATION = 360
SHOT_SECONDS = 12
EPISODE = film.EPISODE
SERIES = film.SERIES
REPO = "FadyIasaad/Nightfall-Diaries"


def pinned_url(path, revision):
    if (not isinstance(revision, str) or len(revision) != 40
            or any(c not in "0123456789abcdef" for c in revision)):
        raise ValueError("Immutable source commit SHA required")
    path = Path(path)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError("Unsafe reference file path")
    return ("https://raw.githubusercontent.com/" + REPO + "/" + revision + "/"
            + "/".join(quote(x, safe="") for x in path.parts))


def check_ref(path):
    path = Path(path)
    if not path.is_file():
        raise RuntimeError("Locked original character image missing")
    return sha256(path)


def make_plan(revision):
    cast, old_pilot = film.scene_plan()
    scenes = old_pilot["scenes"]
    if len(scenes) != 14 or old_pilot["episode"] != EPISODE:
        raise RuntimeError("Unrecognized original E01 cinematic screenplay")
    # Extra independent action beats in the longest scenes. No loops, zooms
    # or reuse of previous output is allowed; each is a NEW inference task.
    expansions = {s["scene_no"] for s in sorted(
        scenes, key=lambda s: (-len(s["script_text"].split()), s["scene_no"])
    )[:4]}
    shots = []
    for scene in scenes:
        visible = scene["visible"]
        if not visible or scene["speaker"] not in cast:
            raise RuntimeError("Original cast metadata missing")
        refs = []
        # Lead reference is the approved 2026-11-13 CGI Ember when Ember leads.
        lead = Path(film.ROOT / scene["reference_file"])
        refs.append({
            "character": scene["visual_lead"],
            "url": pinned_url(lead.relative_to(film.ROOT), revision),
            "sha256": check_ref(lead),
        })
        for character_id in visible:
            if character_id == scene["visual_lead"]:
                continue
            path = character_image(SERIES, character_id)
            refs.append({
                "character": character_id,
                "url": pinned_url(path.relative_to(film.ROOT), revision),
                "sha256": check_ref(path),
            })
        if len(refs) > 5:
            raise RuntimeError("Agnes Flash supports no more than five image references")
        count = 2 if scene["scene_no"] in expansions else 1
        for part in range(1, count + 1):
            action = (
                "Begin the scripted scene with original new character motion."
                if part == 1 else
                "Different original action beat and different camera angle, "
                "continue the same story without replaying or slowing any earlier footage."
            )
            shot_number = len(shots) + 1
            shots.append({
                "index": shot_number, "scene": scene["scene_no"], "part": part,
                "duration_seconds": SHOT_SECONDS, "speaker": scene["speaker"],
                "voice_id": scene["voice_id"], "text": scene["script_text"],
                "visible_characters": visible,
                "images": [x["url"] for x in refs],
                "reference_hashes": refs,
                "prompt": (
                    "Cinematic 3D stylized animation with moving articulated characters, "
                    "rich detailed fur, expressive eye/ear/limb acting, continuous grounded "
                    "motion and film-quality lighting, portrait 9:16 composition. "
                    "Maintain each pictured character's exact design, no morphing or extra "
                    "scarf stars. No photo slideshow or still-camera zoom. "
                    + action + " " + scene["ai_motion_prompt"]
                ),
                "requires_qa": True,
            })
    duration = len(shots) * SHOT_SECONDS
    if len(shots) != 18 or not MIN_DURATION <= duration <= MAX_DURATION:
        raise RuntimeError("Fresh E01 Agnes plan violates owner's 3–6 minute duration")
    core = {
        "schema": SCHEMA, "episode": EPISODE, "series": SERIES,
        "reference_revision": revision, "model": MODEL,
        "shots": shots, "target_seconds": duration,
        "original_story_files_unmodified": True,
    }
    digest = hashlib.sha256(json.dumps(core, sort_keys=True).encode()).hexdigest()
    return {
        **core, "plan_sha256": digest,
        "total_new_shots": len(shots), "existing_old_hf_clips_reused": 0,
        "voice_scene_count": len(scenes),
        "api_generation_requests_made": 0,
        "true_lipsync_approved": False,
        "cinematic_quality_approved": False,
        "automatic_public_publishing_authorized": False,
        "zero_charge_account_verified": False,
        "status": "FRESH_216_SECOND_PLAN_ONLY",
    }


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="output/agnes_e01/shot_plan.json")
    parser.add_argument("--reference-commit", default=os.environ.get("GITHUB_SHA", ""))
    args = parser.parse_args()
    result = make_plan(args.reference_commit)
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("AGNES_FRESH_E01_PLAN", json.dumps({
        key: result[key] for key in
        ("status", "total_new_shots", "target_seconds", "api_generation_requests_made",
         "automatic_public_publishing_authorized")
    }))


if __name__ == "__main__":
    main()
