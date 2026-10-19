"""GodRender product identity tests; legacy wire schemas and imported history remain unchanged."""
from __future__ import annotations
import importlib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class GodRenderIdentityTests(unittest.TestCase):
    def test_browser_brand(self):
        html = (ROOT / "studio/static/index.html").read_text(encoding="utf-8")
        script = (ROOT / "studio/static/app.js").read_text(encoding="utf-8")
        self.assertIn("<title>GodRender Studio</title>", html)
        self.assertIn("<strong>GodRender</strong>", html)
        self.assertIn("GodRender Studio access token", script)
        self.assertNotIn("AIVideoEdit Studio", html)

    def test_mcp_identity(self):
        mcp = importlib.import_module("aivideo_mcp")
        self.assertEqual(mcp.SERVER_NAME, "godrender")
        self.assertTrue((ROOT / "studio/godrender_mcp.py").is_file())
        profile = (ROOT / "studio/deepseek_harness/cordis.patch.yml.example").read_text(encoding="utf-8")
        self.assertIn("serverName: godrender", profile)
        self.assertIn("studio/godrender_mcp.py", profile)

    def test_single_active_home_and_history(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertTrue(readme.startswith("# GodRender\n"))
        self.assertIn("only", agents.lower())
        self.assertIn("GodRender", readme)
        self.assertTrue((ROOT / "config/brain_source_index.json").is_file())
        self.assertTrue((ROOT / "docs/COMPATIBILITY_DEBT.md").is_file())

    def test_native_boot_keeps_versioned_wire_compatibility(self):
        src = (ROOT / "studio/core_adapter.py").read_text(encoding="utf-8")
        self.assertIn("AIVideoEdit OS BOOTSTRAP: PASS", src)
        self.assertIn("SouthPaw302/GodRender.git", src)
        self.assertNotIn("SouthPaw302/AIVideoEdit-MainV2-Lab.git", src)
        self.assertTrue((ROOT / "bootstrap.py").is_file())
        self.assertTrue((ROOT / "general/reusable/PRODUCTION_CONTRACT.json").is_file())
        self.assertIn("legacy", (ROOT / "docs/COMPATIBILITY_DEBT.md").read_text(encoding="utf-8").lower())

if __name__ == "__main__":
    unittest.main()
