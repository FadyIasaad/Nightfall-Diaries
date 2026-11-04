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

    def test_reject_fake_tiny_video(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"candidate.mp4"
            p.write_bytes(b"not a real video")
            with self.assertRaisesRegex(RuntimeError, "small"):
                check_media(p)
