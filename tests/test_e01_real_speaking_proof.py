"""Contract for $0 E01 first episode voice and daily quality-gate runner."""
import pathlib
import unittest
from pilot import e01_real_speaking_proof as trial

ROOT = pathlib.Path(__file__).resolve().parents[1]


class FirstEpisodeSpeakingProofTests(unittest.TestCase):
    def test_locked_reference_identity_and_original_lines(self):
        self.assertEqual(len(trial.SOURCE_SHA256), 64)
        self.assertTrue(trial.SOURCE.is_file())
        self.assertEqual(trial.sha(trial.SOURCE), trial.SOURCE_SHA256)
        data = (ROOT / "seasons/S01_the_last_little_fox/screenplays/E01.json").read_text()
        self.assertIn("Moss? Can anyone hear me?", data)
        self.assertEqual(trial.SPACE, "henrybit/SadTalker-Demo")

    def test_no_fallback_or_billable_secrets(self):
        code = pathlib.Path(trial.__file__).read_text()
        self.assertIn("BLOCKED_PROVIDER_CREDENTIAL_COULD_INCURE_COST", code)
        self.assertIn("MODEL_NO_LONGER_RUNNING_ON_VERIFIED_FREE_ZEROGPU", code)
        self.assertEqual(trial.MAX_FREE_REQUESTS, 1)
        self.assertNotIn("publish_video(", code)
        self.assertNotIn("studio.e01_v4_art_direction", code)

    def test_movie_validator_refuses_missing_video(self):
        with self.assertRaises(Exception):
            trial.validate_movie(ROOT / "this_movie_does_not_exist.mp4")


if __name__ == "__main__":
    unittest.main()
