#!/usr/bin/env python3
"""Local, no-hosting American Empire sandbox agent entry point.

Check and serve require Python only; scene requires local Node + Playwright
(or an exported verified P7 receipt). Rendering is optional and requires
Godot 4 plus FFmpeg. Never exposes a remote control API or mutates canon.
"""
from __future__ import annotations

import argparse
import functools
import http.server
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
TOOLS = ROOT / "tools"
WEB = ROOT / "web"
DIST = WEB / "dist"
GODOT = ROOT / "godot"
OUTPUT = ROOT / "sandbox-output"


def run(*args: str, cwd: Path | None = None, env: dict | None = None,
        timeout: int = 180) -> None:
    subprocess.run(list(args), cwd=str(cwd or REPO), env=env, timeout=timeout, check=True)


def build(*, verify: bool = True) -> dict:
    if not (REPO / "AGENTS.md").is_file() or not (ROOT / "CANON_LOCK.json").is_file():
        raise RuntimeError("Not an intact GodRender/AE checkout; do not substitute a demo")
    if verify:
        run(sys.executable, str(TOOLS / "verify_canon.py"))
    run(sys.executable, str(TOOLS / "build_web.py"), "--repro", timeout=240)
    for rel in ("index.html", "standalone.html", "data/world.json",
                "data/brain.json", "data/model.json", "data/inhabitants.json"):
        if not (DIST / rel).is_file():
            raise RuntimeError("Required browser build missing: " + rel)
    world = json.loads((DIST / "data/world.json").read_text(encoding="utf-8"))
    brain = json.loads((DIST / "data/brain.json").read_text(encoding="utf-8"))
    if world.get("schema") != "american-empire.godot-explorer-bundle.v1":
        raise RuntimeError("World data provenance failed")
    if brain.get("world_bundle_sha256") != world.get("bundle_sha256"):
        raise RuntimeError("Browser brain and world are not source-aligned")
    return {"status": "AE_SANDBOX_BUILD_PASS",
            "world_sha256": world["bundle_sha256"],
            "site": str(DIST / "index.html"),
            "offline": str(DIST / "standalone.html"),
            "network_required": False}


def handler(directory: Path = DIST):
    return functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(directory))


def local_server(port: int = 0) -> http.server.ThreadingHTTPServer:
    # Never make the simulation or any agent tool available on the LAN.
    return http.server.ThreadingHTTPServer(("127.0.0.1", port), handler())


def probe(server: http.server.ThreadingHTTPServer) -> None:
    with urllib.request.urlopen(
        f"http://127.0.0.1:{server.server_address[1]}/data/world.json", timeout=8
    ) as response:
        data = json.loads(response.read())
    if data.get("schema") != "american-empire.godot-explorer-bundle.v1":
        raise RuntimeError("Local browser server returned the wrong source bundle")


def start_for_agent(server: http.server.ThreadingHTTPServer):
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        probe(server)
    except Exception:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
        raise
    return thread


