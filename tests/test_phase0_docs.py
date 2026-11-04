"""Phase 0 documentation acceptance and safeguards.

Intentionally conservative; later phases may change gates only after owner
approval and successful production-quality evidence.
"""
import json
import re
import unittest
from pathlib import Path
from studio.restore import ROOT, validate_stories

DOCS=ROOT / "docs"

class Phase0Acceptance(unittest.TestCase):
    def test_every_studio_file_has_keep_replace_or_retire_decision(self):
        audit=(DOCS/"PHASE_0_AUDIT.md").read_text(encoding="utf-8")
        for path in sorted((ROOT/"studio").rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                rel=path.relative_to(ROOT).as_posix()
                with self.subTest(path=rel):
                    self.assertIn("`"+rel+"`",audit)

    def test_every_public_policy_or_review_document_exists(self):
        for p in ("index.md","privacy.md","terms.md","support.md",
                  "PLATFORM_AUDITS.md","MODEL_LICENSE_AUDIT.md","PHASE_0_AUDIT.md"):
            with self.subTest(document=p):
                path=DOCS/p
                self.assertTrue(path.is_file())
                self.assertGreater(path.stat().st_size,200)

    def test_no_unverified_public_publishing_was_enabled(self):
        production=json.loads((ROOT/"studio/production_settings.json").read_text(encoding="utf-8"))
        fields=("production_enabled","renderer_verified","cinematic_video_approved",
                "voice_lipsync_verified","youtube_verified","facebook_verified",
                "instagram_verified","tiktok_verified","publishing_implemented",
                "automatic_new_series")
        for key in fields:
            self.assertIs(production[key],False,key)
        config=json.loads((ROOT/"config.json").read_text(encoding="utf-8"))
        self.assertIs(config["public_publish_enabled"],False)
        self.assertIs(config["automatic_new_series"],False)

    def test_privacy_and_terms_are_explicit_drafts_without_fake_contact(self):
        privacy=(DOCS/"privacy.md").read_text(encoding="utf-8")
        terms=(DOCS/"terms.md").read_text(encoding="utf-8")
        support=(DOCS/"support.md").read_text(encoding="utf-8")
        self.assertIn("Draft",privacy)
        self.assertIn("Draft",terms)
        self.assertIn("OWNER ACTION REQUIRED",privacy)
        self.assertIn("not",support.lower())
        self.assertNotIn("example@nightfalldiaries.com",privacy)

    def test_platform_policy_reflects_2026_youtube_change(self):
        content=(DOCS/"PLATFORM_AUDITS.md").read_text(encoding="utf-8")
        self.assertIn("November 2, 2026",content)
        self.assertIn("unverified API projects",content)
        self.assertIn("NOT submitted",content)
        self.assertIn("video.publish",content)

    def test_canon_and_locked_voices_remain_restorable(self):
        self.assertEqual(validate_stories(),22)
        for series in ("S01_the_last_little_fox","S02_the_boy_who_forgot_tomorrow"):
            registry=json.loads((ROOT/"seasons"/series/"characters/character_registry.json").read_text())
            self.assertEqual(len(registry["characters"]),5)
            self.assertTrue((ROOT/"seasons"/series/"characters/cloud_reference_locks.json").is_file())
        self.assertTrue((ROOT/"studio/voice_profile_locks.json").is_file())

    def test_docs_do_not_contain_plaintext_access_credentials(self):
        patterns=[r"ghp_[A-Za-z0-9]{20,}",r"hf_[A-Za-z0-9]{20,}",
                  r"(?i)bearer\\s+[A-Za-z0-9._-]{40,}"]
        for path in DOCS.glob("*.md"):
            content=path.read_text(encoding="utf-8")
            for p in patterns:
                with self.subTest(path=path.name,pattern=p):
                    self.assertIsNone(re.search(p,content))
