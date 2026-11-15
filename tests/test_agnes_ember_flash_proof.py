"""Offline safeguards for one real Agnes video test; never use the service."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pilot import agnes_ember_flash_proof as agnes


class TestAgnesEmberOneClip(unittest.TestCase):
    def test_request_is_locked_to_only_one_free_candidate_with_actual_image(self):
        payload = agnes.build_request()
        self.assertEqual(payload["model"], "agnes-video-2.5-flash")
        self.assertEqual(payload["mode"], "reference")
        self.assertEqual(payload["seconds"], "5")
        self.assertEqual(payload["size"], "720P")
        self.assertEqual(payload["aspect_ratio"], "9:16")
        self.assertEqual(payload["n"], 1)
        self.assertEqual(payload["images"], [agnes.IMAGE_URL])
        self.assertNotIn("videos", payload)
        self.assertNotIn("payment", payload)
        self.assertEqual(hashlib.sha256(agnes.CINEMATIC_IMAGE.read_bytes()).hexdigest(),
                         agnes.SOURCE_SHA)

    def test_prepare_has_zero_model_calls_even_with_a_secret(self):
        with tempfile.TemporaryDirectory() as folder, \
             patch.object(agnes, "OUTPUT", Path(folder)), \
             patch.object(agnes, "STATUS_FILE", Path(folder) / "status.json"), \
             patch.dict("os.environ", {"AGNES_API_KEY": "not-real"}, clear=False), \
             patch.object(agnes, "urlopen", side_effect=AssertionError("No network allowed")), \
             patch.object(agnes, "eligibility", side_effect=AssertionError("No account call")):
            report = agnes.run(None)
            self.assertEqual(report["status"], "PREPARED_NOT_SUBMITTED")
            self.assertEqual(report["post_requests_attempted"], 0)
            self.assertFalse(report["public_publish"])
            self.assertTrue(Path(folder, "status.json").is_file())

    def test_run_requires_owner_confirmation_before_any_api_or_price_read(self):
        with patch.object(agnes, "fetch_public_get", side_effect=AssertionError("No GET")), \
             self.assertRaisesRegex(RuntimeError, "NOT_OWNER_CONFIRMED"):
            agnes.eligibility("example-only", "NOT_VERIFIED")

    def test_no_key_rejected_even_with_exact_confirmation(self):
        with patch.object(agnes, "fetch_public_get",
                          side_effect=AssertionError("No GET")), \
             self.assertRaisesRegex(RuntimeError, "SECRET_UNAVAILABLE"):
            agnes.eligibility("", agnes.CONFIRMATION)

    def test_only_exact_official_flash_price_and_model_can_pass(self):
        with patch.object(agnes, "fetch_public_get", return_value="official-doc"), \
             patch.object(agnes, "flash_public_trial_is_zero", return_value=True), \
             patch.object(agnes, "probe", return_value={"target_model_listed": True}):
            self.assertTrue(agnes.eligibility("example-only", agnes.CONFIRMATION))
        with patch.object(agnes, "fetch_public_get", return_value="changed"), \
             patch.object(agnes, "flash_public_trial_is_zero", return_value=False), \
             patch.object(agnes, "probe", side_effect=AssertionError("No GET catalog")), \
             self.assertRaisesRegex(RuntimeError, "NOT_ZERO"):
            agnes.eligibility("example-only", agnes.CONFIRMATION)

    def test_wrong_source_sha_rejected_no_fallback(self):
        with patch.object(agnes, "SOURCE_SHA", "0" * 64), \
             self.assertRaisesRegex(RuntimeError, "HASH_MISMATCH"):
            agnes.build_request()

    def test_source_url_pinned_to_immutable_commit(self):
        self.assertIn(agnes.IMAGE_REVISION, agnes.IMAGE_URL)
        self.assertEqual(agnes.IMAGE_URL.count("raw.githubusercontent.com"), 1)
        self.assertTrue(agnes.IMAGE_URL.endswith(".webp"))


if __name__ == "__main__":
    unittest.main()
