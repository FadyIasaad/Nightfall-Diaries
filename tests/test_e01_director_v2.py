"""Nightfall V2 QA: original story sets, richer Moss, movement and no-gap timing."""
import importlib.util
import math
import tempfile
import unittest
import wave
from pathlib import Path

HAS_PIL=importlib.util.find_spec("PIL") is not None
HAS_CV2=importlib.util.find_spec("cv2") is not None

@unittest.skipUnless(HAS_PIL and HAS_CV2,"Dedicated V2 workflow installs art dependencies")
class RealV2ArtTests(unittest.TestCase):
    def test_story_environments_match_canonical_actions(self):
        from studio.e01_v2_art_direction import SETS
        self.assertEqual(set(SETS),set(range(1,15)))
        self.assertEqual(SETS[1][0],"burning_grove")
        self.assertEqual(SETS[5][0],"feather_closeup")
        self.assertEqual(SETS[8][0],"cliff_ledge")
        self.assertEqual(SETS[10][0],"dangling_roots")
        self.assertEqual(SETS[11][0],"rescue_ledge")
        self.assertEqual(SETS[12][0],"blue_smoke_corridor")
        self.assertEqual(SETS[14][0],"mystery_silhouette")
    def test_scene_art_is_not_a_repeated_blurry_background(self):
        from studio.e01_v2_art_direction import story_set
        from PIL import ImageChops,ImageStat
        a=story_set(1)
        b=story_set(8)
        c=story_set(12)
        self.assertEqual(a.size,(360,640))
        self.assertGreater(max(ImageStat.Stat(ImageChops.difference(a,b)).mean),15)
        self.assertGreater(max(ImageStat.Stat(ImageChops.difference(b,c)).mean),12)
    def test_articulated_moss_is_visually_richer_and_moves(self):
        from studio.e01_v2_art_direction import moss_parts,frame
        from PIL import ImageChops,ImageStat
        shell,neck,head,legs=moss_parts()
        self.assertEqual(len(legs),4)
        self.assertEqual(shell.size,(420,340))
        self.assertIsNotNone(shell.getbbox())
        a=frame(6,0,0.1,8,"Stay close","s01_moss",["s01_moss"],"Moss emerges from smoke")
        b=frame(6,.75,.8,8,"Stay close","s01_moss",["s01_moss"],"Moss emerges from smoke")
        self.assertEqual(a.size,(360,640))
        self.assertGreater(max(ImageStat.Stat(ImageChops.difference(a,b)).mean),.5)
    def test_painterly_ember_still_uses_the_approved_reference(self):
        from studio.e01_v2_art_direction import frame
        a=frame(9,.5,.3,7,"Look down","s01_ember",["s01_ember"],"Forest floor crumbles")
        self.assertEqual(a.size,(360,640))
        self.assertGreater(len(set(a.resize((20,35)).getdata())),100)

@unittest.skipUnless(HAS_PIL and HAS_CV2,"Dedicated V2 workflow installs art dependencies")
class DirectorCutTimingTests(unittest.TestCase):
    def test_180_seconds_exactly_and_14_live_shots(self):
        from pilot.e01_director_v2 import frame_budget
        with tempfile.TemporaryDirectory() as root:
            voices={}
            for i in range(1,15):
                p=Path(root)/f"voice_{i:02d}.wav"
                with wave.open(str(p),"wb") as f:
                    f.setnchannels(1);f.setsampwidth(2);f.setframerate(24000)
                    f.writeframes(b"\x00\x00"*(24000*(8 if i%3==0 else 7)))
                voices[i]=p
            count,times=frame_budget(voices)
            self.assertEqual(len(count),14)
            self.assertEqual(sum(count),2160)
            self.assertEqual(len(times),14)
            self.assertTrue(all(f>math.ceil(s*12) for f,s in zip(count,times)))
    def test_sound_bed_is_continuous_real_original_audio(self):
        from pilot.e01_director_v2 import sound_bed
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)/"fx.wav"
            sound_bed(9,12,p)
            with wave.open(str(p),"rb") as f:
                self.assertEqual(f.getnframes(),24000)
                self.assertEqual(f.getframerate(),24000)
                data=f.readframes(f.getnframes())
                self.assertNotEqual(data,b"\x00"*len(data))

if __name__=="__main__":
    unittest.main()
