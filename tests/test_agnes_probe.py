"""Read-only Agnes probe contract; no billable video even with a secret."""
import json
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from studio.agnes_probe import API_MODELS_URL, ONLY_CANDIDATE, probe
from studio.restore import ROOT


class _Response:
    status = 200
    def __init__(self, payload):
        self.payload = payload
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, _count):
        return self.payload


class AgnesProbeSafety(unittest.TestCase):
    def test_missing_secret_no_network_calls(self):
        def forbidden(*args, **kwargs):
            raise AssertionError("No network request without a secret")
        result = probe("", opener=forbidden)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertFalse(result["submitted_generation_task"])

    def test_model_list_does_not_approve_video_or_price(self):
        def fake(request, timeout):
            self.assertEqual(request.method, "GET")
            self.assertEqual(request.full_url, API_MODELS_URL)
            self.assertEqual(timeout, 15)
            return _Response(json.dumps({
                "object": "list",
                "data": [{"id": ONLY_CANDIDATE}, {"id": "other-model"}],
            }).encode())
        result = probe("dummy-for-test-only", opener=fake)
        self.assertEqual(result["status"], "CONNECTED_PRICING_UNVERIFIED")
        self.assertTrue(result["target_model_listed"])
        for flag in ("current_zero_price_verified", "zero_card_auto_billing_disabled_verified",
                     "free_recurrent_quota_verified", "rendered_video",
                     "submitted_generation_task", "video_generation_authorized",
                     "uploaded_to_any_platform"):
            self.assertFalse(result[flag])

    def test_other_model_not_silently_substituted(self):
        result = probe("dummy", opener=lambda request, timeout:
                       _Response(b'{"data":[{"id":"agnes-video-2.5"}]}'))
        self.assertEqual(result["status"], "BLOCKED")
        self.assertFalse(result["target_model_listed"])

    def test_only_manual_mode_can_access_secret(self):
        yml = (ROOT / ".github/workflows/nightfall.yml").read_text(encoding="utf-8")
        self.assertIn("inputs.mode == 'engine_probe' && inputs.action == 'Check setup'", yml)
        self.assertIn("AGNES_API_KEY: ${{ secrets.AGNES_API_KEY }}", yml)
        self.assertNotIn("POST /v1/videos", yml)
        self.assertEqual(yml.count("runs-on: ubuntu-latest"), 1)
        code = (ROOT / "studio/agnes_probe.py").read_text(encoding="utf-8")
        self.assertIn('method="GET"', code)
        self.assertNotIn('method="POST"', code)
        self.assertNotIn("videos/generate", code)
        self.assertNotIn("recharge", code)
