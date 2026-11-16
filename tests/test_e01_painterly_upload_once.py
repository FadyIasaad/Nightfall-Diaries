"""Offline receipt and safety tests for exact owner-approved painterly E01 upload."""
import base64
import json
import sys
import unittest
from unittest.mock import MagicMock, Mock, patch

# Baseline offline CI does not install requests. The actual upload workflow
# installs the genuine library; unit tests must never perform HTTP calls.
try:
    import requests  # noqa: F401
except ModuleNotFoundError:
    sys.modules["requests"] = MagicMock()

from pilot import e01_painterly_upload_once as release


class PainterlyReleaseSafety(unittest.TestCase):
    def test_no_owner_release_approval_means_no_network_or_media(self):
        with patch.dict("os.environ", {"OWNER_AUTHORIZED_E01_PUBLIC_UPLOAD":"NO"}), \
             patch.object(release, "verified_source", side_effect=AssertionError("no source read")), \
             self.assertRaisesRegex(RuntimeError, "EXPLICIT_USER_APPROVAL"):
            release.execute()

    def test_exact_source_sha_and_separate_publishing_receipt_file(self):
        self.assertEqual(len(release.SRC_SHA),64)
        self.assertIn("_painterly_v2.json",release.RECEIPT_PATH)
        self.assertTrue(release.FILM.name.endswith("_PUBLIC.mp4"))
        self.assertEqual(release.TAG,"nightfall-e01-painterly-2p5d-20261116")

    def test_new_receipt_is_not_false_claim_of_four_platform_uploads(self):
        res=Mock(status_code=404)
        with patch.object(release.requests,"get",return_value=res), \
             patch.dict("os.environ",{"GH_TOKEN":"dummy-token"}):
            record,sha=release.read_receipt()
        self.assertIsNone(sha)
        self.assertEqual(record["facebook"]["phase"],"not_attempted")
        self.assertEqual(record["instagram"]["phase"],"not_attempted")
        self.assertTrue(record["youtube"]["phase"].startswith("blocked"))
        self.assertTrue(record["tiktok"]["phase"].startswith("blocked"))
        self.assertEqual(record["film_source_sha256"],release.SRC_SHA)

    def test_publish_receipt_file_uses_exact_sha_and_expected_base(self):
        old={"film_source_sha256":release.SRC_SHA,"facebook":{"phase":"initiated_no_auto_retry"}}
        resp=Mock()
        resp.json.return_value={"content":{"sha":"newsha"}}
        with patch.object(release.requests,"put",return_value=resp) as sent, \
             patch.dict("os.environ",{"GH_TOKEN":"example-token"}):
            self.assertEqual(release.save_receipt(old,"oldsha"),"newsha")
        args=sent.call_args
        body=args.kwargs["json"]
        self.assertEqual(body["sha"],"oldsha")
        self.assertEqual(body["branch"],"main")
        restored=json.loads(base64.b64decode(body["content"]))
        self.assertEqual(restored["facebook"]["phase"],"initiated_no_auto_retry")

    def test_user_scope_matches_only_expected_nightfall_page(self):
        # Facebook-specific page resolver is deliberately used rather than
        # selecting the arbitrary first /me/accounts Page or user profile.
        self.assertIn("Nightfall",release.DESCRIPTION)
        self.assertIn("2.5D",release.DESCRIPTION)
        self.assertEqual(release.GRAPH_VIDEO,"https://graph-video.facebook.com/v25.0")

    def test_generic_api_error_never_exposes_oauth_body(self):
        err=ValueError("secret token should never be copied")
        self.assertEqual(release.clean_error(err),{
            "failure_type":"ValueError","http_status":None
        })


if __name__=="__main__":
    unittest.main()
