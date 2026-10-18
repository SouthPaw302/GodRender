#!/usr/bin/env python3
"""GodRender MCP entrypoint. Retains the legacy adapter filename as a compatibility module."""
from aivideo_mcp import main

if __name__ == "__main__":
    raise SystemExit(main())
