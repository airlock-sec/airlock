---
date: 2026-10-30 15:56 UTC
tasks: 3.6, FR-13, FR-14, R-2, 9.6, 3.7, 3.11
summary: Close the last two unblocked 3.6 indicators: `pat-credential-harvest` and `pat-chain-c2` land as WARN data rules, with the credential alternation anchored to cut its ReDoS-harness cost from 10.3 ms to 1.2 ms.
---

Migrated on 2026-10-30 by task 1.15 from the row this change hand-wrote into the section
9 table of `ROADMAP.md`, which is now generated. The text below is that row, re-wrapped
at 88 characters and with its table escapes turned back into pipes; nothing else was
changed.

Close the last two unblocked 3.6 indicators: `pat-credential-harvest` and `pat-chain-c2`
land as WARN rules in `rules/builtin/builtin_patterns.toml`, taking the file to six and
3.6's remaining list to the two Cargo-dependent shapes that belong to 6.4. The
credential rule names fourteen stores across ten alternation branches, by path and not
by directory (AWS credentials, four OpenSSH private-key names, the Solana CLI keypair,
GnuPG's `private-keys-v1.d`, Chrome's `Login Data` and `Local Storage/leveldb`,
`key3.db`/`key4.db`, `wallet.dat`, Electrum and MultiversX wallet dirs), because the old
script carried this list at HIGH and matched the folder, which is how a rule about paths
turns into a rule about false positives; trailing guards on the key branches are what
keep a provisioned public key out of a report, and the fixture's negative half is
exactly that: a `.pub`, a `pubring.kbx`, a `wallet.dat.bak` and an application config.
The chain rule names the public infrastructure the reported campaigns actually pointed
at (a Tron node provider, Tronscan, the BSC data seeds) rather than attacker domains, so
a campaign moving node is a one-line data edit. Tiering is the part a reviewer should
push on: `cfg-chain-endpoint` stays the stricter rule and the only one that can fail a
build, because it reads one of five config filenames and fires on an endpoint being
*configured*; this one reads every file that is code and fires on a host being *named*,
which a dApp integration does daily, and the same reasoning puts a key store at WARN.
Both are the pairing's half, not its conclusion, and 3.7 owns the HIGH that a named
store plus a decoder plus an endpoint makes; two tests assert the exit code stays 0 for
each shape on its own, so the tier is a check rather than a claim. One measurement
rewrote a shipped pattern: the flat ten-branch credential alternation cost 10.3 ms on
the ReDoS harness's worst cap-length line, inside the 60 ms per-line gate but priced by
paired scan of one corpus (the same 1 MB, once with the two new rules dropped from the
context) at 50 to 65 ms of the 1200 ms aggregate budget, and anchoring every branch
behind `[./\\."']` let `re` skip columns no branch can start at, which is 1.2 ms on the
same bait with the same recall across fifteen path spellings that
`TestTheCredentialAnchorKeepsItsRecall` now pins, including Windows separators and a
bare database name handed to a path join. 9.6 records the resulting headroom with its
noise: about 1040 ms median on this box, about 50 ms of run-to-run drift for an
unchanged configuration, and both `main` and this branch observed above the gate when
the machine is loaded. The cost of the anchor is recorded rather than hidden: a store
name with no separator, quote or dot in front of it is invisible, which for a path list
is no loss. The rules then found two of themselves in this repository (a comment quoting
`key4.db`, a fixture fragment holding the whole `Login Data` string) and both were fixed
at the source, not suppressed. Roles stayed at the four code roles the family already
names; the three CI roles are deliberately absent because `roles.py`'s extension
fallback already delivers them, and `TestTheCiSurfaceIsReachedByTheFallback` asserts a
workflow and a `package.json` reach the pattern path through that fallback instead of
trusting it. Docs: `ARCHITECTURE.md` 9.6 gains the two rules, the tier argument, the
anchoring measurement, the residual the anchor costs and the note that the remaining
aggregate headroom is stated with its run-to-run noise and belongs to 3.11 to re-derive
on the hosted runner rather than to widen; `ARCHITECTURE_ESSENTIALS.md` 7 names six ids;
README and `docs/wave/application.md` move to 24 rules and 739 tests; the
`detectors/builtin_patterns.py` stub docstring stops saying four.
`scripts/build_site.py` was run and its output committed, so the published rule
reference carries both rules at WARN. Verified locally, Python 3.14.0 while CI runs
3.11: `ruff check` clean, `ruff format --check` clean on 62 files, `mypy src` clean on
25 files, `airlock scan --mode full .` 0 HIGH · 0 WARN · 2 INFO over 125 files with
nothing skipped, `pytest` 739 collected (29 more than `main`), 737 passed with 1 skipped
on the run with both timing gates green. Every local red is a timing gate and they move
with machine load rather than with this change: a `main` worktree run in the same window
failed `test_a_cap_length_line_stays_inside_the_budget[config_role._DANGEROUS_COMMAND]`
the same way (77 to 90 ms against a 60 ms budget), and in this branch's busiest window
two more gates breached once each, `cfg-network`'s per-line case and the 1 MB aggregate
pass at 1214 ms, both of which pass in isolation here and neither of which this change
touches. `main` worst observed 1221 ms on the aggregate in a loaded window too. Hosted
CI runs every one of these gates green on `main` in about 25 s and the pull request's
own run is the measurement that decides. No budget, skip or marker in
`tests/unit/test_redos.py` was touched. `check_roadmap_touched.sh` was then run against
the pushed commit and exits 0, and the hosted run
[41088470408](https://github.com/airlock-sec/airlock/actions/runs/41088470408) put both
timing gates back inside their budgets on pull request #47: 738 passed with 1 skipped in
9.59 s on Python 3.11, with `ruff check`, `ruff format --check`, `mypy src`, the
self-scan and the `roadmap` checks all green (run 41088470296, 8 s). The hosted timing
envelope is therefore measured rather than assumed. merged into this branch after #46
landed and took `main` to `8568def`, which adds its 18 collected cases to this slice, so
the merged tree collects 758 tests and README and `docs/wave/application.md` state that
number. Not done by this row: the `build.rs` and native-binary families (6.4), the
pairings that make these two WARNs a verdict (3.7), and parity against the old script,
which still waits on 0.10's corpus

Two things the row said that are not true of the tree it merged into, corrected here
rather than in the row: it ends by counting "18 collected cases" from #46 and a merged
tree of 758 tests, and #46's own record
(`2026-10-30-1552-make-submodules-actionable-scanner.md`) reports 18 as the number of
cases in its two new classes rather than the suite total, so the sentence was an
inference about a count nobody had re-measured at that point; and "the hosted timing
envelope is therefore measured rather than assumed. merged into this branch after #46
landed" reads as one sentence where two were meant. The count that stands for the merged
tree is the one README and `docs/wave/application.md` now state: 24 rules and 796
collected cases.
