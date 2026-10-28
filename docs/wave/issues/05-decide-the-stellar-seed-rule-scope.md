---
slug: decide-the-stellar-seed-rule-scope
title: Check whether gitleaks and TruffleHog already detect Stellar secret seeds, and decide D-06
labels: Stellar Wave, complexity: trivial, area: detectors, documentation
roadmap: 0.7
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** Research and a recorded decision, with no code to change and no dependency on another issue. It is the gate on two Phase 6 rows: 6.2 (`strkey.py`) and 6.3 (the detector) both wait on the outcome.

## Problem

`ARCHITECTURE.md` 9.4 specifies a Stellar secret-seed detector: a candidate matching
`\bS[A-Z2-7]{55}\b`, base32-decoded to 35 bytes, version byte `0x90`, with a CRC16-XModem checksum
over the first 33 bytes matching the trailing two. The row ends with
`[Unverified: byte details recalled from memory]`.

Two things are wrong with building on that. The first is the marker itself: those byte details have
not been checked against a reference, and a checksum rule written from memory either misses seeds or
fires on 56-character noise. The second is the more useful question, and it is task 0.7: **is this
Airlock's job at all?** Secret scanning is a crowded, well-tooled space. If gitleaks and TruffleHog
already carry a Stellar strkey rule, then a third implementation is duplicated effort with a worse
test history, and the honest answer is decision D-06's second or third option: narrow the rule to
what those tools miss, or drop it and point users at a tool that does it properly.

D-06 is Open in the `ROADMAP.md` decision log, and
[`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 10 says an open
decision blocks the work behind it. That is what this issue unblocks.

## What to build

1. **Check the two tools at the source.** Read the current gitleaks default rule set and TruffleHog's
   detectors in their repositories, not in a blog post. Report whether either matches a Stellar
   `S…` secret seed, with the rule id or file path and the commit you read. Note whether they decode
   and verify the checksum or only pattern-match, because that difference is the whole coverage
   question: a pattern-only rule fires on test vectors and misses anything adjacent.
2. **Verify the encoding details** you are reasoning about, from the reference implementation in
   `stellar-go` or the `strkey` specification, and record them. Do not correct one remembered
   constant with another.
3. **Recommend, then let the owner decide.** Fill in D-06 with keep, narrow or drop, the evidence
   line, and the date. Write the reasoning into the pull request so the decision can be reviewed
   rather than taken on trust. If the answer is "drop", say what replaces it in the PRD's FR list
   rather than deleting the requirement silently.
4. **Adjust the queue.** If D-06 lands as narrow or drop, tasks 6.2 and 6.3 and
   `ARCHITECTURE.md` 9.4 change shape. Update the rows in this pull request so the roadmap and the
   decision log do not contradict each other the day the decision is recorded.

**Out of scope:** implementing `strkey.py` or the detector. This issue ends at the decision.

## Acceptance criteria

- [ ] The pull request names the gitleaks and TruffleHog rules found, with file paths and the commit or version read, or states plainly that neither has one.
- [ ] The strkey byte details in `ARCHITECTURE.md` 9.4 are confirmed against a reference or corrected, and the `[Unverified]` marker there is gone or replaced with a citation.
- [ ] D-06 in the `ROADMAP.md` decision log reads Decided, with the date, the choice and the evidence.
- [ ] Tasks 6.2 and 6.3, and `PRD.md`'s corresponding FR row, are consistent with that decision.
- [ ] `ROADMAP.md` carries a changelog row with a UTC date, `Last updated` moved, and `python scripts/roadmap_progress.py --check` passing.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass.
- [ ] No live-looking seed is committed anywhere in the repository: test vectors are constructed from a documented reference, and a real-looking `S…` string in a fixture is a rejection.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- Runtime: Python 3.11, standard library only. [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 forbids adding a runtime dependency, and a scan never touches the network, so a helper library is not an option here.
- Code today: [`src/airlock/detectors/stellar_seed.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/detectors/stellar_seed.py) and [`src/airlock/strkey.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/strkey.py) are stubs of a few lines each, registered as neither `DETECTORS` nor `DETECTOR_NAMES` in [`src/airlock/detectors/__init__.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/detectors/__init__.py).
- Design text: [`ARCHITECTURE.md`](https://github.com/airlock-sec/airlock/blob/main/ARCHITECTURE.md) 9.4, which carries a `[Unverified: byte details recalled from memory]` marker, and decision D-06 in [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md).
- Three honest outcomes: keep the rule, narrow it, or drop it because gitleaks and TruffleHog already cover it. A drop closes this issue and deletes the stub, so write the comparison in the pull request either way.
- Do not commit a live-looking seed while testing the tools you compare. Build any probe key from fragments, per [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4.

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md) — where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md) — private disclosure only; never open an issue about a bypass
