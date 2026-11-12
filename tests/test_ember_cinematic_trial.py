"""Safety gates for first real cinematic-reference film test."""
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import MagicMock, patch
from pilot import ember_cinematic_trial as film


class EmberCinematicTrialTests(unittest.TestCase):
    def test_new_reference_binary_matches_sha_and_all_canon_untouched(self):
        report = film.build_report()
        self.assertEqual(report["episode"], "S01_the_last_little_fox_E01")
        self.assertEqual(report["new_cinematic_reference_sha256"], film.IMAGE_SHA256)
        self.assertEqual(report["E01_scene_count"], 14)
        self.assertEqual(report["story_count"], 22)
        self.assertEqual(report["locked_cast_count"], 5)
        self.assertTrue(report["original_reference_unchanged"])
        self.assertFalse(report["full_episode_generated"])
        self.assertFalse(report["social_upload_attempted"])
        self.assertFalse(report["paid_provider_called"])
        self.assertFalse(report["cinematic_quality_approved"])

    def test_no_inference_on_main_push_or_schedule(self):
        with patch.dict(os.environ, {"GITHUB_EVENT_NAME": "push",
                                          "GITHUB_RUN_ATTEMPT": "1",
                                          "GITHUB_HEAD_REF": film.BRANCH,
                                          "NIGHTFALL_EMBER_LTX_ONCE": "YES"}):
            c = MagicMock()
            r = film.build_report()
            self.assertEqual(film.run_trial(r, client_factory=c), 2)
            c.assert_not_called()
            self.assertEqual(r["status"], "BLOCKED_NOT_PR_FIRST_OPEN_RUN")

    def test_no_inference_on_pr_rerun(self):
        with TemporaryDirectory() as d:
            e = Path(d)/"event.json"; e.write_text('{"action":"opened"}')
            with patch.dict(os.environ, {"GITHUB_EVENT_NAME": "pull_request",
                                              "GITHUB_RUN_ATTEMPT": "2",
                                              "GITHUB_HEAD_REF": film.BRANCH,
                                              "GITHUB_EVENT_PATH": str(e),
                                              "NIGHTFALL_EMBER_LTX_ONCE": "YES"}):
                self.assertFalse(film.allowed())

    def test_no_inference_on_pr_revision(self):
        with TemporaryDirectory() as d:
            e = Path(d)/"event.json"; e.write_text('{"action":"synchronize"}')
            with patch.dict(os.environ, {"GITHUB_EVENT_NAME": "pull_request",
                                              "GITHUB_RUN_ATTEMPT": "1",
                                              "GITHUB_HEAD_REF": film.BRANCH,
                                              "GITHUB_EVENT_PATH": str(e),
                                              "NIGHTFALL_EMBER_LTX_ONCE": "YES"}):
                self.assertFalse(film.allowed())

    def test_no_provider_request_with_token_even_when_authorized(self):
        with TemporaryDirectory() as d:
            e = Path(d)/"event.json"; e.write_text('{"action":"opened"}')
            env = {"GITHUB_EVENT_NAME": "pull_request",
                   "GITHUB_RUN_ATTEMPT": "1",
                   "GITHUB_HEAD_REF": film.BRANCH,
                   "GITHUB_EVENT_PATH": str(e),
                   "NIGHTFALL_EMBER_LTX_ONCE": "YES",
                   "HF_TOKEN": "NOT_AUTHORIZED"}
            with patch.dict(os.environ, env):
                r = film.build_report()
                c = MagicMock()
                self.assertEqual(film.run_trial(r, client_factory=c), 2)
                self.assertEqual(r["status"], "BLOCKED_ANY_GENERATION_TOKEN_PRESENT")
                c.assert_not_called()

    def test_open_pr_with_api_schema_drift_never_calls_inference(self):
        with TemporaryDirectory() as d:
            e = Path(d)/"event.json"; e.write_text('{"action":"opened"}')
            env = {"GITHUB_EVENT_NAME": "pull_request",
                   "GITHUB_RUN_ATTEMPT": "1",
                   "GITHUB_HEAD_REF": film.BRANCH,
                   "GITHUB_EVENT_PATH": str(e),
                   "NIGHTFALL_EMBER_LTX_ONCE": "YES",
                   "HF_TOKEN": "", "AGNES_API_KEY": "", "LTX_API_KEY": ""}
            fake = MagicMock()
            fake.view_api.return_value={"named_endpoints":{"/run":{"parameters":[None]*7}}}
            with patch("pilot.ember_cinematic_trial.OUTPUT", Path(d)), \
                 patch("pilot.ember_cinematic_trial.REPORT", Path(d)/"test.json"), \
                 patch("pilot.ember_cinematic_trial.subprocess.run") as proc, \
                 patch.dict(os.environ, env):
                proc.return_value.returncode=0
                r=film.build_report()
                self.assertEqual(film.run_trial(r,client_factory=lambda *a,**k:fake,image_handler=lambda x:x),2)
                fake.predict.assert_not_called()
                self.assertEqual(r["status"],"BLOCKED_OFFICIAL_LTX_API_SCHEMA_CHANGED")

    def test_only_first_pr_opened_may_generate_and_archive(self):
        workflow=(film.ROOT/".github/workflows/nightfall.yml").read_text()
        self.assertIn(film.BRANCH,workflow)
        self.assertIn("github.event.action == 'opened'",workflow)
        self.assertIn("github.run_attempt == 1",workflow)
        self.assertIn("NIGHTFALL_EMBER_LTX_ONCE: YES",workflow)
        self.assertIn("ember_cinematic_2sec_unapproved.mp4",workflow)
        self.assertIn("HF_TOKEN: ''",workflow)


if __name__=="__main__":
    unittest.main()
