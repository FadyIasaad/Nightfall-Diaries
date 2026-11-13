import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from studio.quality_gate import check_media

class MediaGateTests(unittest.TestCase):
    def test_reject_missing_file(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(RuntimeError, "missing"):
                check_media(Path(folder)/"missing.mp4")

    def test_reject_unsupported_mode(self):
        with self.assertRaises(ValueError):
            check_media("x.mp4", mode="slideshow")

    def test_full_episodes_require_at_least_two_minutes(self):
        import json
        from unittest.mock import MagicMock
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "E01_full.mp4"
            path.write_bytes(b"valid-looking-fake-payload" * 1000)
            media = {
                "streams": [
                    {"codec_type": "video", "codec_name": "h264",
                     "width": 720, "height": 1280},
                    {"codec_type": "audio", "codec_name": "aac"}
                ],
                "format": {"duration": "119.99"}
            }
            fake = MagicMock()
            fake.stdout = json.dumps(media)
            with patch("studio.quality_gate.subprocess.run", return_value=fake):
                with self.assertRaisesRegex(RuntimeError, "120-180"):
                    check_media(path, mode="full")
                for seconds in (120, 150, 180):
                    media["format"]["duration"] = str(seconds)
                    fake.stdout = json.dumps(media)
                    result = check_media(path, mode="full")
                    self.assertEqual(result["duration_seconds"], seconds)
                    self.assertFalse(result["cinematic_and_lipsync_review_passed"])
                media["format"]["duration"] = "180.01"
                fake.stdout = json.dumps(media)
                with self.assertRaisesRegex(RuntimeError, "120-180"):
                    check_media(path, mode="full")

    def test_reject_fake_tiny_video(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"candidate.mp4"
            p.write_bytes(b"not a real video")
            with self.assertRaisesRegex(RuntimeError, "small"):
                check_media(p)
