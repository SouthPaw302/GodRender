# GodRender Harness / MCP adapter

This optional adapter connects a provider-neutral agent loop to the same GodRender Studio Tool API. It is **not** a separate rendering repository or separate production authority.

Preferred entry: `python studio/godrender_mcp.py` from a GodRender checkout. The old adapter filename remains for clients already configured with it. MCP tool names retain their stable dotted/`__` forms, but the MCP server identity is now `godrender`.

Use `studio/deepseek_harness/cordis.patch.yml.example` as an example, substituting the real path to **GodRender**.

Safety: an agent must run `python godrender_boot.py`, honor per-production guard/FX gates and real evidence, and never claim success from an unexecuted renderer. Harness configuration may request tool operations but does not authorize publishing or bypass human Director approval.

The compatibility engine still needs a real boot attestation; see `docs/COMPATIBILITY_DEBT.md`. Runtime credentials belong in environment settings, not tracked files.
