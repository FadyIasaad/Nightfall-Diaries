"""Canonical first pilot expands story while leaving every original dialogue line untouched."""
import json
import unittest
from studio.restore import ROOT
from studio.screenplay import load_screenplay

class ScreenplayTests(unittest.TestCase):
    def test_first_episode_is_complete_draft(self):
        ep="S01_the_last_little_fox_E01"
        screenplay=load_screenplay(ep)
        self.assertEqual(len(screenplay["scenes"]), 20)
        self.assertEqual(screenplay["episode_id"], ep)
        self.assertEqual(screenplay["production_status"], "SCREENPLAY_DRAFT_NOT_RENDERED")
        words=sum(len(scene["text"].split()) for scene in screenplay["scenes"])
        self.assertGreaterEqual(words, 400)
        self.assertLessEqual(words, 750)

    def test_archive_remains_locked_four_scenes(self):
        ep="S01_the_last_little_fox_E01"
        orig=json.loads((ROOT/"seasons/S01_the_last_little_fox/scripts/E01.json").read_text())
        expanded=load_screenplay(ep)
        self.assertEqual(len(orig["scenes"]), 4)
        for source in orig["scenes"]:
            self.assertEqual(sum(
                source["text"] in x["text"] and source["character_id"]==x["character_id"]
                for x in expanded["scenes"]),1)

    def test_other_episodes_fall_back_to_original_archive(self):
        screenplay=load_screenplay("S01_the_last_little_fox_E02")
        self.assertEqual(len(screenplay["scenes"]), 4)
