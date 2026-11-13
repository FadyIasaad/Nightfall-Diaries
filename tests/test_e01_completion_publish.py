"""Offline release contract: immediate publishing trigger, 4 API guards, no doubles."""
import copy
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from pilot import e01_completion_publish as p


def approved_film():
    return {
        "episode": p.EPISODE, "film_ready_for_public": True,
        "shots_verified": 36, "kokoro_voices_verified": 14,
        "technical_mp4_passed": True, "duration_seconds": 150.0,
        "real_lipsync_approved": True, "cinematic_motion_approved": True,
        "blockers": [],
    }


def credentials():
    return {
        name: {"credentials_configured": True, "official_identity_verified": True,
               "permission_to_publicly_publish_tested": False,
               "public_post_created": False, "missing_names": []}
        for name in p.TARGETS
    }


def environment():
    return {"GITHUB_REF": "refs/heads/main",
            "GITHUB_EVENT_NAME": "workflow_dispatch",
            "GITHUB_RUN_ATTEMPT": "1"}


class ReleaseSafetyTests(unittest.TestCase):
    def test_real_progress_is_not_equivalent_to_full_approved_episode(self):
        _, plan = p.resume.film.scene_plan()
        state = p.resume.create_state(plan)
        state["completed"].append({"scene": 1, "part": 1})
        settings = {
            "voice_lipsync_verified": False, "cinematic_video_approved": False,
            "renderer_verified": False, "production_enabled": False,
            "publishing_implemented": False,
            "youtube_verified": False, "facebook_verified": False,
            "instagram_verified": False, "tiktok_verified": False,
        }
        with patch.object(p.resume, "load_state", return_value=state):
            with patch.object(p, "_flags",
                              return_value=(settings, {"public_publish_enabled": False})):
                report = p.film_gate()
        self.assertFalse(report["film_ready_for_public"])
        self.assertIn("FILM_NOT_36_OF_36_GENUINE_SHOTS", report["blockers"])
        self.assertIn("PUBLIC_RELEASE_NOT_ENABLED", report["blockers"])

    def test_no_public_network_or_receipts_before_quality_gate(self):
        with patch.dict(os.environ, environment(), clear=True):
            with patch.object(p, "film_gate", return_value={
                "film_ready_for_public": False,
                "blockers": ["REAL_CHARACTER_LIPSYNC_NOT_APPROVED"]}):
                read = Mock(side_effect=AssertionError("No remote public receipt"))
                writer = Mock(side_effect=AssertionError("No posts"))
                adapters = {name: Mock(side_effect=AssertionError("No public posts"))
                            for name in p.TARGETS}
                report = p.release_once(adapters=adapters,
                                        receipt_read=read, receipt_write=writer)
        self.assertEqual(report["status"], "WAITING_REAL_FILM_AND_LIPSYNC_APPROVAL")
        self.assertEqual(report["requests_submitted"], 0)
        read.assert_not_called()
        writer.assert_not_called()
        for adapter in adapters.values():
            adapter.assert_not_called()

    def test_no_platform_upload_if_one_account_missing_or_unaudited(self):
        missing = credentials()
        missing["tiktok"]["credentials_configured"] = False
        missing["tiktok"]["missing_names"] = ["TIKTOK_APP_AUDITED"]
        with patch.dict(os.environ, environment(), clear=True):
            with patch.object(p, "film_gate", return_value=approved_film()):
                with patch.object(p, "token_preflight", return_value=missing):
                    read = Mock(side_effect=AssertionError("No remote upload"))
                    result = p.release_once(receipt_read=read)
        self.assertEqual(result["status"],
                         "BLOCKED_MISSING_PLATFORM_CREDENTIALS_OR_TIKTOK_AUDIT")
        read.assert_not_called()

    def test_authorized_completion_submits_once_per_platform_and_blocks_duplicates(self):
        state = {}
        saved = []
        count = {name: 0 for name in p.TARGETS}
        def receipt_write(obj):
            saved.append(copy.deepcopy(obj))
            state.clear()
            state.update(copy.deepcopy(obj))
        def receipt_read(_):
            return copy.deepcopy(state), None
        def adapter(name):
            def send():
                count[name] += 1
                self.assertEqual(saved[-1]["destinations"][name]["phase"], "initiated")
                self.assertFalse(saved[-1]["destinations"][name]["public_confirmed"])
                return {"id": name + "-post-id", "status": "accepted_processing"}
            return send
        adapters = {name: adapter(name) for name in p.TARGETS}
        with patch.dict(os.environ, environment(), clear=True):
            with patch.object(p, "film_gate", return_value=approved_film()):
                with patch.object(p, "token_preflight", side_effect=credentials):
                    # side_effect=credentials is callable only if used with ().
                    with patch.object(p, "_read_only_platform_probe",
                                      side_effect=lambda x: x):
                        with patch.object(p.resume, "load_state", return_value={}):
                            with patch.object(p.resume.film, "scene_plan",
                                              return_value=(None, {"scenes": []})):
                                with patch.object(p, "sha256", return_value="a"*64):
                                    first = p.release_once(
                                        adapters=adapters, receipt_read=receipt_read,
                                        receipt_write=receipt_write)
                                    second = p.release_once(
                                        adapters=adapters, receipt_read=receipt_read,
                                        receipt_write=receipt_write)
        self.assertEqual(first["requests_submitted"], 4)
        self.assertEqual(first["public_posts_verified"], 0)
        self.assertEqual(second["requests_submitted"], 0)
        self.assertEqual(count, {name: 1 for name in p.TARGETS})
        self.assertTrue(all(state["destinations"][n]["phase"] == "accepted"
                            for n in p.TARGETS))
        self.assertTrue(all(not state["destinations"][n]["public_confirmed"]
                            for n in p.TARGETS))

    def test_unknown_network_result_is_not_retried_even_on_next_run(self):
        receipts = {}
        saves = []
        calls = []
        def read(_):
            return copy.deepcopy(receipts), None
        def save(obj):
            saves.append(copy.deepcopy(obj))
            receipts.clear()
            receipts.update(copy.deepcopy(obj))
        def send():
            calls.append(1)
            raise TimeoutError("unknown whether upload reached Meta")
        adapters = {"youtube": send,
                    **{name: lambda: {"id": name, "status": "accepted"}
                       for name in p.TARGETS if name != "youtube"}}
        with patch.dict(os.environ, environment(), clear=True):
            with patch.object(p, "film_gate", return_value=approved_film()):
                with patch.object(p, "token_preflight", return_value=credentials()):
                    with patch.object(p, "_read_only_platform_probe",
                                      side_effect=lambda x: x):
                        with patch.object(p.resume, "load_state", return_value={}):
                            with patch.object(p.resume.film, "scene_plan",
                                              return_value=(None, {"scenes": []})):
                                with patch.object(p, "sha256", return_value="a"*64):
                                    result = p.release_once(
                                        adapters=adapters, receipt_read=read,
                                        receipt_write=save)
                                    again = p.release_once(
                                        adapters=adapters, receipt_read=read,
                                        receipt_write=save)
        self.assertEqual(calls, [1])
        self.assertEqual(receipts["destinations"]["youtube"]["phase"], "ambiguous")
        self.assertEqual(again["requests_submitted"], 0)

    def test_tiktok_requires_confirmed_eligible_public_privacy_and_runtime(self):
        # Official video.publish user-consent preflight is a hard prerequisite.
        with patch.dict(os.environ, {
            "TIKTOK_APP_AUDITED": "false",
            "TIKTOK_CREATOR_POSTING_CONSENT": "false",
        }, clear=True):
            result = p.token_preflight()
        self.assertFalse(result["tiktok"]["credentials_configured"])
        self.assertIn("TIKTOK_APP_AUDITED", result["tiktok"]["missing_names"])

    def test_workflow_posts_on_assembly_result_not_on_a_calendar(self):
        source = (p.ROOT / ".github/workflows/nightfall_story_one_click.yml").read_text()
        section = source.split(
            "      - name: Immediately route approved complete E01 to ALL four platforms",
            1)[1].split("      - name: Archive complete technical MP4", 1)[0]
        self.assertIn("steps.assemble_film.outcome == 'success'", section)
        self.assertIn("steps.assembly.outputs.assembled == 'true'", section)
        self.assertNotIn("github.event.schedule ==", section)
        self.assertIn("python -m pilot.e01_completion_publish --mode on-completion", section)
        self.assertIn("TIKTOK_APP_AUDITED", section)
        self.assertIn("FB_EXPECTED_PAGE_ID", section)
        self.assertNotIn("YOUTUBE_VISIBILITY: public", section)
        self.assertIn("No publication time", source)

    def test_private_youtube_ambiguity_prevents_second_public_upload(self):
        state = {"youtube_private_attempt_started": True}
        with patch.object(p.youtube_preview, "_channel_preflight",
                          return_value=("UC-test", None)):
            with patch.dict(os.environ, {"YOUTUBE_EXPECTED_CHANNEL_ID": "UC-test"}):
                with self.assertRaisesRegex(RuntimeError, "no duplicate"):
                    p._youtube_public(Path("/never.mp4"), "t", "d", state)


if __name__ == "__main__":
    unittest.main()
