"""G1 proof branch: immutable original Nightfall content and publish gates.

This test can run entirely offline on the standard safe runner.
It does NOT approve any candidate Blender scene or character model.
"""
import hashlib
import json
import unittest
from pathlib import Path

from studio.restore import ROOT,validate_stories

MANIFEST=ROOT/"docs/g1_protected_git_blobs.json"

def git_blob_sha1(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode("ascii")+b"\0"+raw).hexdigest()

class G1ProtectedContentTests(unittest.TestCase):
    def test_source_artifacts_unchanged(self):
        data=json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(data["baseline_commit"],"ef613a5ce78b8d54b9f33fba381060249b7593b9")
        self.assertGreaterEqual(len(data["files"]),40)
        self.assertEqual(data["protected_file_count"],len(data["files"]))
        for item in data["files"]:
            path=ROOT/item["path"]
            with self.subTest(path=item["path"]):
                self.assertTrue(path.is_file())
                self.assertEqual(git_blob_sha1(path.read_bytes()),item["git_blob_sha1"])

    def test_original_stories_and_flags_remain_locked(self):
        self.assertEqual(validate_stories(),22)
        flags=json.loads((ROOT/"studio/production_settings.json").read_text())
        self.assertTrue(all(not value for key,value in flags.items() if
            key.endswith("_verified") or key in ("production_enabled","publishing_implemented","automatic_new_series","cinematic_video_approved")))
        config=json.loads((ROOT/"config.json").read_text())
        self.assertFalse(config["public_publish_enabled"])

    def test_no_gpu_or_asset_is_falsely_approved(self):
        ledger=(ROOT/"docs/licence_ledger.md").read_text()
        audit=(ROOT/"docs/G1_CPU_AUDIT_BLOCKED_2026-11-06.md").read_text()
        self.assertIn("BLOCKED",audit)
        self.assertIn("NOT APPROVED",ledger)
        self.assertIn("no 15-second proof",audit)
