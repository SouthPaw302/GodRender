# American Empire — Native Boot Handoff

Branch is `world/american-empire`, not a new `song/` branch. Run the native `bootstrap.py boot` on that same checkout with exact current protected `main` as OS authority.

Known blocker: `main`'s `general/reusable/tools/branch_policy.py` refuses `world/american-empire` at production-guard validation. Do not fake `song/american-empire`, bypass guards, patch materialized `.godrender/os`, or claim PASS. The production source/canonical history is preserved. A narrowly scoped reviewed change to the shared policy is needed before full boot is feasible without renaming the branch.

Next after boot PASS: source-byte/hash ingestion under project guard; link persistent world-state handoff to Godot; run short scene proof; review before any master or public interface change.
