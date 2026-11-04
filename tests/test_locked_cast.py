import json
import tempfile
import unittest
from pathlib import Path
from studio.continuity import locked_cast,sha256

class LockedCastTests(unittest.TestCase):
    def test_all_original_characters_keep_hash_locked_images_and_neural_voices(self):
        for season in ("S01_the_last_little_fox","S02_the_boy_who_forgot_tomorrow"):
            cast=locked_cast(season)
            self.assertEqual(len(cast),5)
            self.assertEqual(len(set(c["voice"]["voice_id"] for c in cast.values())),5)

    def test_unknown_season_rejected(self):
        with self.assertRaises(ValueError):
            locked_cast("S03_unapproved")

    def make_fake_cast(self,root,correct_image=True,correct_voice=True):
        folder=root/"seasons"/"S01_the_last_little_fox"/"characters"
        image_folder=folder/"test"
        image_folder.mkdir(parents=True)
        (root/"studio").mkdir()
        photo=image_folder/"cloud_reference.png"
        photo.write_bytes(b"original reference")
        registry={"characters":[{"id":"test","voice":{"engine":"kokoro","voice_id":"am_puck","lang":"en-US","speed":1.0}}]}
        (folder/"character_registry.json").write_text(json.dumps(registry))
        (folder/"cloud_reference_locks.json").write_text(json.dumps({"test":sha256(photo) if correct_image else "0"*64}))
        profile={"engine":"kokoro","voice_id":"am_puck" if correct_voice else "am_fenrir","lang":"en-US","speed":1.0}
        (root/"studio/voice_profile_locks.json").write_text(json.dumps({"S01_the_last_little_fox":{"test":profile}}))

    def test_reference_tampering_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            self.make_fake_cast(root,correct_image=False)
            with self.assertRaisesRegex(ValueError,"CHARACTER_REFERENCE_DRIFT"):
                locked_cast("S01_the_last_little_fox",root)

    def test_voice_switch_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            self.make_fake_cast(root,correct_voice=False)
            with self.assertRaisesRegex(ValueError,"VOICE_PROFILE_DRIFT"):
                locked_cast("S01_the_last_little_fox",root)
