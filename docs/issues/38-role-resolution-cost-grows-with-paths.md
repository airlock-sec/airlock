---
slug: role-resolution-cost-grows-with-paths
title: Every tracked path is matched against every role glob by recursion, and nothing measures what that costs on a large repository
labels: enhancement, complexity: medium, area: engine
roadmap: 2.4, 7.7
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** The matcher is 60 lines of shipped, fully tested code (`src/airlock/roles.py:142-177`) and 7.7 has not yet produced a number to argue from, so the useful contribution here is the measurement plus a decision, not a speculative optimisation.

## Problem

`resolve_roles` runs `sorted(role_globs.items())` per file and calls `match_glob` for every glob of every role (`src/airlock/roles.py:199-215`, `_any_glob` at 218). `_match_segments` recurses per path segment, and `_segment_pattern` builds a regex source string per segment, per pattern, per path; `re.compile` memoizes the result, so the repeated work is the string building and the cache lookup rather than compilation.

The role set is nine today, so the cost is small and this is not a bug. It is a scaling question the roadmap already has open: 7.4 adds ten candidate config globs and 7.5 adds composite actions, devcontainers, `Makefile` and `justfile`. Multiplying the glob count by several and the path count by a monorepo's ten thousand tracked files is how a scanner that measured fine in Phase 2 ends up slower than the script it replaced, and 3.11 has already recorded one measured overshoot (63 ms against a 50 ms target for `cfg-network`).

There is also a correctness detail hiding in the same function: `sorted(role_globs)` means role order comes from the alphabetical role name rather than from `rules/roles.toml`, so a `roles` tuple is alphabetical by role, not declaration order. `resolve_roles`'s docstring promises "a stable order", which is true, and the docs describing resolution order as magic, then globs, then fallback describe a precedence that the sort silently reorders. Worth confirming and stating in the same change.

## What to build

1. **Measure first.** Build the synthetic large repository 7.7 needs (a script that generates tracked paths across the role-shaped directories, with content that does not trigger findings), and record roles-resolution time against path count and glob count. The harness belongs in `scripts/` or a test marked as slow, not in the default suite.
2. **Then decide.** Candidates, in the order a measurement would justify them: precompile the glob table once per scan instead of per path, index globs by their last literal segment so `**/package.json` is a filename lookup, or accept the cost and record it as a design limit. Do not implement all three.
3. **Settle the ordering question** in whichever way is correct, and make the docstring, `ARCHITECTURE.md` 6.2 and any test agree on whether role order is declaration order or alphabetical.
4. **Add the regression bound.** Once a number exists, assert it: a test that resolution over the synthetic tree stays inside a stated budget, with the budget recorded as a measurement rather than a guess, and a note in the test about which runner produced it (hosted CI decides, per the project's own rule about timing gates).

**Out of scope:** Reaching a target for whole-scan runtime on a real large repository, which is 7.7's task and this issue's harness is a step toward it rather than a substitute, and any change to which roles exist.

## Acceptance criteria

- [ ] A committed harness generates a synthetic tracked tree and reports roles-resolution time against path and glob counts.
- [ ] The resolution cost is either inside a stated budget with a test, or the accepted limit is recorded in `ARCHITECTURE.md` 7.
- [ ] Role resolution order matches what `ARCHITECTURE.md` 6.2 documents, with a test naming the order.
- [ ] No existing role-resolution fixture expectation changes.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- [`src/airlock/roles.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/roles.py) (`_segment_pattern`, `_match_segments`, `resolve_roles`)
- [`rules/roles.toml`](https://github.com/airlock-sec/airlock/blob/main/rules/roles.toml) (the glob set the cost scales with)
- [`tests/unit/test_roles.py`](https://github.com/airlock-sec/airlock/blob/main/tests/unit/test_roles.py)

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
