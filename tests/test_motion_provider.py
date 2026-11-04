import json
import unittest
from unittest.mock import patch

from studio.motion_provider import ENDPOINT, SPACE_ID, probe, settings
from studio.free_video import find_video

class ZeroBudgetProviderTests(unittest.TestCase):
    def test_empty_github_variables_use_documented_free_space(self):
        space, endpoint, args = settings({"HF_VIDEO_SPACE":"","HF_VIDEO_ENDPOINT":"",
            "HF_VIDEO_ARGS_JSON":""})
        self.assertEqual(space, SPACE_ID)
        self.assertEqual(endpoint, ENDPOINT)
        self.assertEqual(len(args),9)
        self.assertEqual(args[0:2],["$image","$prompt"])
        self.assertEqual(args[4],5.0)

    def test_custom_unverified_provider_rejected(self):
        with self.assertRaisesRegex(ValueError,"reviewed zero-cost"):
            settings({"HF_VIDEO_SPACE":"paid-provider/some-api"})

    def test_invalid_endpoint_arguments_rejected(self):
        with self.assertRaises(ValueError):
            settings({"HF_VIDEO_ARGS_JSON":'["$image", "$prompt"]'})
        with self.assertRaises(ValueError):
            settings({"HF_VIDEO_ARGS_JSON":'not-json'})

    def test_read_only_probe_requires_expected_endpoint(self):
        hub = {"runtime":{"stage":"RUNNING","hardware":{"current":"zero-a10g"}}}
        api = {"named_endpoints":{ENDPOINT:{"parameters":[{}]*9}}}
        with patch("studio.motion_provider._read_json",side_effect=[hub,api]) as call:
            result=probe()
        self.assertEqual(result["state"],"READY_FOR_ONE_QUOTA_LIMITED_TEST")
        self.assertFalse(result["inference_attempted"])
        self.assertEqual(call.call_count,2)

    def test_stop_if_space_or_endpoint_changed(self):
        with patch("studio.motion_provider._read_json",
                   side_effect=[{"runtime":{"stage":"SLEEPING"}},{}]):
            self.assertEqual(probe()["state"],"BLOCKED")
        with patch("studio.motion_provider._read_json",
                   side_effect=[{"runtime":{"stage":"RUNNING"}},{"named_endpoints":{}}]):
            self.assertEqual(probe()["state"],"BLOCKED")

    def test_static_placeholder_is_not_video(self):
        self.assertIsNone(find_video({"path":"/not/a/real/motion.mp4"}))
