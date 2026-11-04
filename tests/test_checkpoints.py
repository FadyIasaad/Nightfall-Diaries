import tempfile
import unittest
from pathlib import Path
from studio.checkpoints import fingerprint,paths,restore_clip,save_clip

class SavedMotionTests(unittest.TestCase):
    def test_reuse_requires_same_voice_character_reference_and_prompt(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            source=root/"source.mp4";source.write_bytes(b"A"*12000)
            expected=fingerprint({"voice":"am_puck","image":"original-hash","prompt":"run"})
            save_clip("S01_the_last_little_fox_E01","full",1,0,expected,source,root/"cache")
            target=root/"dest.mp4"
            self.assertTrue(restore_clip("S01_the_last_little_fox_E01","full",1,0,expected,target,root/"cache"))
            self.assertEqual(target.read_bytes(),source.read_bytes())
            self.assertFalse(restore_clip("S01_the_last_little_fox_E01","full",1,0,fingerprint({"voice":"am_fenrir"}),target,root/"cache"))

    def test_detect_modified_cache_and_unsafe_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            source=root/"source.mp4";source.write_bytes(b"B"*12000)
            key=fingerprint({"scene":1})
            save_clip("S01_the_last_little_fox_E02","full",2,0,key,source,root/"cache")
            video,_=paths("S01_the_last_little_fox_E02","full",2,0,root/"cache")
            video.write_bytes(b"C"*12000)
            self.assertFalse(restore_clip("S01_the_last_little_fox_E02","full",2,0,key,root/"dest.mp4",root/"cache"))
            with self.assertRaises(ValueError):
                paths("../../outside","full",0,0,root/"cache")
