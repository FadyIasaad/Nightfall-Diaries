"""Never skip unfinished episodes; move from Fox S01 to Boy S02 after 12 QA proofs."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pilot import story_one_click as story


class OriginalSeriesAutoSequenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for sid, n in ((story.CATALOG[0][0], 12),
                       (story.CATALOG[1][0], 10)):
            p = self.root / "seasons" / sid / "episodes"
            p.mkdir(parents=True)
            items = [{"id": f"{sid}_E{i:02d}"} for i in range(1, n+1)]
            (p / "episodes.json").write_text(
                json.dumps({"series_id": sid, "episodes": items}))
        self.patcher = patch.object(story, "ROOT", self.root)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def mark(self, i, good=True):
        ep = f"{story.CATALOG[0][0]}_E{i:02d}"
        d = self.root / "produced"
        d.mkdir(exist_ok=True)
        (d / (ep + ".json")).write_text(json.dumps({
            "episode_id": ep, "film_sha256": "a"*64,
            "duration_seconds": 195,
            "real_cinematic_motion_verified": good,
            "true_character_lipsync_verified": good,
            "film_quality_approved": good,
        }))

    def test_all_twelve_approved_film_episodes_auto_queue_original_second_series(self):
        for i in range(1, 13):
            self.mark(i)
        result = story.current_state(story.default())
        self.assertEqual(result["series_id"], story.CATALOG[1][0])
        self.assertEqual(result["episode_id"], story.CATALOG[1][0] + "_E01")
        self.assertTrue(result["next_series_automatically_selected"])
        self.assertEqual(result["series_completed_before_current"],
                         ["The Last Little Fox"])
        # The second renderer is NOT yet real/verified; never fake success.
        self.assertFalse(result["e01_free_motion_supported"])
        self.assertEqual(result["status"],
                         "BLOCKED_UNPREPARED_EPISODE_NO_GPU_NO_UPLOAD")

    def test_one_unfinished_episode_blocks_early_switch(self):
        for i in range(1, 12):
            self.mark(i)
        result = story.current_state(story.default())
        self.assertEqual(result["episode_id"],
                         story.CATALOG[0][0] + "_E12")
        self.assertFalse(result["next_series_automatically_selected"])

    def test_preview_or_missing_lipsync_cannot_skip_episode(self):
        self.mark(1, good=False)
        self.assertEqual(story.current_state(story.default())["episode_id"],
                         story.CATALOG[0][0] + "_E01")

    def test_publishing_not_required_for_sequence_only_actual_qa(self):
        for i in range(1, 13):
            self.mark(i)
        self.assertFalse((self.root / "published").exists())
        self.assertEqual(story.current_state(story.default())["series_id"],
                         story.CATALOG[1][0])


if __name__ == "__main__":
    unittest.main()
