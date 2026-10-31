---
slug: no-rule-for-workflow-script-injection
title: No shipped rule flags untrusted event data interpolated straight into a `run:` block
labels: enhancement, complexity: high, area: rules
roadmap: 3.6, 3.7
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** `ci_surface.py` is built exactly for two-condition rules, and it already ships one pairing over `${{ ... }}` interpolations (`_SECRETS_INTERP` plus a display verb), so the machinery, the role and the fixture module all exist.

## Problem

A workflow line that puts GitHub's own event object into a shell is code execution with the runner's token:

```yaml
- run: echo "${{{ github.event.issue.body }}}"
```

Nothing reports it. `rules/builtin/ci_surface.toml` ships six rules and the three that read workflow grammar look elsewhere: `pat-privileged-trigger` wants a `workflow_run`, `pull_request_target` or the dynamic `pull_request` event name (line 35), `pat-secret-dump` wants a `${{ secrets.* }}` interpolation paired with a display verb (line 46), and `pat-ptr-head-checkout` wants a privileged trigger paired with a checkout of a head ref (line 56). An event payload from a stranger, interpolated into a shell, matches none of the three.

This is the highest-volume class in GitHub's own security advisories for Actions, and the fix that maintainers are told to apply (`env:` indirection plus a shell quoting discipline) is exactly the negative fixture the detector would need. `ci_surface.py` already names the safe form in its docstring for the secret case: passing a value through `env:` or `with:` "is how a workflow uses one, and it is the negative fixture rather than a finding".

The rule set's own header comment for the family says what is missing: the ported HIGH list covers "workflow secret dump" and not workflow injection, and `ARCHITECTURE.md` 9.6 records the family's residuals. This issue is one of them.

## What to build

1. **Write the pairing in `ci_surface.py`, not as one regex.** The module's whole argument is that a single pattern for a two-condition rule is either a false-positive machine or a quadratic one (its docstring, and the ReDoS reason for reading trigger and fetch patterns through `rules.line_matches`). Use an untrusted-context pattern (the `${{ github.event.` and `${{ github.` payload families, `inputs.` for a reusable workflow) plus a "this line is a shell" condition, and run the second test only on lines the first already hit.
2. **Decide what a shell is in YAML.** A `run:` block, a `$(...)`, a backtick and a here-string are the candidates; `--` argument passing is not. Say which forms the rule claims, and record the residual it leaves (a value interpolated into a step's `args:` list reaches a process without a shell).
3. **Get severity right and defend it.** A paired interpolation is HIGH if the trigger is untrusted by origin, which is the honest overlap with `pat-privileged-trigger`; a `push` event interpolating `github.event.head_commit .message` is still attacker-influenceable but weaker. Write the reasoning into the rationale, since a reviewer will otherwise read the severity as copied.
4. **No masking, ever.** AGENTS.md 4 and ADR-013 forbid comment and string masking, so a workflow comment spelling out the shape is a finding by design, and the existing `${{{{ ... }}}}` escape sequence in a `run:` block is a legitimate non-match that needs its own negative fixture.
5. **Fixtures and cost.** Positive per interpolation family, negative for the `env:` form and the doubled-brace escape, and a near-miss line at `line_cap` added to `tests/unit/test_redos.py` for the new pattern, because this is the pattern most likely to be expensive.

## Acceptance criteria

- [ ] A `run:` step that interpolates `github.event` payload data into a shell command is a named finding, and the finding names the line it paired with.
- [ ] The `env:` indirection form, the `${{{{ ... }}}}` escape and a `with:` input pass produce no finding, each with its own fixture.
- [ ] The new pattern's measured cost on the ReDoS harness's near-miss bait is recorded, and no existing timing budget is widened.
- [ ] The rule is data with a `builtin:ci_surface` pointer, a rationale that states the severity argument, and a row in the generated rule reference.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.
- [ ] `ARCHITECTURE.md` 9.6 stops listing workflow script injection as an uncovered residual, or explains the part of it that still is.

## Tech stack

- [`src/airlock/detectors/ci_surface.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/detectors/ci_surface.py) (`_secret_dumps` is the pairing shape to follow)
- [`rules/builtin/ci_surface.toml`](https://github.com/airlock-sec/airlock/blob/main/rules/builtin/ci_surface.toml)
- [`tests/unit/test_redos.py`](https://github.com/airlock-sec/airlock/blob/main/tests/unit/test_redos.py) and [`tests/fixtures/ci_surface.py`](https://github.com/airlock-sec/airlock/blob/main/tests/fixtures/ci_surface.py)
- The GitHub Actions `context` object reference, for which fields an untrusted sender controls

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
