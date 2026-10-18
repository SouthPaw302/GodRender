# GodRender Studio

The GodRender browser workstation uses a six-stage direction-to-release production workflow backed by Python, FFmpeg, reusable FX and explicit technical/creative acceptance.

## Start

At the **GodRender repository root**:

```bash
python godrender_boot.py
python studio/stack.py
```

Open `http://127.0.0.1:8080`. The full app lives in `studio/`; `studio/server.py` is a smaller fallback. Windows: `studio/start_windows.bat`. Termux: `bash studio/start_termux.sh`.

Studio listens on loopback unless configured otherwise. For LAN binding a strong access token is mandatory. Runtime media, proxies and logs are local by default; optional storage mirroring uses `rclone`.

## Compatibility settings

Legacy configuration environment keys remain operational so deployed workstations do not break: `AIVE_HOST`, `AIVE_PORT`, `AIVE_STUDIO_TOKEN`, `AIVE_RUNTIME`, `AIVE_WORKERS`, `AIVE_MAX_UPLOAD`, `AIVE_RCLONE_REMOTE`, and `AIVE_CORE_AUTOBOOT`. These are compatibility **identifiers**, not the product name. Renaming their wire contracts requires a separately tested migration.

## Interfaces

- `GET /api/health`, `/api/system`, `/api/core`, `/api/tools`
- `POST /api/core/bootstrap`, `/api/tools/call`
- `python studio/godrender_mcp.py` — first-party MCP entry; older script filename remains a forwarding-compatible adapter.
- Tool families: project/media lifecycle, production stages, FX gate, shot proof, assembly, final QC, archive and optional harness.

## Rules and acceptance

GodRender is the single active project. Keep old song production methods discoverable through the [External Brain](https://docs.google.com/spreadsheets/d/1Xi2wSER-vEIjy52FTKA5RvMXNnGrTxoYiEoPhyXw77c/edit); never treat their footage as automatically approved.

Current core bootstrap still uses a pinned legacy production-OS checkout to validate source contracts and emit historic session schemas. Studio may correctly show 'core not loaded' when that compatibility checkout cannot be validated. Read `docs/COMPATIBILITY_DEBT.md` before changing its implementation.

## Verification

```bash
python tools/verify_consolidation.py
PYTHONPATH=studio python -m unittest discover -s tests -p 'test_*.py' -v
PYTHONPATH=studio python studio/selftest.py
```

The GitHub smoke test verifies boot, server endpoints, and sources; this does **not** substitute for a real film with accepted media, audio, FX and Director visual QC.
