"""Offline contract tests: daily 36-shot completion and PRIVATE-only uploading."""
import copy
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from pilot import e01_free_resume as resume
from pilot import e01_private_youtube as youtube


def full_test_state(plan):
    state = resume.create_state(plan)
    state["completed"] = [
        {"scene": s["scene_no"], "part": part,
         "file": "mock.mp4", "sha256": "a"*64, "seconds": float(seconds)}
        for s in plan["scenes"]
        for part, seconds in enumerate(s["subshot_seconds"], 1)
    ]
    return state


class DailyE01Contract(unittest.TestCase):
    def test_next_shot_never_restarts_from_saved_part_one(self):
        _, plan = resume.film.scene_plan()
        s = resume.create_state(plan)
        s["completed"].append({"scene": 1, "part": 1})
        nextshot = resume.next_unfinished(s, plan)
        self.assertEqual((nextshot[0]["scene_no"], nextshot[1]), (1, 2))
        self.assertEqual(nextshot[2], 5)

    def test_automatic_daily_gate_assembles_only_after_all_36(self):
        _, plan = resume.film.scene_plan()
        state = full_test_state(plan)
        self.assertEqual(len(state["completed"]), 36)
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "outputs.txt"
            with patch.object(resume, "load_state", return_value=state):
                with patch.dict(os.environ, {"GITHUB_OUTPUT": str(dest)}):
                    ready = resume.assembly_gate()
            self.assertTrue(ready["ready"])
            self.assertTrue(ready["all_36_genuine_shots_verified"])
            self.assertIn("ready=true", dest.read_text())
            state["completed"].pop()
            with patch.object(resume, "load_state", return_value=state):
                with patch.dict(os.environ, {"GITHUB_OUTPUT": str(dest)}):
                    pending = resume.assembly_gate()
            self.assertFalse(pending["ready"])
            self.assertFalse(pending["all_36_genuine_shots_verified"])

    def test_after_all_shots_daily_schedule_makes_no_further_gpu_request(self):
        _, plan = resume.film.scene_plan()
        state = full_test_state(plan)
        env = {
            "GITHUB_EVENT_NAME": "schedule", "GITHUB_REF": "refs/heads/main",
            "NIGHTFALL_FREE_DAILY_ENABLED": "YES", "NIGHTFALL_FREE_RESUME": "YES",
            "GITHUB_RUN_ATTEMPT": "1", "HF_TOKEN": "fake",
        }
        with patch.dict(os.environ, env, clear=True):
            with patch.object(resume, "load_state", return_value=state):
                with patch.object(resume, "_save"):
                    with patch.object(resume, "account_preflight") as quota:
                        result = resume.resume_one_shot()
                        quota.assert_not_called()
        self.assertEqual(result["shots_completed"], 36)
        self.assertIsNone(result["next"])

    def test_assembly_remains_blocked_if_even_one_real_shot_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            with patch.object(resume, "OUT", out), patch.object(resume, "STATE", out / "progress.json"):
                with patch.dict(os.environ, {
                    "GITHUB_EVENT_NAME": "schedule", "GITHUB_REF": "refs/heads/main",
                    "NIGHTFALL_FREE_ASSEMBLE": "YES",
                    "NIGHTFALL_FREE_DAILY_ENABLED": "YES", "GITHUB_RUN_ATTEMPT": "1",
                }, clear=True):
                    with self.assertRaisesRegex(RuntimeError, "36 real motion clips"):
                        resume.assemble_unapproved()

    def test_workflow_has_daily_but_no_public_upload(self):
        wf = (resume.ROOT / ".github/workflows/nightfall.yml").read_text()
        self.assertIn("github.event.schedule == '0 10 * * *'", wf)
        self.assertIn("python -m pilot.e01_free_resume --mode assembly-gate", wf)
        self.assertIn("python -m pilot.e01_free_resume --mode assemble", wf)
        self.assertIn("python -m pilot.e01_private_youtube", wf)
        self.assertIn("YOUTUBE_VISIBILITY: private", wf)
        self.assertNotIn("NIGHTFALL_LIVE: true", wf)


