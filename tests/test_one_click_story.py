"""One-click story title UX and safe continuation of actual E01 progress."""
import base64
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from pilot import story_one_click as story
from pilot import e01_free_resume as resume


class OneClickStoryTests(unittest.TestCase):
    def test_resolves_exact_story_titles_and_arabic_aliases(self):
        a, b = story.resolve_title(" The Last Little Fox ")
        self.assertEqual(a, "S01_the_last_little_fox")
        self.assertEqual(b, "The Last Little Fox")
        self.assertEqual(story.resolve_title("الثعلب الصغير الأخير")[0], a)
        self.assertEqual(story.resolve_title("The Boy Who Forgot Tomorrow")[0],
                         "S02_the_boy_who_forgot_tomorrow")
        self.assertEqual(story.resolve_title("الولد الذي نسي الغد")[1],
                         "The Boy Who Forgot Tomorrow")

    def test_ambiguous_or_unknown_story_fails_before_any_gpu(self):
        for name in ("Last", "Nightfall", "S01", "E02", "", "other story"):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    story.resolve_title(name)
        with self.assertRaisesRegex(ValueError, "Unknown Nightfall story"):
            story.select_story("The Wrong Fox")

    def test_story_title_maps_to_first_not_publicly_completed_episode(self):
        choice = story.select_story("The Last Little Fox")
        current = story.current_state(choice)
        self.assertEqual(current["episode_id"], "S01_the_last_little_fox_E01")
        self.assertTrue(current["e01_free_motion_supported"])
        self.assertEqual(current["status"], "RESUME_FROM_LAST_SHA_VERIFIED_E01_SHOT")
        self.assertFalse(current["publishing_is_public"])
        self.assertFalse(current["may_charge_paid_gpu"])

    def test_unprepared_second_story_stops_without_fake_episode_or_gpu(self):
        chosen = story.select_story("The Boy Who Forgot Tomorrow")
        current = story.current_state(chosen)
        self.assertEqual(current["episode_id"], "S02_the_boy_who_forgot_tomorrow_E01")
        self.assertFalse(current["e01_free_motion_supported"])
        self.assertEqual(current["status"], "BLOCKED_UNPREPARED_EPISODE_NO_GPU_NO_UPLOAD")

    def test_default_preserves_in_progress_ember_e01(self):
        with tempfile.TemporaryDirectory() as d:
            with patch.object(story, "CONFIG_PATH", Path(d) / "active_story.json"):
                current = story.current_state(story.read_selection())
        self.assertEqual(current["episode_id"], "S01_the_last_little_fox_E01")
        self.assertTrue(current["e01_free_motion_supported"])
        # Existing checkpoint manifest remains independent of story UI.
        cast, plan = resume.film.scene_plan()
        progress = resume.create_state(plan)
        progress["completed"].append({"scene": 1, "part": 1})
        next_part = resume.next_unfinished(progress, plan)
        self.assertEqual((next_part[0]["scene_no"], next_part[1]), (1, 2))

    def test_saved_selection_refuses_tampered_metadata(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "active_story.json"
            f.write_text(json.dumps({
                "schema_version": 1, "series_id": "S01_the_last_little_fox",
                "title": "The Boy Who Forgot Tomorrow"
            }))
            with patch.object(story, "CONFIG_PATH", f):
                with self.assertRaisesRegex(ValueError, "drifted"):
                    story.read_selection()

    def test_story_update_persists_nonsecret_selected_title(self):
        chosen = story.select_story("The Last Little Fox")
        with tempfile.TemporaryDirectory() as d:
            dest = Path(d) / "active_story.json"
            prior = MagicMock()
            prior.read.return_value = json.dumps({"sha": "old-content-sha"}).encode()
            prior.status = 200
            accepted = MagicMock()
            accepted.status = 200
            accepted.read.return_value = b"{}"
            calls = []
            def fake_open(req, timeout):
                calls.append(req)
                return accepted if req.get_method() == "PUT" else prior
            # urlopen supports context manager. The mock read returns JSON bytes.
            prior.__enter__.return_value = prior
            accepted.__enter__.return_value = accepted
            with patch.object(story, "CONFIG_PATH", dest):
                with patch("pilot.story_one_click.urllib.request.urlopen", side_effect=fake_open):
                    story.persist_selection(chosen, token="test-workflow-token")
            self.assertEqual(len(calls), 2)
            post = json.loads(calls[-1].data)
            self.assertEqual(post["branch"], "main")
            self.assertEqual(post["sha"], "old-content-sha")
            decoded = json.loads(base64.b64decode(post["content"]))
            self.assertEqual(decoded, chosen)
            self.assertNotIn("test-workflow-token", json.dumps(post))
            self.assertEqual(json.loads(dest.read_text()), chosen)

    def test_dedicated_story_workflow_has_one_input_and_no_episode_field(self):
        content = (story.ROOT / ".github/workflows/nightfall_story_one_click.yml").read_text()
        manual = content.split("  workflow_dispatch:", 1)[1].split("  schedule:", 1)[0]
        self.assertIn("      story:", manual)
        self.assertNotIn("      episode:", manual)
        self.assertNotIn("      action:", manual)
        self.assertEqual(manual.count("        type: string"), 1)
        self.assertIn("The Last Little Fox", manual)
        self.assertIn("python -m pilot.story_one_click --mode select", content)
        self.assertIn("python -m pilot.story_one_click --mode current", content)
        self.assertIn("python -m pilot.e01_free_resume --mode one-shot", content)
        self.assertIn("python -m pilot.e01_free_resume --mode assemble", content)
        self.assertIn("python -m pilot.e01_completion_publish", content)
        self.assertIn("python -m pilot.e01_verify_platforms", content)
        self.assertIn("python -m pilot.e01_telegram_notify", content)
        self.assertIn("nightfall-free-e01-parts-", content)
        self.assertIn("secrets.TELEGRAM_BOT_TOKEN", content)
        self.assertNotIn("Stage a fully assembled E01 as YouTube PRIVATE", content)
        self.assertNotIn("NIGHTFALL_LIVE: true", content)

    def test_old_daily_workflow_no_longer_runs_duplicate_e01_gpu(self):
        old = (story.ROOT / ".github/workflows/nightfall.yml").read_text()
        section = old.split("      # LEGACY MANUAL E01 controls ONLY;", 1)[1].split(
            "      # Read-only API metadata only.", 1)[0]
        self.assertNotIn(
            "(github.event_name == 'schedule' && github.event.schedule == '0 10 * * *')",
            section)
        self.assertIn("if: (false) ||", section)


if __name__ == "__main__":
    unittest.main()
