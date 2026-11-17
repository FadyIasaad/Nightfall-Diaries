"""No-network safety tests for specifically authorized V4 remaster release."""
import os
import unittest
from unittest.mock import patch

from pilot import e01_v4_remaster_upload_once as v4
from pilot import e01_painterly_upload_once as old


class RemasteredE01ReleaseTests(unittest.TestCase):
    def test_unique_receipt_and_exact_source(self):
        self.assertEqual(len(v4.SOURCE_SHA256), 64)
        self.assertNotEqual(v4.SOURCE_SHA256, "6a41bf8978e84c3df1c76b355b8b92e32796836ade92dc24e484d86b2472c1da")
        self.assertNotEqual(v4.RECEIPT, "published/S01_the_last_little_fox_E01_painterly_v2.json")
        self.assertIn("V4_remastered",v4.RECEIPT)
        self.assertIn("V4_Remastered",v4.FILM.name)

    def test_no_attempt_without_explicit_release_authorization(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError,"AUTHORIZATION_MISSING"):
                v4.execute()

    def test_ref_and_rerun_gates_precede_any_network(self):
        with patch.dict(os.environ,{
            "OWNER_AUTHORIZED_E01_V4_REMASTER_PUBLIC":"YES",
            "GITHUB_REF":"refs/heads/review",
            "GITHUB_RUN_ATTEMPT":"1",
        },clear=True):
            with self.assertRaisesRegex(RuntimeError,"NOT_MAIN_BRANCH"):
                v4.execute()
        with patch.dict(os.environ,{
            "OWNER_AUTHORIZED_E01_V4_REMASTER_PUBLIC":"YES",
            "GITHUB_REF":"refs/heads/main",
            "GITHUB_RUN_ATTEMPT":"2",
        },clear=True):
            with self.assertRaisesRegex(RuntimeError,"NO_RETRY"):
                v4.execute()

    def test_disclosure_and_no_old_episode_receipt_overwrite(self):
        prior = {k:getattr(old,k) for k in (
            "SRC_SHA","RECEIPT_PATH","FILM","TAG","RELEASE_URL",
            "GH_API","TITLE","DESCRIPTION"
        )}
        try:
            v4.configure()
            self.assertEqual(old.SRC_SHA,v4.SOURCE_SHA256)
            self.assertEqual(old.RECEIPT_PATH,v4.RECEIPT)
            self.assertIn("not Episode 2",old.DESCRIPTION)
            self.assertIn("not full 3D animation",old.DESCRIPTION)
            self.assertIn("Remastered",old.TITLE)
            self.assertEqual(old.FILM,v4.FILM)
        finally:
            for key,value in prior.items():
                setattr(old,key,value)


if __name__ == "__main__":
    unittest.main()
