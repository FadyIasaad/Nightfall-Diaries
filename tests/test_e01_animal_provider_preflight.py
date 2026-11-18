"""Read-only first-episode model audit and retired-schedule regression gates."""
import pathlib
import unittest
from pilot import e01_animal_provider_preflight as p

ROOT = pathlib.Path(__file__).resolve().parents[1]


class ModelFreeBudgetTests(unittest.TestCase):
    def test_joyvasa_has_strict_animal_mode_and_no_readiness_claim(self):
        joy = next(x for x in p.PROVIDERS if "joyvasa" in x["space"])
        self.assertTrue(joy["verified_animal_capable_upstream"])
        self.assertEqual(p.classify(joy, {"stage":"PAUSED","hardware":"zero-a10g"}),"PAUSED_OR_UNAVAILABLE")
        self.assertEqual(p.classify(joy, {"stage":"RUNNING","hardware":"zero-a10g"}),
                         "CANDIDATE_ONLY_MODEL_AND_QUALITY_UNVERIFIED")
        self.assertEqual(p.classify(joy, {"stage":"RUNNING","hardware":"a10g-small"}),
                         "NO_CONFIRMED_FREE_ZEROGPU_HARDWARE")

    def test_no_billable_or_overquota_longcat_request(self):
        for option in p.PROVIDERS:
            if "LongCat" in option["space"]:
                self.assertGreater(option["reservation_seconds"], p.ANONYMOUS_ZEROGPU_SECONDS)
                self.assertEqual(p.classify(option, {"stage":"RUNNING","hardware":"zero-a10g"}),
                                 "FREE_ANONYMOUS_QUOTA_TOO_SMALL")
        self.assertEqual(p.classify(p.PROVIDERS[0], {}),"UNKNOWN_NO_AUTOMATED_GENERATION")
        text = (ROOT/"pilot/e01_animal_provider_preflight.py").read_text()
        self.assertNotIn("client.predict(",text)
        self.assertNotIn("spaces.GPU(",text)
        self.assertIn("REFUSE_PROVIDER_TOKEN_IN_READ_ONLY_BUDGET_CHECK",text)

    def test_only_quality_gate_stays_on_daily_schedule(self):
        cpu=(ROOT/".github/workflows/nightfall_cpu_animated_e01.yml").read_text()
        agnes=(ROOT/".github/workflows/nightfall_agnes_e01_production.yml").read_text()
        retired=(ROOT/".github/workflows/nightfall_story_one_click.yml").read_text()
        daily=(ROOT/".github/workflows/nightfall_e01_daily_real_speaking.yml").read_text()
        for obsolete in (cpu, agnes, retired):
            self.assertNotIn("  schedule:",obsolete)
            self.assertIn("workflow_dispatch:", obsolete)
        self.assertIn("  schedule:",daily)
        self.assertIn("timezone: 'Africa/Cairo'",daily)
        self.assertIn("MODE:",daily)


if __name__=="__main__":
    unittest.main()
