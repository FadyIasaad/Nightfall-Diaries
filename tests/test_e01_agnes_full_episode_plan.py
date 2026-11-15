"""Offline tests for preserving all six genuine MP4s in an independent Agnes plan."""
import hashlib
import tempfile
import unittest
from pathlib import Path

from pilot import e01_agnes_full_episode_plan as migration
from pilot import e01_full_run as film
from pilot import e01_free_resume as old

REV = "d235d66f5f17e19b2020623a5cba0ff78caf2321"
DURATIONS = [5.042, 5.042, 3.042, 5.042, 4.042, 2.042]


class TestAgnesFullEpisodeMigration(unittest.TestCase):
    def setUp(self):
        _, self.plan = film.scene_plan()
        self.temp = tempfile.TemporaryDirectory()
        self.dir = Path(self.temp.name)
        self.state = old.create_state(self.plan)
        for (scene, part), seconds in zip(migration.OLD_PREFIX, DURATIONS):
            name = f"scene_{scene:02d}_part_{part:02d}_generated.mp4"
            content = f"authentic-fixture-{scene}-{part}".encode()
            (self.dir / name).write_bytes(content)
            self.state["completed"].append({
                "scene": scene, "part": part, "file": name,
                "seconds": seconds, "sha256": hashlib.sha256(content).hexdigest(),
            })

    def tearDown(self):
        self.temp.cleanup()

    def test_exact_six_preserved_and_fifteen_full_length_new_shots(self):
        result = migration.make_plan(self.plan, self.state, self.dir, REV)
        self.assertEqual(result["existing_clips_preserved"], 6)
        self.assertEqual(result["new_agnes_requests_planned"], 15)
        self.assertEqual(result["expected_unique_motion_shots"], 21)
        self.assertGreaterEqual(result["projected_episode_seconds"], 180)
        self.assertLessEqual(result["projected_episode_seconds"], 360)
        self.assertAlmostEqual(result["existing_real_motion_seconds"], 24.252, places=3)
        self.assertEqual(result["planned_new_real_motion_seconds"], 162)
        self.assertEqual({r["scene"] for r in result["new_ai_shots"]}, set(range(3, 15)))
        self.assertEqual(sorted(r["seconds"] for r in result["new_ai_shots"]),
                         [6, 6, 6] + [12] * 12)
        self.assertEqual({r["model"] for r in result["new_ai_shots"]},
                         {"agnes-video-2.5-flash"})
        self.assertTrue(all(r["mode"] == "reference" and r["size"] == "720P"
                            and r["aspect_ratio"] == "9:16"
                            and "/d235d66f" in r["image_url"] for r in result["new_ai_shots"]))
        self.assertFalse(result["public_publishing_authorized"])
        self.assertFalse(result["true_character_lipsync_verified"])
        self.assertFalse(result["price_and_account_type_authorized"])
        self.assertEqual(result["api_requests_sent"], 0)

    def test_original_mp4_hash_mismatch_fails_without_rebuilding(self):
        (self.dir / self.state["completed"][0]["file"]).write_bytes(b"tampered")
        with self.assertRaisesRegex(RuntimeError, "SHA mismatch"):
            migration.make_plan(self.plan, self.state, self.dir, REV)

    def test_any_new_existing_clip_requires_reconciliation_not_discard(self):
        self.state["completed"].append({
            "scene": 3, "part": 1, "file": "scene_03_part_01_generated.mp4",
            "seconds": 5, "sha256": "0" * 64,
        })
        with self.assertRaisesRegex(RuntimeError, "Original completed shots changed"):
            migration.make_plan(self.plan, self.state, self.dir, REV)

    def test_wrong_original_episode_plan_fails(self):
        self.state["plan_sha256"] = "0" * 64
        with self.assertRaisesRegex(RuntimeError, "fingerprint mismatch"):
            migration.make_plan(self.plan, self.state, self.dir, REV)

    def test_unsafe_filenames_rejected(self):
        self.state["completed"][0]["file"] = "../../something.mp4"
        with self.assertRaisesRegex(RuntimeError, "Unsafe original video file"):
            migration.make_plan(self.plan, self.state, self.dir, REV)

    def test_immutable_image_urls_and_no_traversal(self):
        self.assertTrue(migration.pinned_reference("seasons/a/ref.png", REV).endswith("ref.png"))
        with self.assertRaises(ValueError):
            migration.pinned_reference("../../secrets.txt", REV)
        with self.assertRaises(ValueError):
            migration.pinned_reference("assets/reference.png", "main")


if __name__ == "__main__":
    unittest.main()
