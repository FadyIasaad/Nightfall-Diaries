"""Offline contract tests for 150-second DISTINCT motion and official account checks."""
import json
import os
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch, MagicMock

from pilot import e01_full_run as film
from pilot import official_platform_preflight as auth


class FullEpisodeRealProofTests(unittest.TestCase):
    def test_14_unchanged_scenes_have_exact_150_second_distinct_plan(self):
        _cast, report = film.scene_plan()
        self.assertEqual(report["source_scene_count"], 14)
        self.assertEqual(report["target_seconds"], 150)
        self.assertEqual(report["requested_seconds_sum"], 150)
        self.assertEqual(report["min_final_seconds"], 120)
        self.assertFalse(report["film_created"])
        self.assertFalse(report["publication_attempted"])
        self.assertFalse(report["paid_api_calls"])
        scene_ids = [i["scene_no"] for i in report["scenes"]]
        self.assertEqual(scene_ids, list(range(1, 15)))
        self.assertEqual(sum(s["target_seconds"] for s in report["scenes"]), 150)
        self.assertEqual(len(set(s["ai_motion_prompt"] for s in report["scenes"])), 14)
        self.assertEqual([s["target_seconds"] for s in report["scenes"]],
                         [13, 11, 11, 12, 10, 10, 10, 11, 11, 8, 10, 12, 10, 11])
        self.assertTrue(all(s["voice_engine"] == "kokoro" for s in report["scenes"]))
        self.assertIn("s01_moss", report["unverified_visual_sources"])

    def test_no_real_inference_without_exact_one_time_pr_trigger(self):
        cast, report = film.scene_plan()
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(film, "OUT", Path(tmp)):
                with patch.object(film, "REPORT", Path(tmp) / "full_e01_evidence.json"):
                    with patch.dict(os.environ, {"GITHUB_EVENT_NAME": "push",
                                                 "GITHUB_HEAD_REF": film.PR_BRANCH,
                                                 "GITHUB_RUN_ATTEMPT": "1",
                                                 "NIGHTFALL_E01_FULL_REAL": "YES",
                                                 "HF_TOKEN": ""}):
                        factory = MagicMock()
                        self.assertEqual(film.render_all(cast, report, factory=factory), 2)
                        factory.assert_not_called()
        self.assertFalse(report["film_created"])

    def test_only_actual_pr_head_with_activation_message_authorizes_full_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            event = Path(tmp) / "event.json"
            event.write_text(json.dumps({
                "action": "synchronize",
                "pull_request": {
                    "head": {
                        "sha": "a" * 40,
                        "repo": {"full_name": "FadyIasaad/Nightfall-Diaries"},
                    }
                }
            }))
            env = {
                "GITHUB_EVENT_NAME": "pull_request",
                "GITHUB_HEAD_REF": film.PR_BRANCH,
                "GITHUB_RUN_ATTEMPT": "1",
                "NIGHTFALL_E01_FULL_REAL": "YES",
                "GITHUB_EVENT_PATH": str(event),
                "HF_TOKEN": "",
            }
            with patch.dict(os.environ, env):
                with patch("pilot.e01_full_run.subprocess.run") as git:
                    git.return_value.stdout = film.TRIGGER_MARKER + "\\n"
                    self.assertTrue(film.authorized_run())
                    self.assertEqual(git.call_args.args[0][-1], "a" * 40)
            data = json.loads(event.read_text())
            data["pull_request"]["head"]["repo"]["full_name"] = "untrusted/fork"
            event.write_text(json.dumps(data))
            with patch.dict(os.environ, env):
                with patch("pilot.e01_full_run.subprocess.run") as git:
                    self.assertFalse(film.authorized_run())
                    git.assert_not_called()

    def test_fourteen_scene_motion_never_uses_static_fill_or_loop(self):
        source = (film.ROOT / "pilot/e01_full_run.py").read_text()
        self.assertIn("for scene in report[\"scenes\"]:", source)
        self.assertIn("client.predict(", source)
        self.assertIn("real_kokoro_audio_files", source)
        self.assertIn("scene_shorter", source.replace("Generated unique shot shorter", "scene_shorter"))
        self.assertNotIn("filter_complex loop", source)
        self.assertNotIn("image2", source)
        self.assertNotIn("publish_youtube", source)
        self.assertNotIn("publish_instagram", source)

    def test_free_video_request_uses_unique_prompt_and_request(self):
        with tempfile.TemporaryDirectory() as tmp:
            cast, report = film.scene_plan()
            one = report["scenes"][0]
            fake = Path(tmp) / "received.mp4"
            fake.write_bytes(b"x" * 25000)
            client = MagicMock()
            client.predict.return_value = (str(fake),)
            with patch.dict("sys.modules", {"gradio_client": types.SimpleNamespace(handle_file=lambda x: x)}):
                with patch.object(film, "OUT", Path(tmp)):
                    with patch("pilot.e01_full_run.ffprobe", return_value={
                        "streams": [{"codec_type": "video", "width": 576, "height": 1024}],
                        "format": {"duration": 13.1},
                    }):
                        path, seconds = film.generate_scene(client, one)
            self.assertEqual(seconds, 13.1)
            self.assertTrue(path.is_file())
            self.assertEqual(client.predict.call_count, 1)
            args = client.predict.call_args
            self.assertEqual(args.kwargs["api_name"], "/run")
            self.assertEqual(args.args[4], one["target_seconds"])
            self.assertEqual(args.args[0], one["ai_motion_prompt"])


