"""The narrator speaks off-screen; actual visible characters must drive the motion input."""
import unittest
from studio.continuity import locked_cast
from studio.real_film import visual_lead, motion_prompt
from studio.screenplay import load_screenplay

class NarratorSceneRenderTests(unittest.TestCase):
    def test_all_first_two_episodes_have_visual_and_voice_separation(self):
        series="S01_the_last_little_fox"
        cast=locked_cast(series)
        for ep in ("E01","E02"):
            scenes=load_screenplay(series+"_"+ep)["scenes"]
            for scene in scenes:
                with self.subTest(ep=ep,speaker=scene["character_id"]):
                    lead=visual_lead(scene,cast)
                    self.assertTrue(cast[lead]["visual"])
                    self.assertIn(lead,scene["visible"])
                    prompt=motion_prompt(scene,cast,lead)
                    self.assertIsInstance(prompt,str)
                    self.assertIn(cast[lead]["visual"],prompt)
                    self.assertNotIn("None",prompt)
                    if scene["character_id"].endswith("_narrator"):
                        self.assertNotEqual(lead,scene["character_id"])
                        self.assertIn("voice-over",prompt)

    def test_narrator_uses_visible_moss_not_default_ember(self):
        cast=locked_cast("S01_the_last_little_fox")
        scene={"character_id":"s01_narrator","visible":["s01_moss"],"text":"Moss arrived.","direction":"Moss walks."}
        self.assertEqual(visual_lead(scene,cast),"s01_moss")
        self.assertIn("Moss walks.",motion_prompt(scene,cast,"s01_moss"))

    def test_empty_unapproved_or_invisible_cast_blocks_before_spending_quota(self):
        cast=locked_cast("S01_the_last_little_fox")
        with self.assertRaisesRegex(ValueError,"visible"):
            visual_lead({"character_id":"s01_narrator","visible":[]},cast)
        with self.assertRaisesRegex(ValueError,"Unapproved"):
            visual_lead({"character_id":"s01_narrator","visible":["s03_invented"]},cast)
        with self.assertRaisesRegex(ValueError,"visible"):
            visual_lead({"character_id":"s01_ember","visible":["s01_narrator"]},cast)

    def test_dialogue_line_keeps_original_locked_speaker(self):
        cast=locked_cast("S01_the_last_little_fox")
        scene={"character_id":"s01_moss","visible":["s01_ember"],"text":"Stay close.","direction":"Ember listens."}
        self.assertEqual(visual_lead(scene,cast),"s01_ember")
        prompt=motion_prompt(scene,cast,"s01_ember")
        self.assertIn("Off-screen dialogue by s01_moss",prompt)
        self.assertIn("Stay close.",prompt)
