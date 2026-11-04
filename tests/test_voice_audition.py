import unittest
from studio.voice_audition import voice_definitions

class VoiceAuditionsTests(unittest.TestCase):
    def test_fox_voice_cast_has_five_distinct_locked_roles(self):
        cast=voice_definitions("S01_the_last_little_fox")
        self.assertEqual(len(cast),5)
        self.assertEqual(len({c["voice_id"] for c in cast}),5)
        self.assertTrue(all(c["line"] and c["direction"] for c in cast))

    def test_human_season_voice_cast_exists(self):
        self.assertEqual(len(voice_definitions("S02_the_boy_who_forgot_tomorrow")),5)

    def test_unapproved_new_season_rejected(self):
        with self.assertRaises(ValueError):
            voice_definitions("S03_unapproved")