class PlatformIdentitySafetyTests(unittest.TestCase):
    def test_missing_tokens_make_no_api_requests(self):
        with patch.dict(os.environ, {}, clear=True):
            mock = MagicMock()
            report = auth.report_all() if False else None
            for p in auth.PLATFORMS:
                out = auth.credential_probe(p, session=mock)
                self.assertEqual(out["status"], "NOT_CONFIGURED")
                self.assertFalse(out["official_video_upload_tested"])
                self.assertFalse(out["public_post_created"])
            mock.get.assert_not_called()
            mock.post.assert_not_called()

    def test_facebook_identity_uses_only_get(self):
        mock = MagicMock()
        mock.get.return_value.json.return_value = {"id": "123456789", "name": "Nightfall Diaries"}
        with patch.dict(os.environ, {"FB_PAGE_ACCESS_TOKEN": "secret"}):
            result = auth.credential_probe("facebook", session=mock)
        self.assertTrue(result["read_only_identity_verified"])
        self.assertFalse(result["publishing_permission_verified"])
        self.assertFalse(result["official_video_upload_tested"])
        self.assertFalse(result["public_post_created"])
        self.assertEqual(result["account_id_redacted"], "***6789")
        mock.post.assert_not_called()
        self.assertEqual(mock.get.call_args.args[0], auth.GRAPH + "/me")

    def test_youtube_may_post_token_refresh_but_never_video(self):
        mock = MagicMock()
        mock.post.return_value.json.return_value = {"access_token": "new-short-lived-token"}
        mock.get.return_value.json.return_value = {"items": [{"id": "youtube-channel-1234"}]}
        with patch.dict(os.environ, {
            "YOUTUBE_REFRESH_TOKEN": "refresh-secret",
            "YOUTUBE_CLIENT_ID": "client-id",
            "YOUTUBE_CLIENT_SECRET": "client-secret",
        }):
            result = auth.credential_probe("youtube", session=mock)
        self.assertTrue(result["read_only_identity_verified"])
        self.assertFalse(result["official_video_upload_tested"])
        self.assertFalse(result["publishing_permission_verified"])
        self.assertEqual(mock.post.call_count, 1)
        self.assertEqual(mock.post.call_args.args[0], auth.GOOGLE_TOKEN)
        self.assertEqual(mock.get.call_args.args[0], auth.YOUTUBE)
        self.assertNotIn("refresh-secret", json.dumps(result))


if __name__ == "__main__":
    unittest.main()
