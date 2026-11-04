"""Regression tests for visible same-day manual action and its execution path."""
import unittest
from studio.restore import ROOT
from studio.run_free import main
from unittest.mock import patch
import sys

class ManualExtraEpisodeTests(unittest.TestCase):
    def test_extra_episode_dropdown_has_dependencies_and_runner(self):
        workflow=(ROOT/".github/workflows/nightfall.yml").read_text(encoding="utf-8")
        self.assertIn("          - Generate another episode",workflow)
        self.assertGreaterEqual(workflow.count("inputs.action == 'Generate another episode'"),3)
        self.assertIn('"Generate another episode") MODE=generate_another_episode',workflow)
        self.assertIn("python -m studio.run_free --action",workflow)

    def test_render_production_uses_immutable_cast(self):
        renderer=(ROOT/"studio/real_film.py").read_text(encoding="utf-8")
        self.assertIn("cast = locked_cast(season_id)",renderer)
        self.assertIn("240 <= words <= 430",renderer)

    def test_auto_is_rejected_for_manual_extra_without_GPU(self):
        with patch.object(sys,"argv",["studio.run_free","--action","generate_another_episode","--episode","auto"]):
            with self.assertRaisesRegex(SystemExit,"EPISODE_REQUIRED"):
                main()
