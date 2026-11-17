"""Isolated cinematic V4 candidate; preserves prior V4 clean shell and V1-3."""
import json

from pilot import e01_director_v2 as engine
from studio import e01_v4_art_direction as art


def main():
    engine.VERSION = "nightfall-e01-v4-cinematic-painterly-composition-20261117"
    engine.OUT = engine.ROOT / "output/nightfall_e01_v4_cinematic"
    engine.STATE = engine.OUT / "progress.json"
    engine.FINAL = engine.OUT / "Nightfall_S01_E01_V4_Cinematic_Painterly_180s_REVIEW.mp4"
    engine.frame = art.frame
    engine.SETS = art.SETS
    engine.main()
    if engine.STATE.is_file():
        state = json.loads(engine.STATE.read_text(encoding="utf-8"))
        report = {
            "version": engine.VERSION,
            "status": state.get("status"),
            "completed_scenes": len(state.get("completed", [])),
            "target_seconds": 180,
            "original_story_unchanged": True,
            "original_kokoro_voices_unchanged": True,
            "approved_ember_reference_unchanged": True,
            "art_direction": [
                "14 textured and distinct story environments",
                "scene-specific camera composition",
                "warm/cool character lighting integration",
                "richer haze and physically placed magic feather",
                "small readable cinematic subtitles"
            ],
            "cinematic_3d_verified": False,
            "accurate_phoneme_lipsync_verified": False,
            "moss_matches_ember_quality_verified": False,
            "human_art_approval_pending": True,
            "public_uploads": False
        }
        (engine.OUT / "v4_review.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
