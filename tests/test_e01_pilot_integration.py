"""First-film integration tests: no GPU is consumed by this test module."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from studio.restore import ROOT
from pilot.e01_pilot import (
    APPROVED_HEAD, EPISODE_ID, SEASON, audit, one_shot
)


class FirstEpisodePilotIntegrationTests(unittest.TestCase):
    def test_all_original_cast_and_14_scenes_ready_without_render(self):
        with tempfile.TemporaryDirectory() as d:
            report, proof, cast = audit(d)
            self.assertEqual(report["episode_id"], EPISODE_ID)
            self.assertEqual(report["original_episode_count_verified"], 22)
            self.assertEqual(report["expanded_scene_count"], 14)
            self.assertTrue(240 <= report["expanded_spoken_words"] <= 430)
            self.assertEqual(report["locked_cast_count"], 5)
            self.assertEqual(report["proof_shot_count"], 3)
            self.assertEqual(len(cast), 5)
            self.assertTrue(report["original_image_references_verified"])
            self.assertFalse(report["full_episode_mp4_generated"])
            self.assertFalse(report["public_publishing_attempted"])
            self.assertFalse(report["paid_api_calls"])
            self.assertFalse(report["lip_sync_verified"])
            data = json.loads((Path(d) / "e01_all_14_scenes.json").read_text())
            self.assertEqual(len(data["scene_jobs"]), 14)
            for shot in data["scene_jobs"]:
                self.assertEqual(shot["voice_engine"], "kokoro")
                self.assertEqual(len(shot["image_ref_sha256"]), 64)
                self.assertIn("Real animation only", shot["prompt"])
                self.assertEqual(shot["status"], "PLANNED_NOT_RENDERED")
            self.assertFalse((Path(d) / "e01_first_shot_unapproved.mp4").exists())

    def test_free_clip_cannot_run_outside_one_pilot_pr(self):
        with tempfile.TemporaryDirectory() as d:
            report, proof, cast = audit(d)
            with patch.dict(os.environ, {"GITHUB_EVENT_NAME": "push",
                                          "GITHUB_HEAD_REF": APPROVED_HEAD,
                                          "NIGHTFALL_E01_ONE_SHOT": "YES_ONCE"}):
                with patch("pilot.e01_pilot.motion_probe") as provider:
                    self.assertEqual(one_shot(d, report, proof, cast), 2)
                    provider.assert_not_called()
            self.assertEqual(report["single_test_status"], "BLOCKED_WRONG_CI_CONTEXT")
            self.assertFalse(report["full_episode_mp4_generated"])

    def test_unavailable_free_provider_creates_no_video(self):
        with tempfile.TemporaryDirectory() as d:
            report, proof, cast = audit(d)
            env = {"GITHUB_EVENT_NAME": "pull_request",
                   "GITHUB_HEAD_REF": APPROVED_HEAD,
                   "NIGHTFALL_E01_ONE_SHOT": "YES_ONCE"}
            with patch.dict(os.environ, env):
                with patch("pilot.e01_pilot.motion_probe", return_value={
                        "state": "BLOCKED", "notes": "Free quota unavailable"}):
                    self.assertEqual(one_shot(d, report, proof, cast), 2)
            self.assertFalse(report["first_motion_clip_attempted"])
            self.assertEqual(report["single_test_status"], "BLOCKED_PUBLIC_FREE_PROVIDER")
            self.assertFalse(report["full_episode_mp4_generated"])

    def test_only_one_clip_can_be_attempted_and_never_approved(self):
        with tempfile.TemporaryDirectory() as d:
            report, proof, cast = audit(d)
            env = {"GITHUB_EVENT_NAME": "pull_request",
                   "GITHUB_HEAD_REF": APPROVED_HEAD,
                   "NIGHTFALL_E01_ONE_SHOT": "YES_ONCE"}
            calls = []
            def fake_generator(image, prompt, destination, seconds):
                calls.append((image, seconds))
                Path(destination).write_bytes(b"fake video bytes " * 2000)
            with patch.dict(os.environ, env):
                with patch("pilot.e01_pilot.motion_probe", return_value={
                        "state": "READY_FOR_ONE_QUOTA_LIMITED_TEST"}):
                    with patch("studio.free_video.generate_video", side_effect=fake_generator):
                        with patch("pilot.e01_pilot.subprocess.run") as ffprobe:
                            ffprobe.return_value.stdout = json.dumps({
                                "streams": [{"codec_type": "video", "width": 320, "height": 576}],
                                "format": {"duration": "5.0"},
                            })
                            result = one_shot(d, report, proof, cast)
            self.assertEqual(result, 0)
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0][1], 5.0)
            self.assertEqual(report["single_test_status"], "VIDEO_CANDIDATE_UNAPPROVED")
            self.assertFalse(report["full_episode_mp4_generated"])
            self.assertFalse(report["lip_sync_verified"])
            self.assertFalse(report["public_publishing_attempted"])

    def test_workflow_one_off_protection(self):
        workflow = (ROOT / ".github/workflows/nightfall.yml").read_text(encoding="utf-8")
        self.assertIn(APPROVED_HEAD, workflow)
        self.assertIn("github.event.action == 'opened'", workflow)
        self.assertIn("NIGHTFALL_E01_ONE_SHOT: YES_ONCE", workflow)
        self.assertIn("e01_first_shot_unapproved.mp4", workflow)
        self.assertNotIn("NIGHTFALL_LIVE: true", workflow)


if __name__ == "__main__":
    unittest.main()
