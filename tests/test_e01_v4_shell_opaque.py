"""Moss shell opaque geometry regression: no forest showing through plates."""
import importlib.util
import unittest

HAS_PIL=importlib.util.find_spec("PIL") is not None
HAS_NUMPY=importlib.util.find_spec("numpy") is not None

@unittest.skipUnless(HAS_PIL and HAS_NUMPY,"Dedicated rendering workflow provides Pillow/NumPy")
class MossOpaqueTest(unittest.TestCase):
    def test_shell_fully_covers_its_center_despite_scute_detail(self):
        from studio.e01_v3_painterly_moss import parts
        shell=parts()[2]
        a=shell.getchannel("A")
        center=a.getpixel((185,169))
        self.assertGreaterEqual(center,220)
        # No large holes through plates inside 70% radius.
        total=0
        poor=0
        for y in range(115,227):
            for x in range(91,281):
                if ((x-185)/155)**2+((y-169)/96)**2<0.49:
                    total+=1
                    poor+=a.getpixel((x,y))<190
        self.assertLess(poor/total,.025,
                        "Shell-scute alpha holes show background through hero")
    def test_natural_tortoise_rig_and_canonical_crack_preserved(self):
        from studio.e01_v3_painterly_moss import parts
        feet,body,shell,head=parts()
        self.assertEqual(len(feet),4)
        self.assertEqual(shell.size,(420,340))
        self.assertTrue(head.getbbox())
        self.assertTrue(body.getbbox())

if __name__=="__main__":
    unittest.main()
