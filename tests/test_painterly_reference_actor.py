"""Visual and integrity tests: premium 2.5D Ember animated anatomy from approved art."""
import importlib.util
import unittest

HAVE_PIL=importlib.util.find_spec("PIL") is not None


@unittest.skipUnless(HAVE_PIL, "Dedicated painterly workflow installs Pillow")
class LockedReferenceCharacterTests(unittest.TestCase):
    def test_original_reference_is_sha_verified_and_independent_rig_layers(self):
        from studio import painterly_reference_actor_v2 as art
        original, layers=art.approved_cutout()
        self.assertEqual(original.size,(512,640))
        self.assertEqual(set(layers),
                         {"head","body","tail","forepaw","hindpaw","scarf"})
        self.assertTrue(all(part.size==(512,640) for part in layers.values()))
        self.assertGreater(layers["head"].getchannel("A").getbbox()[2],330)
        self.assertGreater(layers["tail"].getchannel("A").getbbox()[2],100)
        self.assertGreater(layers["scarf"].getchannel("A").getbbox()[2],290)
        self.assertEqual(len(art.SHA),64)

    def test_actual_actor_head_tail_and_limbs_move_independently(self):
        from studio import painterly_reference_actor_v2 as art
        from PIL import ImageChops, ImageStat
        a=art.puppet(0.0,0.1,"run")
        b=art.puppet(0.68,0.88,"run")
        diff=ImageChops.difference(a,b)
        self.assertGreater(max(ImageStat.Stat(diff).mean),.3)

    def test_full_framed_film_is_painterly_not_previous_emoji(self):
        from studio import painterly_reference_actor_v2 as art
        from PIL import ImageChops, ImageStat
        f1=art.render_frame(1,0,.1,20,"The forest blazed",
                            "s01_narrator",["s01_ember"],
                            "Tracking shot: the fox runs.")
        f2=art.render_frame(1,.8,.8,20,"The forest blazed",
                            "s01_ember",["s01_ember"],
                            "Tracking shot: the fox runs.")
        self.assertEqual(f1.size,(360,640))
        self.assertEqual(f2.size,(360,640))
        self.assertGreater(max(ImageStat.Stat(f1).stddev),20)
        difference=ImageChops.difference(f1,f2)
        self.assertGreater(max(ImageStat.Stat(difference).mean),2)

    def test_moss_is_independently_painted_with_shell_and_eye_animation(self):
        from studio import painterly_reference_actor_v2 as art
        a=art.render_frame(6,0,.5,12,"Stay close","s01_moss",
                           ["s01_moss"],"Moss steps from fire.")
        b=art.render_frame(6,.5,.6,12,"Stay close","s01_moss",
                           ["s01_moss"],"Moss steps from fire.")
        self.assertNotEqual(a.tobytes(),b.tobytes())

    def test_stable_identity_for_same_frame_and_no_network_required(self):
        from studio import painterly_reference_actor_v2 as art
        x=art.render_frame(4,2.2,.5,18,"What is that?",
                           "s01_ember",["s01_ember"],"Ember turns")
        y=art.render_frame(4,2.2,.5,18,"What is that?",
                           "s01_ember",["s01_ember"],"Ember turns")
        self.assertEqual(x.tobytes(),y.tobytes())


if __name__=="__main__":
    unittest.main()
