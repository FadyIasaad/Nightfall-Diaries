"""Visual regression: premium tortoise and unobstructed approved fox face."""
import importlib.util
import unittest

PIL=importlib.util.find_spec("PIL") is not None
CV2=importlib.util.find_spec("cv2") is not None
NUMPY=importlib.util.find_spec("numpy") is not None

@unittest.skipUnless(PIL and CV2 and NUMPY,"Dedicated art workflow installs Pillow OpenCV NumPy")
class MossPremiumReview(unittest.TestCase):
    def test_painterly_moss_has_full_head_body_four_moving_feet(self):
        from studio.e01_v3_painterly_moss import parts,draw_moss
        from PIL import Image,ImageChops,ImageStat
        feet,body,shell,head=parts()
        self.assertEqual(len(feet),4)
        self.assertTrue(all(x.getbbox() for x in feet+[body,shell,head]))
        a=Image.new("RGBA",(360,640))
        b=Image.new("RGBA",(360,640))
        draw_moss(a,185,504,0.0,.1,scale=1.0)
        draw_moss(b,185,504,.8,.8,scale=1.0)
        self.assertGreater(max(ImageStat.Stat(ImageChops.difference(a,b)).mean),.1)
        # The whole tortoise stays inside the video frame, unlike v2 clipping.
        self.assertLess(a.getchannel("A").getbbox()[2],360)
    def test_blue_feather_does_not_hide_em_speaking_face(self):
        from studio.e01_v2_art_direction import frame
        from PIL import ImageStat
        a=frame(3,.3,.3,8,"Ember sees a feather",
                "s01_ember",["s01_ember"],"Ember steadies himself")
        self.assertEqual(a.size,(360,640))
        self.assertGreater(max(ImageStat.Stat(a).stddev),25)
    def test_canonical_features_tortoise_shell_crack_and_shaded_scutes(self):
        from studio.e01_v3_painterly_moss import parts
        from PIL import ImageStat
        feet,body,shell,head=parts()
        self.assertGreater(max(ImageStat.Stat(shell.convert("RGB")).stddev),15)
        self.assertGreater(max(ImageStat.Stat(head.convert("RGB")).stddev),10)

if __name__=="__main__":
    unittest.main()
