"""Real-shot continuation: no paid calls, each real clip gets its own alert."""
import os
import unittest
from unittest.mock import Mock, patch

from pilot import e01_continuous_free as batch
from pilot import e01_free_resume as resume
from studio.restore import ROOT


class ContinueOnlyRealClipsTests(unittest.TestCase):
    def test_two_real_clips_announce_separately_before_next_free_request(self):
        state = {"completed": [], "status": "READY"}
        events = []

        def shot(*, allow_same_run_retry):
            self.assertTrue(allow_same_run_retry)
            # Every new inference must happen AFTER the previous alert.
            completed = len(state["completed"])
            if completed:
                self.assertEqual(events[-1], "telegram")
            events.append("gpu")
            if completed == 2:
                state["status"] = "PAUSED_FREE_QUOTA_INSUFFICIENT"
                return {"state": state["status"]}
            state["completed"].append({
                "scene": 1, "part": completed + 1,
                "sha256": f"{completed+1:064x}",
                "seconds": 5.04,
            })
            state["status"] = "PARTIAL_REAL_MOTION_UNAPPROVED"
            return {"state": state["status"]}

        def alert(current):
            events.append("telegram")
            self.assertEqual(len(current["completed"]),
                             len([x for x in events if x == "telegram"]))
            return {"status": "REAL_MOTION_SHOT_NOTIFICATION_SENT",
                    "messages_sent": 1}

        with patch.object(resume, "load_state", return_value=state):
            result = batch.continue_free(
                single_shot=shot, plan_loader=lambda: (None, {}),
                alert=alert, monotonic=lambda: 0)
        self.assertEqual(events, ["gpu", "telegram", "gpu", "telegram", "gpu"])
        self.assertEqual(result["shots_completed"], 2)
        self.assertEqual(result["telegram_messages_sent"], 2)
        self.assertEqual(result["status"], "PAUSED_FREE_QUOTA_INSUFFICIENT")
        self.assertFalse(result["public_posts_created"])

    def test_zero_free_quota_never_fabricates_or_announces_clip(self):
        state = {"completed": [
            {"scene": 1, "part": 1, "sha256": "a"*64, "seconds": 5.04}],
            "status": "PAUSED_FREE_QUOTA_INSUFFICIENT"}
        alert = Mock()
        shot = Mock(return_value={"state": "PAUSED_FREE_QUOTA_INSUFFICIENT"})
        with patch.object(resume, "load_state", return_value=state):
            result = batch.continue_free(single_shot=shot,
                                         plan_loader=lambda: (None, {}),
                                         alert=alert, monotonic=lambda: 0)
        self.assertEqual(result["new_real_shots_in_this_run"], 0)
        self.assertEqual(result["shots_completed"], 1)
        alert.assert_not_called()
        self.assertEqual(shot.call_count, 1)

    def test_time_limit_stops_before_another_gpu_attempt(self):
        shot = Mock()
        with patch.object(resume, "load_state",
                          return_value={"completed": [], "status": "READY"}):
            result = batch.continue_free(single_shot=shot,
                                         plan_loader=lambda: (None, {}),
                                         monotonic=Mock(side_effect=[0, 11]),
                                         max_elapsed_seconds=10)
        self.assertEqual(result["status"], "BATCH_SAFE_TIME_LIMIT")
        shot.assert_not_called()

    def test_provider_error_is_reported_without_repeated_gpu_or_false_alerts(self):
        shot = Mock(side_effect=RuntimeError("prohibited token details"))
        alert = Mock()
        with patch.object(resume, "load_state",
                          return_value={"completed": [], "status": "BLOCKED_FREE_PROVIDER_OR_AUTH"}):
            result = batch.continue_free(single_shot=shot,
                                         plan_loader=lambda: (None, {}),
                                         alert=alert, monotonic=lambda: 0)
        self.assertEqual(result["status"], "FREE_PROVIDER_OR_AUTH_ERROR_RuntimeError")
        alert.assert_not_called()
        self.assertEqual(shot.call_count, 1)

    def test_marker_only_push_starts_immediately_on_main(self):
        w = (ROOT / ".github/workflows/nightfall_story_one_click.yml").read_text()
        self.assertIn("'.github/nightfall_start_now.txt'", w)
        self.assertIn("python -m pilot.e01_continuous_free", w)
        self.assertIn("NIGHTFALL_OWNER_START_NOW:", w)
        self.assertIn("TELEGRAM_BOT_TOKEN:", w)
        self.assertIn("TELEGRAM_CHAT_ID:", w)
        self.assertIn("python -m pilot.e01_telegram_notify --mode progress", w)

    def test_no_arbitrary_push_can_invoke_inference(self):
        with patch.dict(os.environ, {
            "GITHUB_EVENT_NAME": "push", "GITHUB_REF": "refs/heads/main",
            "NIGHTFALL_FREE_RESUME": "YES", "GITHUB_RUN_ATTEMPT": "1",
            "NIGHTFALL_OWNER_START_NOW": "NO"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "authorized"):
                resume.resume_one_shot(client_factory=Mock(),
                                       hf_api_factory=Mock())


if __name__ == "__main__":
    unittest.main()
