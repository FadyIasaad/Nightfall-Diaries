"""No-charge, source-locked LTX-2.5 experiment regression tests."""
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch, MagicMock

from pilot import e01_new_cinematic_ref as m


class TestLTX25Pilot(unittest.TestCase):
    def test_audit_cinematic_asset_and_original_episode_locked(self):
        report = m.audit()
        self.assertTrue(report["original_22_episodes_verified"])
        self.assertEqual(report["expanded_scene_count"], 14)
        self.assertEqual(report["locked_cast_count"], 5)
        self.assertEqual(len(report["source_ember_sha256"]), 64)
        self.assertTrue(report["source_reference_is_new_candidate_not_canon"])
        self.assertTrue(report["original_character_locks_verified"])
        self.assertEqual(report["source_ember_sha256"], m.IMAGE_SHA256)
        self.assertEqual(report["provider"], "Lightricks/LTX-2.5")
        self.assertEqual((report["width"], report["height"]), (576, 1024))
        self.assertFalse(report["token_used"])
        self.assertFalse(report["paid_api_calls"])
        self.assertFalse(report["full_episode_created"])
        self.assertFalse(report["social_uploads"])

    def test_cannot_infer_outside_exact_open_pr(self):
        report = m.audit()
        with patch.dict(os.environ, {
            "GITHUB_EVENT_NAME": "push",
            "GITHUB_HEAD_REF": m.BRANCH,
            "NIGHTFALL_LTX25_ONE_SHOT": "YES",
        }):
            factory = MagicMock()
            self.assertEqual(m.trial(report, factory), 2)
            factory.assert_not_called()
        self.assertEqual(report["status"], "BLOCKED_NOT_ORIGINAL_PR_OPEN_EVENT")
        self.assertFalse(report["generation_attempted"])

    def test_excludes_auth_token_even_in_correct_event(self):
        with tempfile.TemporaryDirectory() as d:
            ev = Path(d) / "event.json"
            ev.write_text('{"action":"opened"}')
            report = m.audit()
            with patch.dict(os.environ, {
                "GITHUB_EVENT_PATH": str(ev),
                "GITHUB_EVENT_NAME": "pull_request",
                "GITHUB_HEAD_REF": m.BRANCH,
                "NIGHTFALL_LTX25_ONE_SHOT": "YES",
                "HF_TOKEN": "unexpected-paid-key",
            }):
                factory = MagicMock()
                self.assertEqual(m.trial(report, factory), 2)
                factory.assert_not_called()
            self.assertEqual(report["status"], "BLOCKED_UNEXPECTED_HF_TOKEN")

    def test_schema_changes_block_before_gpu(self):
        with tempfile.TemporaryDirectory() as d:
            ev = Path(d) / "event.json"
            ev.write_text('{"action":"opened"}')
            report = m.audit()
            client = MagicMock()
            client.view_api.return_value = {
                "named_endpoints": {"/run": {"parameters": [None] * 9}}
            }
            fake_gradio = types.SimpleNamespace(handle_file=lambda x: x)
            with patch.dict(sys.modules, {"gradio_client": fake_gradio}):
                with patch.dict(os.environ, {
                    "GITHUB_EVENT_PATH": str(ev),
                    "GITHUB_EVENT_NAME": "pull_request",
                    "GITHUB_HEAD_REF": m.BRANCH,
                    "NIGHTFALL_LTX25_ONE_SHOT": "YES",
                    "HF_TOKEN": "",
                }):
                    self.assertEqual(m.trial(report, lambda *a, **kw: client), 2)
                    client.predict.assert_not_called()
            self.assertEqual(report["status"], "BLOCKED_LTX25_API_SCHEMA_CHANGED")
            self.assertFalse(report["generation_attempted"])

    def test_single_generation_and_never_publishes(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            ev = tmp / "event.json"
            ev.write_text('{"action":"opened"}')
            fake_mp4 = tmp / "test.mp4"
            fake_mp4.write_bytes(b"stand-in" * 2000)
            report = m.audit()
            client = MagicMock()
            client.view_api.return_value = {
                "named_endpoints": {"/run": {"parameters": [None] * 10}}
            }
            client.predict.return_value = (str(fake_mp4), "used prompt", 41, "49 frames")
            ffprobe = MagicMock()
            ffprobe.stdout = json.dumps({
                "streams": [{"codec_type": "video", "width": 576, "height": 1024}],
                "format": {"duration": "2.04"},
            })
            fake_gradio = types.SimpleNamespace(handle_file=lambda x: x)
            with patch("pilot.e01_new_cinematic_ref.OUTPUT", tmp / "result"):
                with patch("pilot.e01_new_cinematic_ref.subprocess.run", return_value=ffprobe):
                    with patch.dict(sys.modules, {"gradio_client": fake_gradio}):
                        with patch.dict(os.environ, {
                            "GITHUB_EVENT_PATH": str(ev),
                            "GITHUB_EVENT_NAME": "pull_request",
                            "GITHUB_HEAD_REF": m.BRANCH,
                            "NIGHTFALL_LTX25_ONE_SHOT": "YES",
                            "HF_TOKEN": "",
                        }):
                            self.assertEqual(m.trial(report, lambda *a, **kw: client), 0)
            self.assertEqual(client.predict.call_count, 1)
            self.assertEqual(client.predict.call_args.kwargs["api_name"], "/run")
            self.assertEqual(client.predict.call_args.args[2:6], (1024, 576, 2.0, 41))
            self.assertEqual(report["status"], "UNAPPROVED_LTX25_VIDEO_CANDIDATE")
            self.assertFalse(report["full_episode_created"])
            self.assertFalse(report["social_uploads"])
            self.assertFalse(report["cinematic_quality_approved"])

    def test_pr_once_only_and_artifact_safety(self):
        wf = (m.ROOT / ".github/workflows/nightfall.yml").read_text()
        self.assertIn("github.event.action == 'opened'", wf)
        self.assertIn(m.BRANCH, wf)
        self.assertIn("NIGHTFALL_LTX25_ONE_SHOT: YES", wf)
        self.assertIn("HF_TOKEN: ''", wf)
        self.assertIn("new_ember_one_shot_unapproved.mp4", wf)
        self.assertNotIn("NIGHTFALL_LIVE: true", wf)


if __name__ == "__main__":
    unittest.main()