def scene(opts: argparse.Namespace) -> dict:
    build()
    destination = (opts.output_dir or OUTPUT).expanduser().resolve()
    archive = (ROOT / "archive").resolve()
    source = (WEB / "src").resolve()
    if (destination == archive or archive in destination.parents or
            destination == source or source in destination.parents or
            destination == REPO or destination == ROOT or
            destination == (ROOT / "tools") or
            destination == (GODOT / "data")):
        raise ValueError("Refusing to put derived output in a protected/source directory")
    destination.mkdir(parents=True, exist_ok=True)
    source_receipt = opts.receipt
    if source_receipt is None:
        node = shutil.which("node")
        if not node:
            raise RuntimeError("Browser receipt capture requires Node + Playwright; or supply --receipt")
        browser_script = WEB / "tests" / "replay_scene_request.mjs"
        env = os.environ.copy()
        env["AE_SCENE_OUTPUT"] = str(destination)
        if opts.request:
            raw = opts.request.read_text(encoding="utf-8")
            if len(raw.encode("utf-8")) > 21000:
                raise ValueError("Scene request exceeds the existing P9 gate")
            env["AE_SCENE_REQUEST_JSON"] = raw
        with local_server(0) as server:
            thread = start_for_agent(server)
            env["AE_BASE_URL"] = f"http://127.0.0.1:{server.server_address[1]}"
            try:
                run(node, str(browser_script), cwd=WEB, env=env, timeout=180)
            finally:
                server.shutdown()
                thread.join(timeout=10)
        source_receipt = destination / "ae-p7-receipt.json"
        requested = json.loads((destination / "scene_request.json").read_text(encoding="utf-8"))
        actor, year, place = requested["actor"], requested["year"], requested["observer_place"]
    else:
        if opts.request:
            raise ValueError("--request requires replay from the actual browser; do not mix it with --receipt")
        actor, year, place = opts.actor, opts.year, opts.place
    contract = destination / "scene_contract.json"
    geometry = destination / "procedural_geometry.json"
    run(sys.executable, str(TOOLS / "export_godot_scene.py"),
        "--receipt", str(source_receipt),
        "--output", str(contract),
        "--actor", actor, "--year", str(year), "--place", place)
    run(sys.executable, str(TOOLS / "build_procedural_geometry.py"),
        "--contract", str(contract), "--output", str(geometry),
        "--town-variation", str(opts.town_variation),
        "--road-variation", str(opts.road_variation))
    run(sys.executable, str(TOOLS / "build_procedural_geometry.py"),
        "--contract", str(contract), "--verify", str(geometry))
    record = json.loads(geometry.read_text(encoding="utf-8"))
    summary = {
        "status": "AE_SANDBOX_SCENE_DATA_PASS",
        "classification": "source-bound_synthetic_technical_geometry_not_film",
        "actor": actor, "year": year, "place": place,
        "geometry_sha256": record["geometry_sha256"],
        "source_p7_snapshot_sha256": record["source_p7_snapshot_sha256"],
        "settlements": len(record["settlements"]),
        "roads": len(record["roads"]),
        "output_dir": str(destination),
        "godot_rendered": False,
    }
    if opts.render:
        render_scene(destination, godot_bin=opts.godot_bin)
        summary["godot_rendered"] = True
        summary["movie"] = str(destination / "godot-proof.mp4")
        summary["status"] = "AE_SANDBOX_GODOT_TECHNICAL_PASS"
    (destination / "agent-receipt.json").write_text(
        json.dumps(summary, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return summary


def render_scene(output: Path, *, godot_bin: str | None) -> None:
    godot = godot_bin or os.environ.get("GODOT_BIN") or shutil.which("godot") or shutil.which("godot4")
    ffmpeg = shutil.which("ffmpeg")
    if not godot or not ffmpeg:
        raise RuntimeError("Render requested but Godot 4 or FFmpeg is not installed")
    # Isolated project copy: no writes to the tracked Godot scenes/data.
    with tempfile.TemporaryDirectory(prefix="ae-sandbox-godot-") as temp:
        project = Path(temp) / "project"
        shutil.copytree(GODOT, project,
                        ignore=shutil.ignore_patterns(".godot", "*.tmp", "scene_contract.json",
                                                      "procedural_geometry.json"))
        data_dir = project / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        for name in ("scene_contract.json", "procedural_geometry.json"):
            shutil.copy2(output / name, data_dir / name)
        import_log = subprocess.run(
            [godot, "--headless", "--path", str(project), "--editor", "--import", "--quit"],
            text=True, capture_output=True, timeout=120, check=True)
        (output / "import.log").write_text(import_log.stdout + import_log.stderr, encoding="utf-8")
        if any(x in (import_log.stdout + import_log.stderr) for x in ("SCRIPT ERROR", "Parse Error")):
            raise RuntimeError("Godot procedural scene script import failed")
        cmd = [godot, "--path", str(project),
               "--scene", "res://scenes/procedural_scene.tscn",
               "--rendering-method", "gl_compatibility",
               "--write-movie", str(output / "frame.png"),
               "--fixed-fps", "24", "--quit-after", "48", "--", "--scene-proof"]
        if not os.environ.get("DISPLAY") and shutil.which("xvfb-run"):
            cmd = ["xvfb-run", "-a"] + cmd
        elif not os.environ.get("DISPLAY"):
            cmd.insert(1, "--headless")
        rendered = subprocess.run(cmd, text=True, capture_output=True, timeout=240, check=True)
        log = rendered.stdout + rendered.stderr
        (output / "godot.log").write_text(log, encoding="utf-8")
        if ("AE_PROCEDURAL_SCENE_READY" not in log or
                any(x in log for x in ("SCRIPT ERROR", "Parse Error", "AE_SCENE_FAIL",
                                       "AE_PROCEDURAL_FAIL"))):
            raise RuntimeError("Godot did not execute the validated synthetic 3D scene")
        run(ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
            "-framerate", "24", "-i", str(output / "frame%08d.png"),
            "-c:v", "libx264", "-preset", "fast", "-crf", "24",
            "-pix_fmt", "yuv420p", str(output / "godot-proof.mp4"), timeout=120)
        # Existing source/three-frame/movie integrity proof; not a film acceptance.
        run(sys.executable, str(TOOLS / "verify_scene_proof.py"),
            "--root", str(output), timeout=90)


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    actions = cli.add_subparsers(dest="command", required=True)
    actions.add_parser("check", help="Verify locked canon and build the complete browser site locally")
    srv = actions.add_parser("serve", help="Serve the real World Explorer on sandbox localhost")
    srv.add_argument("--port", type=int, default=8765)
    sc = actions.add_parser("scene", help="Replay a P7 browser world and derive source-bound procedural 3D")
    sc.add_argument("--receipt", type=Path, help="Previously exported, hash-verified P7 receipt (no Playwright)")
    sc.add_argument("--request", type=Path, help="Observer World Scene Forge JSON; requires Playwright")
    sc.add_argument("--actor", default="claire")
    sc.add_argument("--year", type=int, default=2027)
    sc.add_argument("--place", default="paris")
    sc.add_argument("--town-variation", type=int, default=0)
    sc.add_argument("--road-variation", type=int, default=0)
    sc.add_argument("--output-dir", type=Path)
    sc.add_argument("--render", action="store_true", help="Optional real Godot 4 technical movie proof")
    sc.add_argument("--godot-bin", help="Specific Godot 4 executable for --render")
    opts = cli.parse_args(argv)
    try:
        if opts.command == "check":
            print(json.dumps(build(), sort_keys=True))
        elif opts.command == "serve":
            info = build()
            with local_server(opts.port) as server:
                print(f"AE_SANDBOX_SITE_READY http://127.0.0.1:{server.server_address[1]} "
                      f"source={info['world_sha256']}", flush=True)
                server.serve_forever()
        elif opts.command == "scene":
            print(json.dumps(scene(opts), sort_keys=True))
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError,
            KeyError, json.JSONDecodeError) as exc:
        print(f"AE_SANDBOX_FAIL: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
