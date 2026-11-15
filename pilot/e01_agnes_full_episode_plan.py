"""Conservative read-only E01 Agnes migration plan, preserving proven real MP4 footage.

Agnes Flash supports 4-12 second genuine video requests. To avoid abandoning
six SHA-verified clips or changing the original HF plan digest, this file builds
an INDEPENDENT candidate sequence: first six authentic clips from scenes 1-2
(24.25s measured), then twelve 12s story beats and three additional 6s story
beats across the remaining twelve scripted scenes. About 186s total; exact
final length comes from ffprobe, and actual cinematic/lipsync QA remains required.

This module NEVER submits a video request, buys GPU, changes a story, or posts.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import quote

from pilot import e01_full_run as film
from pilot import e01_free_resume as old
from studio.continuity import sha256

SCHEMA = "nightfall-e01-agnes-migration-v1"
MODEL = "agnes-video-2.5-flash"
OWNER_MIN_SECONDS = 180
OWNER_MAX_SECONDS = 360
OLD_PREFIX = ((1, 1), (1, 2), (1, 3), (2, 1), (2, 2), (2, 3))
DEFAULT_OUT = Path("output/e01_agnes_migration/plan.json")
REPO = "FadyIasaad/Nightfall-Diaries"


def pinned_reference(path, revision):
    if not revision or len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision):
        raise ValueError("Immutable 40-character commit required for public reference URL")
    relative = Path(path)
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise ValueError("Unsafe reference path")
    return "https://raw.githubusercontent.com/" + REPO + "/" + revision + "/" + "/".join(
        quote(part, safe="") for part in relative.parts
    )


def make_plan(original, old_state, base_dir, revision):
    """All existing MP4s must pass original plan digest AND per-file SHA-256."""
    if (original.get("episode") != film.EPISODE or len(original.get("scenes", [])) != 14):
        raise RuntimeError("Unexpected original episode or screenplay; no migration")
    if (old_state.get("schema") != old.VERSION
            or old_state.get("episode") != film.EPISODE
            or old_state.get("plan_sha256") != old.plan_digest(original)):
        raise RuntimeError("Old production fingerprint mismatch; preserve original footage")
    records = old_state.get("completed", [])
    if {(row.get("scene"), row.get("part")) for row in records} != set(OLD_PREFIX) or len(records) != 6:
        raise RuntimeError("Original completed shots changed: review new state, do not discard footage")
    base_dir = Path(base_dir)
    preserved = []
    for scene_id, part_id in OLD_PREFIX:
        row = next(row for row in records if (row["scene"], row["part"]) == (scene_id, part_id))
        name = row.get("file", "")
        if (not isinstance(name, str) or Path(name).name != name
                or not name.startswith(f"scene_{scene_id:02d}_part_{part_id:02d}_")
                or not name.endswith(".mp4")):
            raise RuntimeError("Unsafe original video file in checkpoint")
        file = base_dir / name
        if not file.is_file() or sha256(file) != row["sha256"]:
            raise RuntimeError("Original video missing/SHA mismatch; do not re-render over it")
        duration = float(row.get("seconds", 0))
        if not 2 <= duration <= 5.5:
            raise RuntimeError("Invalid actual original sub-shot length")
        preserved.append({
            "scene": scene_id, "part": part_id, "file": name,
            "sha256": row["sha256"], "actual_seconds": duration,
            "engine": "Lightricks/LTX-2.5", "origin": "original_sha_verified_checkpoint",
        })
    remaining = original["scenes"][2:]
    # Longer scripted dialogue/action gets a second real, independently
    # generated 6-second shot, NOT a copy/loop/slowdown.
    long_scenes = {item["scene_no"] for item in sorted(
        remaining,
        key=lambda x: (-len(x["script_text"].split()), x["scene_no"])
    )[:3]}
    generated = []
    for scene in remaining:
        no = scene["scene_no"]
        if not 3 <= no <= 14:
            raise RuntimeError("Unexpected scene order in original screenplay")
        rel = scene["reference_file"]
        expected = scene["reference_sha256"]
        reference = film.ROOT / rel
        if not reference.is_file() or sha256(reference) != expected:
            raise RuntimeError("Original cast image fingerprint changed")
        ref_url = pinned_reference(rel, revision)
        chunks = [12, 6] if no in long_scenes else [12]
        for part, seconds in enumerate(chunks, 1):
            prefix = ("First authentic cinematic action beat." if part == 1
                      else "Second DIFFERENT story action beat; cut to a new angle, "
                           "no repeating the first action.")
            generated.append({
                "scene": no, "part": part, "seconds": seconds,
                "model": MODEL, "mode": "reference", "size": "720P",
                "aspect_ratio": "9:16", "image_url": ref_url,
                "reference_sha256": expected, "character_id": scene["visual_lead"],
                "script_speaker": scene["speaker"], "voice_id": scene["voice_id"],
                "prompt": prefix + " " + scene["ai_motion_prompt"],
                "requires_visual_and_lipsync_qa": True,
            })
    duration = round(sum(x["actual_seconds"] for x in preserved)
                     + sum(x["seconds"] for x in generated), 3)
    if not OWNER_MIN_SECONDS <= duration <= OWNER_MAX_SECONDS:
        raise RuntimeError("Episode shorter/longer than user's 3-6 minute specification")
    identity = {
        "schema": SCHEMA, "episode": film.EPISODE,
        "old_plan_sha256": old_state["plan_sha256"],
        "original_screenplay_sha256": hashlib.sha256(json.dumps(
            [{"scene": s["scene_no"], "script_text": s["script_text"],
              "voice_id": s["voice_id"], "reference_sha256": s["reference_sha256"]}
             for s in original["scenes"]], sort_keys=True).encode()).hexdigest(),
        "reference_revision": revision, "preserved": preserved,
        "new_ai_shots": generated,
    }
    digest = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    return {
        **identity, "plan_sha256": digest,
        "existing_clips_preserved": len(preserved),
        "new_agnes_requests_planned": len(generated),
        "expected_unique_motion_shots": len(preserved) + len(generated),
        "existing_real_motion_seconds": round(sum(x["actual_seconds"] for x in preserved), 3),
        "planned_new_real_motion_seconds": sum(x["seconds"] for x in generated),
        "projected_episode_seconds": duration,
        "original_22_episode_story_archive_changed": False,
        "original_existing_checkpoint_changed": False,
        "true_character_lipsync_verified": False,
        "cinematic_quality_approved": False,
        "public_publishing_authorized": False,
        "price_and_account_type_authorized": False,
        "api_requests_sent": 0,
        "status": "SHA_VERIFIED_186S_AGNES_SEQUENCE_PLAN_ONLY",
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", default=str(DEFAULT_OUT))
    p.add_argument("--checkpoint-dir", default=str(old.OUT))
    p.add_argument("--reference-commit", default=os.getenv("GITHUB_SHA", ""))
    args = p.parse_args()
    _, original = film.scene_plan()
    state_file = Path(args.checkpoint_dir) / "progress.json"
    if not state_file.is_file():
        raise SystemExit("No genuine E01 checkpoint restored. No new requests or fake clips.")
    old_state = json.loads(state_file.read_text(encoding="utf-8"))
    report = make_plan(original, old_state, args.checkpoint_dir, args.reference_commit)
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("NIGHTFALL_AGNES_EPISODE_PLAN", json.dumps({
        k: report[k] for k in ("status", "existing_clips_preserved",
                               "new_agnes_requests_planned", "projected_episode_seconds",
                               "api_requests_sent", "public_publishing_authorized")
    }))


if __name__ == "__main__":
    main()
