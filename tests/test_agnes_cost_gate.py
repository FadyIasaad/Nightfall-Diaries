"""Offline safety tests: exact promo price, no POST, no generation."""
import json
import unittest

from studio.agnes_cost_gate import (
    MODEL, PRICING_URL, LTX_METADATA_URL, fetch_public_get,
    flash_public_trial_is_zero, inspect,
)


class _Response:
    status = 200
    def __init__(self, payload):
        self.payload = payload
    def __enter__(self):
        return self
    def __exit__(self, *_):
        return False
    def read(self, _limit):
        return self.payload


PRICING = """## Video models
<table><tr><td>`agnes-video-2.5`</td><td>720P</td>
<td>`$0.025 / second`</td><td>`$0.025 / second`</td></tr>
<tr><td>`agnes-video-2.5-flash`</td><td>720P video duration</td>
<td>`$0.025 / second`</td><td>**`$0 / second`**</td></tr></table>
## Billing notes
"""


class TestAgnesCostGate(unittest.TestCase):
    def test_exact_flash_row_required(self):
        self.assertTrue(flash_public_trial_is_zero(PRICING))
        self.assertFalse(flash_public_trial_is_zero(
            PRICING.replace("**`$0 / second`**", "`$0.025 / second`")
        ))
        self.assertFalse(flash_public_trial_is_zero(
            PRICING.replace(MODEL, "agnes-video-2.5")
        ))
        self.assertFalse(flash_public_trial_is_zero("Flash is free."))

    def test_public_get_only_and_url_allowlist(self):
        def opener(request, timeout):
            self.assertEqual(request.method, "GET")
            self.assertEqual(request.full_url, PRICING_URL)
            self.assertEqual(timeout, 20)
            self.assertNotIn("Authorization", request.headers)
            return _Response(PRICING.encode())
        self.assertIn("Video models", fetch_public_get(PRICING_URL, opener))
        with self.assertRaises(ValueError):
            fetch_public_get("https://example.com/unknown", opener)

    def test_price_and_ltx_available_still_cannot_authorize_generation(self):
        urls = []
        def opener(request, timeout):
            self.assertEqual(request.method, "GET")
            self.assertNotIn("Authorization", request.headers)
            urls.append(request.full_url)
            if request.full_url == PRICING_URL:
                return _Response(PRICING.encode())
            if request.full_url == LTX_METADATA_URL:
                return _Response(json.dumps({
                    "id": "Lightricks/LTX-2.5",
                    "runtime": {"stage": "RUNNING"},
                }).encode())
            raise AssertionError("Unexpected request")
        report = inspect(opener)
        self.assertEqual(urls, [PRICING_URL, LTX_METADATA_URL])
        self.assertEqual(report["status"], "BLOCKED_ACCOUNT_BILLING_UNVERIFIED")
        self.assertTrue(report["public_promotional_zero_price_confirmed"])
        self.assertTrue(report["fallback"]["metadata_available"])
        self.assertFalse(report["account_default_key_type_verified"])
        self.assertFalse(report["enforced_hard_zero_spend_cap_verified"])
        self.assertFalse(report["generation_authorized"])
        self.assertFalse(report["generation_request_sent"])
        self.assertFalse(report["publish_request_sent"])
        self.assertEqual(report["prepared_not_submitted_proof"]["model"], MODEL)

    def test_bad_sources_do_not_authorize_anything(self):
        def opener(request, timeout):
            if request.full_url == PRICING_URL:
                return _Response(b"new paid price")
            raise OSError("offline")
        report = inspect(opener)
        self.assertFalse(report["public_promotional_zero_price_confirmed"])
        self.assertFalse(report["generation_authorized"])


if __name__ == "__main__":
    unittest.main()
