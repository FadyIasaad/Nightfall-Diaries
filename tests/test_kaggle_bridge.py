"""Offline tests of Kaggle staging, immutable Ember assets and zero-publish gates."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from studio.kaggle_bridge import (
    EMBER_PATH, LOCKS_PATH, TEMPLATE, dispatch, original_ember_bytes, safe_owner, stage
)


class KaggleBridgeSafetyTests(unittest.TestCase):
    def test_owner_must_be_a_slug(self):
        self.assertEqual(safe_owner("my-kaggle-account"), "my-kaggle-account")
        for bad in ("", "../bad", "u/name", "UPPER", "a b", "ok;echo"):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    safe_owner(bad)

    def test_probe_is_private_free_t4_no_internet_no_embed(self):
        with tempfile.TemporaryDirectory() as temp:
            config = stage("gpu_probe", "owner", temp)
            self.assertTrue(config["is_private"])
            self.assertTrue(config["enable_gpu"])
            self.assertFalse(config["enable_internet"])
            self.assertEqual(config["machine_shape"], "NvidiaTeslaT4")
            self.assertEqual(config["id"], "owner/nightfall-t4-ember-safe")
            source = (Path(temp) / "nightfall_run.py").read_text()
            self.assertIn("RUN_MODE = 'gpu_probe'", source)
            self.assertIn("EMBER_B64 = ''", source)
            self.assertFalse(config["dataset_sources"])
            self.assertFalse(config["model_sources"])

    def test_only_original_ember_reference_is_embedded(self):
        with tempfile.TemporaryDirectory() as temp:
            raw = original_ember_bytes()
            self.assertTrue(raw.startswith(b"\x89PNG\r\n\x1a\n"))
            config = stage("ember_i2v", "owner", temp)
            self.assertTrue(config["enable_internet"])
            source = (Path(temp) / "nightfall_run.py").read_text()
            self.assertIn("RUN_MODE = 'ember_i2v'", source)
            self.assertIn("EMBER_B64 = ", source)
            self.assertGreater(len(source), len(TEMPLATE.read_text()) + len(raw))
            self.assertEqual(json.loads(LOCKS_PATH.read_text())["s01_ember"],
                             __import__("hashlib").sha256(raw).hexdigest())

    def test_no_token_refuses_api_submission(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch.dict(os.environ, {"KAGGLE_API_TOKEN": ""}):
                with patch("studio.kaggle_bridge.runner") as runner:
                    with self.assertRaisesRegex(RuntimeError, "KAGGLE_API_TOKEN"):
                        dispatch("gpu_probe", "owner", temp)
                    runner.assert_not_called()
            report = json.loads((Path(temp) / "kaggle_dispatch.json").read_text())
            self.assertEqual(report["status"], "BLOCKED_KAGGLE_API_TOKEN_MISSING")

    def test_dry_run_is_offline(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch("studio.kaggle_bridge.runner") as runner:
                report = dispatch("gpu_probe", "owner", temp, dry_run=True)
                runner.assert_not_called()
                self.assertEqual(report["status"], "STAGED_NO_CLOUD_RUN")
                self.assertFalse(report["paid_api_calls"])
                self.assertFalse(report["publishing"])

    def test_unknown_mode_never_dispatches(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                stage("publish", "owner", temp)

    def test_workflow_does_not_publish_from_kaggle(self):
        wf = (EMBER_PATH.parents[4] / ".github/workflows/nightfall.yml").read_text()
        self.assertIn("Kaggle GPU check", wf)
        self.assertIn("Kaggle Ember proof", wf)
        self.assertIn("github.event_name == 'workflow_dispatch'", wf)
        settings = json.loads((EMBER_PATH.parents[4] / "studio/production_settings.json").read_text())
        self.assertFalse(settings["production_enabled"])
        self.assertFalse(settings["cinematic_video_approved"])
        self.assertFalse(settings["publishing_implemented"])


    def test_kaggle_cli_install_declares_six_and_tests_cli_before_dispatch(self):
        workflow = (EMBER_PATH.parents[4] / ".github/workflows/nightfall.yml").read_text()
        install = workflow.index("- name: Install and smoke-test Kaggle CLI")
        auth = workflow.index("- name: Validate Kaggle token with read-only own-kernels query")
        dispatch = workflow.index("- name: Dispatch one private Kaggle T4 notebook")
        self.assertLess(install, auth)
        self.assertLess(auth, dispatch)
        # The CLI install step uses no secret; the next, manual-only step does.
        preflight = workflow[install:auth]
        self.assertIn("'six>=1.16,<2'", preflight)
        self.assertIn("from kaggle.cli import main", preflight)
        self.assertIn("kaggle kernels push --help", preflight)
        self.assertIn("github.event_name == 'pull_request'", preflight)
        self.assertNotIn("KAGGLE_API_TOKEN:", preflight)



    def test_pr_runs_cannot_block_kaggle_and_auth_precedes_gpu(self):
        workflow = (EMBER_PATH.parents[4] / ".github/workflows/nightfall.yml").read_text()
        self.assertIn("format('pr-{0}', github.event.pull_request.number)", workflow)
        self.assertIn("'push-check'", workflow)
        self.assertIn("'production'", workflow)
        self.assertIn("cancel-in-progress: ${{ github.event_name == 'pull_request' }}", workflow)
        auth = workflow.index("- name: Validate Kaggle token with read-only own-kernels query")
        dispatch = workflow.index("- name: Dispatch one private Kaggle T4 notebook")
        self.assertLess(auth, dispatch)
        preflight = workflow[auth:dispatch]
        self.assertIn("kaggle kernels list --mine --page-size 1", preflight)
        self.assertIn("KAGGLE_API_TOKEN: ${{ secrets.KAGGLE_API_TOKEN }}", preflight)
        self.assertIn("KAGGLE_USERNAME: ${{ vars.KAGGLE_USERNAME }}", preflight)
        self.assertIn("github.event_name == 'workflow_dispatch'", preflight)
        self.assertNotIn("github.event_name == 'pull_request'", preflight)


if __name__ == "__main__":
    unittest.main()
