"""Validate the diagnostic is not accidentally enabled for schedule or publishing."""
import ast
from pathlib import Path
import unittest
from studio.restore import ROOT
class G1GeometryDiagnosticSafety(unittest.TestCase):
    def test_script_syntax_and_no_secret_or_network_calls(self):
        p=ROOT/"studio/g1_cpu_geometry_diagnostic.py"
        src=p.read_text(encoding="utf-8")
        ast.parse(src,filename=str(p))
        self.assertIn("UNAPPROVED_CPU_3D_GEOMETRY_DIAGNOSTIC",src)
        self.assertNotIn("publish_youtube",src)
        self.assertNotIn("requests.post",src)
        self.assertNotIn("bpy.ops.wm.open_mainfile",src)
        self.assertIn("LEFT ear white tip",src)
        self.assertIn("single",src.lower())
        self.assertIn("Moss locked spiral",src)
    def test_no_g1_public_approval(self):
        import json
        s=json.loads((ROOT/"studio/production_settings.json").read_text())
        self.assertFalse(s["cinematic_video_approved"])
        self.assertFalse(s["publishing_implemented"])
