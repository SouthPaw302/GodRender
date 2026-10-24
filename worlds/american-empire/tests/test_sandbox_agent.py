"""Sandbox launcher contract: loopback-only, real site files, no media APIs."""
from __future__ import annotations
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import sandbox_agent as agent


class SandboxAgentTests(unittest.TestCase):
    def test_cli_and_site_are_not_deployment_services(self):
        self.assertEqual(agent.DIST, ROOT / "web" / "dist")
        self.assertTrue((agent.TOOLS / "build_web.py").is_file())
        self.assertTrue((agent.TOOLS / "build_procedural_geometry.py").is_file())

    def test_loopback_no_wildcard(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            (base / "data").mkdir()
            (base / "data" / "world.json").write_text(json.dumps({
                "schema": "american-empire.godot-explorer-bundle.v1",
            }), encoding="utf-8")
            original_handler = agent.handler
            with patch.object(agent, "handler", lambda: original_handler(base)):
                with agent.local_server(0) as server:
                    self.assertEqual(server.server_address[0], "127.0.0.1")
                    thread = agent.start_for_agent(server)
                    try:
                        agent.probe(server)
                        with urlopen(f"http://127.0.0.1:{server.server_address[1]}/data/world.json") as answer:
                            self.assertEqual(answer.status, 200)
                        with self.assertRaises(HTTPError) as denied:
                            urlopen(f"http://127.0.0.1:{server.server_address[1]}/data/private.json")
                        self.assertEqual(denied.exception.code, 404)
                    finally:
                        server.shutdown()
                        thread.join(timeout=5)

    def test_built_site_uses_verified_source(self):
        self.assertTrue((ROOT / "CANON_LOCK.json").is_file())
        with patch.object(agent, "run") as mocked:
            with patch.object(agent, "DIST", Path("/unlikely-nonexistent-ae-sandbox-dist")):
                with self.assertRaises(RuntimeError):
                    agent.build()
            self.assertTrue(mocked.called)


if __name__ == "__main__":
    unittest.main()
