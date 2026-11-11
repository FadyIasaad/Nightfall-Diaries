"""Offline tests of Kaggle staging, immutable Ember assets and zero-publish gates."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from studio.kaggle_bridge import (
    EMBER_PATH, LOCKS_PATH, TEMPLATE, diagnose_last, dispatch, original_ember_bytes, safe_owner, stage
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
        self.assertIn("from importlib.metadata import version", preflight)
        self.assertNotIn("from kaggle.cli import main", preflight)
        self.assertNotIn("kaggle kernels push --help", preflight)
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
        self.assertIn("from kaggle.cli import main", preflight)
        self.assertIn("kaggle kernels push --help", preflight)
        self.assertIn("KAGGLE_API_TOKEN: ${{ secrets.KAGGLE_API_TOKEN }}", preflight)
        self.assertIn("KAGGLE_USERNAME: ${{ vars.KAGGLE_USERNAME }}", preflight)
        self.assertIn("github.event_name == 'workflow_dispatch'", preflight)
        self.assertNotIn("github.event_name == 'pull_request'", preflight)


    def test_diagnose_last_uses_existing_kernel_without_gpu_submission(self):
        with tempfile.TemporaryDirectory() as directory:
            commands = []

            def fake_runner(argv, timeout=120):
                commands.append(tuple(argv))
                self.assertNotIn("push", argv)
                self.assertNotIn("logs", argv)  # Not supported in Kaggle CLI 1.8.4.
                if argv[2] == "status":
                    return 'owner/nightfall-t4-ember-safe has status "KernelWorkerStatus.ERROR"'
                if argv[2] == "pull":
                    remote = Path(argv[argv.index("-p") + 1])
                    (remote / "kernel-metadata.json").write_text(json.dumps({
                        "enable_gpu": True, "machine_shape": "NvidiaTeslaT4",
                    }))
                    return "Pulled source and metadata (no run)"
                if argv[2] == "output":
                    output = Path(argv[argv.index("-p") + 1])
                    (output / "nightfall-t4-ember-safe.log").write_text(
                        "Worker CUDA not available; torch.cuda.device_count=0"
                    )
                    (output / "nightfall_kaggle_report.json").write_text(
                        json.dumps({
                            "error_type": "RuntimeError",
                            "error": "No Kaggle GPU allocated; verify account GPU access/quota",
                            "free_gpu_confirmed": False,
                            "gpu_devices": [],
                            "result": "BLOCKED",
                        })
                    )
                    return "Downloaded output files"
                raise AssertionError("Unexpected CLI command")

            with patch.dict(os.environ, {"KAGGLE_API_TOKEN": "secure-sample-not-real"}):
                with patch("studio.kaggle_bridge.runner", side_effect=fake_runner):
                    result = diagnose_last("owner", directory)

            self.assertEqual([x[2] for x in commands], ["status", "pull", "output"])
            self.assertEqual(result["status"], "KAGGLE_WORKER_ERROR_DIAGNOSTIC_COLLECTED")
            self.assertEqual(result["root_cause"], "KAGGLE_CUDA_NOT_ALLOCATED")
            self.assertTrue(result["remote_gpu_enabled"])
            self.assertEqual(result["remote_machine_shape"], "NvidiaTeslaT4")
            self.assertTrue(result["logs_downloaded"])
            self.assertFalse(result["gpu_submission_attempted"])
            self.assertIn("CUDA not available", (Path(directory) / "kaggle_worker_logs.txt").read_text())
            self.assertTrue((Path(directory) / "kaggle_diagnostic.json").is_file())

    def test_diagnose_redacts_tokens_in_downloaded_kaggle_output_logs(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {"KAGGLE_API_TOKEN": "TOP_SECRET_FAKE_TOKEN_123"}):
                def fake_runner(argv, timeout=120):
                    if argv[2] == "status":
                        return "TOP_SECRET_FAKE_TOKEN_123"
                    if argv[2] == "pull":
                        remote = Path(argv[argv.index("-p") + 1])
                        (remote / "kernel-metadata.json").write_text(
                            '{"enable_gpu": false, "machine_shape": null}'
                        )
                    if argv[2] == "output":
                        output = Path(argv[argv.index("-p") + 1])
                        (output / "nightfall-t4-ember-safe.log").write_text(
                            "CUDA error: TOP_SECRET_FAKE_TOKEN_123"
                        )
                    return ""

                with patch("studio.kaggle_bridge.runner", side_effect=fake_runner):
                    result = diagnose_last("owner", directory)
            report = (Path(directory) / "kaggle_diagnostic.json").read_text()
            logs = (Path(directory) / "kaggle_worker_logs.txt").read_text()
            self.assertNotIn("TOP_SECRET_FAKE_TOKEN_123", logs + report)
            self.assertIn("[REDACTED]", logs)
            self.assertIs(result["remote_gpu_enabled"], False)

    def test_diagnostic_action_is_manual_and_never_submits_new_kernel(self):
        workflow = (EMBER_PATH.parents[4] / ".github/workflows/nightfall.yml").read_text()
        self.assertIn("Kaggle diagnose last run", workflow)
        self.assertIn("python -m studio.kaggle_bridge --mode diagnose", workflow)
        self.assertIn("output/kaggle_dispatch/kaggle_worker_logs.txt", workflow)
        self.assertIn("output/kaggle_dispatch/kaggle_diagnostic.json", workflow)
        # The bridge exposes diagnostics but forbids staging/inference for this mode.
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                stage("diagnose", "owner", directory)



if __name__ == "__main__":
    unittest.main()
