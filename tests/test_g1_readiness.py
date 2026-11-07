"""Safety regression for owner-approved $0-budgets G1 preflight."""
import unittest
from pathlib import Path
from studio.restore import ROOT
from studio.g1_readiness import assess

class G1ReadinessTests(unittest.TestCase):
    def test_no_real_models_no_cinematic_render(self):
        report=assess()
        self.assertEqual(report["status"],"BLOCKED")
        self.assertFalse(report["ready_to_render"])
        self.assertFalse(report["rendered_video"])
        self.assertFalse(report["publicly_published"])
        self.assertFalse(report["gpu_used"])
        self.assertEqual({x["character_id"] for x in report["checked_assets"]},
                         {"s01_ember","s01_moss"})
        self.assertTrue(report["issues"])

    def test_original_workflow_requires_explicit_dispatch(self):
        workflow=(ROOT/".github/workflows/nightfall.yml").read_text(encoding="utf-8")
        self.assertIn("mode:",workflow)
        self.assertIn("g1_proof",workflow)
        self.assertIn("github.event_name == 'workflow_dispatch' && inputs.mode == 'g1_proof'",workflow)
        self.assertEqual(workflow.count("runs-on: ubuntu-latest"),2)
        self.assertIn("github.head_ref == 'proof/g1-procedural-cpu-diagnostic-2026-11-07'",workflow)
        self.assertNotIn("runs-on: ubuntu-latest-8-cores",workflow)
        self.assertEqual(workflow.count("name: Nightfall Diaries - One Free Online Workflow"),1)

    def test_no_license_assumed_for_unknown_models(self):
        report=assess()
        self.assertTrue(any("s01_ember" in issue for issue in report["issues"]))
        self.assertTrue(any("s01_moss" in issue for issue in report["issues"]))
