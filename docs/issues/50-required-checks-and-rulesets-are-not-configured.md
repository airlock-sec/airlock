---
slug: required-checks-and-rulesets-are-not-configured
title: Nothing outside the repository stops a direct push, a force push or a pull request that deletes the scan step
labels: enhancement, complexity: medium, area: ci
roadmap: 1.3, G8
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** CI is green and named, `check_roadmap_touched.sh` exists, and the self-scan step is a known job step, so the branch protections and rulesets can be configured and demonstrated against what already ships.

## Problem

The whole design rests on the scan being unremovable from the merge path: `PRD.md`'s threat model, G8 ("a PR that removes the scan step is blocked"), and 4.5's test that a push editing policy plus a payload is caught. Inside the repository, every piece is ready: the CI job runs the gates, the roadmap gate refuses a change without a record, and CODEOWNERS names the protected paths.

Outside the repository, nothing has been recorded as configured. 1.3 is unticked, G8 is unticked, and 0.13 asks whether the org plan even supports the controls (which the governance issue about the plan is separate from this one). A scanner whose required check is not required is a suggestion, and the first real compromise this project would fail to catch is the one that edits the workflow.

This issue is owner-facing work rather than a first pull request, and it is the kind of change that has to be demonstrated rather than asserted: a refused direct push, a blocked force push, and a pull request that removes the scan step failing to merge.

## What to build

1. **Configure `main` protection**: no force push, no deletion, require a pull request, require owner review on the protected paths CODEOWNERS names, and require the CI job's checks to pass before merge.
2. **Demonstrate each refusal** and record what was tried with the output, in the change record. `AGENTS.md`'s discipline is that a claim a reviewer cannot check is a claim that was not proven, and 1.3's `Done when` says exactly this.
3. **Deal with the pinning question honestly.** 0.13 asks whether a required check can be pinned to a trusted source. Whatever the answer, record it in the same place, because an unpinned required check is a workflow edit away, and `ARCHITECTURE.md` 16 should say so rather than leaving it to the risk register.
4. **Say what is not yet true** in `README.md` and the site's trust page until the checks exist. The project's own convention is to state the weaker guarantee rather than the stronger one it hopes for (6.5).

**Out of scope:** Org-level required workflows (a plan question, not a repository one), the runner hardening in 1.2, and `action.yml` (the open issue #34).

## Acceptance criteria

- [ ] A direct push to `main` is refused, with the attempt and the message recorded.
- [ ] A pull request that deletes the scan step cannot merge, demonstrated rather than described.
- [ ] Owner review is required on every path CODEOWNERS names.
- [ ] `ROADMAP.md` 1.3 and gate G8 are ticked only with the demonstrations attached, and the pinning answer from 0.13 is recorded wherever the design states the guarantee.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- [`.github/workflows/ci.yml`](https://github.com/airlock-sec/airlock/blob/main/.github/workflows/ci.yml) (the checks that must become required)
- [`scripts/check_roadmap_touched.sh`](https://github.com/airlock-sec/airlock/blob/main/scripts/check_roadmap_touched.sh)
- [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) (1.3, 0.13, G8)
- GitHub's branch protection and ruleset documentation, read for what the plan supports

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