class PrivateYouTubeSafety(unittest.TestCase):
    def test_no_upload_when_36_original_shots_missing(self):
        with patch.dict(os.environ, {
            "GITHUB_EVENT_NAME": "schedule", "GITHUB_REF": "refs/heads/main",
            "GITHUB_RUN_ATTEMPT": "1", "NIGHTFALL_PRIVATE_YOUTUBE_STAGE": "YES",
        }, clear=True):
            uploader = Mock()
            with self.assertRaisesRegex(RuntimeError, "INCOMPLETE_36"):
                youtube.stage_private_youtube(uploader=uploader)
            uploader.assert_not_called()

    def test_no_youtube_oauth_gives_no_upload(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(youtube._channel_preflight(),
                             (None, "BLOCKED_MISSING_YOUTUBE_OAUTH"))

    def test_one_private_upload_is_idempotent_and_never_public(self):
        with tempfile.TemporaryDirectory() as tmp:
            asset = Path(tmp) / youtube.FULL_VIDEO
            asset.write_bytes(b"fake test bytes")
            state = {
                "assembled_video_sha256": "a" * 64,
                "technical_full_mp4": True,
                "voices": [{"scene": i} for i in range(1, 15)],
                "completed": [{"scene": i, "part": 1} for i in range(1, 37)],
            }
            snapshots = []
            def saved(s):
                snapshots.append(copy.deepcopy(s))
            def upload(file, title, description):
                self.assertEqual(file, asset)
                self.assertEqual(os.environ["YOUTUBE_VISIBILITY"], "private")
                self.assertIn("PRIVATE", title)
                self.assertIn("NOT approved", description)
                self.assertTrue(snapshots[-1]["youtube_private_attempt_started"])
                self.assertFalse(snapshots[-1].get("published_anywhere", False))
                return {"id": "private-id-9876"}
            env = {
                "GITHUB_EVENT_NAME": "schedule", "GITHUB_REF": "refs/heads/main",
                "GITHUB_RUN_ATTEMPT": "1", "NIGHTFALL_PRIVATE_YOUTUBE_STAGE": "YES"
            }
            with patch.dict(os.environ, env, clear=True):
                with patch.object(youtube, "_verify_film", return_value=(
                    state, asset, {"technical_check_passed": True}
                )):
                    with patch.object(youtube, "_save_progress", side_effect=saved):
                        result = youtube.stage_private_youtube(
                            uploader=upload, preflight=lambda: ("UC-verified-channel", None))
                        self.assertEqual(result["status"], "UPLOADED_PRIVATE_UNAPPROVED_NOT_PUBLIC")
                        self.assertFalse(result["publicly_published"])
                        again = youtube.stage_private_youtube(
                            uploader=Mock(side_effect=AssertionError("duplicate")),
                            preflight=lambda: (None, "should not check again"))
                        self.assertEqual(again["status"], "ALREADY_UPLOADED_PRIVATE")
            self.assertEqual(state["youtube_private_receipt"]["visibility"], "private")
            self.assertFalse(state["published_anywhere"])

    def test_ambiguous_upload_error_never_autoretries(self):
        state = {"technical_full_mp4": True}
        with patch.dict(os.environ, {
            "GITHUB_EVENT_NAME": "workflow_dispatch",
            "GITHUB_REF": "refs/heads/main", "GITHUB_RUN_ATTEMPT": "1",
            "NIGHTFALL_PRIVATE_YOUTUBE_STAGE": "YES",
        }, clear=True):
            with patch.object(youtube, "_verify_film", return_value=(
                    state, Path("/mock.mp4"), {})):
                with patch.object(youtube, "_save_progress"):
                    first = youtube.stage_private_youtube(
                        uploader=Mock(side_effect=RuntimeError("network timeout")),
                        preflight=lambda: ("UC-channel", None))
                    self.assertTrue(first["requires_review_to_avoid_duplicate"])
                    second = youtube.stage_private_youtube(
                        uploader=Mock(side_effect=AssertionError("duplicate")),
                        preflight=lambda: ("UC-channel", None))
                    self.assertIn("STOP_POSSIBLE_PREVIOUS", second["status"])


if __name__ == "__main__":
    unittest.main()
