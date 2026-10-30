---
date: 2026-10-27 22:09 UTC
tasks: 2.12, 3.1, 3.2, 3.4, 3.11, FR-13, FR-14
summary: The suite now proves the rules rather than trusting them.
---

The suite now proves the rules rather than trusting them. `tests/fixtures/` holds one
builder per shipped rule, named by that rule's own `tests` table, each with a positive
and a negative case assembled from fragments at call time (`_join("ev", "al")`,
`_join("wer", "get")`) and handed to the scanner as collected files: path, bytes,
content-magic role, whole-file hash, then through the engine pass and the whole detector
registry. `tests/unit/test_fixtures.py` asks every rule in `rules/builtin/` for both
halves, asserts the positive fires and the negative does not, refuses an orphaned
builder, and asserts no run produced `detector-error`, since a fixture that crashed a
detector would otherwise pass by accident. The negative cases are near misses rather
than empty files: `cfg-dynamic-code`'s is `evalOrder: "post"`, `cfg-chain-endpoint`'s is
`rpcRetries: 3`, and `cfg-network-exec`'s keeps the network half and drops the execution
half, which is the pairing the rule exists for. `tests/unit/test_redos.py` times every
pattern that sees attacker text, rule data and detector code alike, on cap-length
adversarial lines built from the pattern's own literal fragments plus runs of one
character, unbalanced brackets and dangling near misses. The measured worst is about 10
ms for the rule patterns and about 20 ms for `config_role`'s dangerous-command test
against a line of repeated `[a-z]`, and 1 MB of adversarial text through the whole
engine measures about 440 ms, so `PRD.md` 7 now states the bound per cap-length line,
which is the exposure the engine actually creates, instead of the earlier 50 ms per MB
target. That target is missed in aggregate by `cfg-network` (about 63 ms per MB) and
marginally by `cfg-chain-endpoint` (about 50 ms), so 3.11 records the measurement and
the candidate fix rather than quietly redefining the goal. FR-14's shape is confirmed
directly: a 5 MB single line costs 8 ms, because the length check is all that runs, and
the harness asserts the one finding it yields is `cfg-long-line` at line 1. Both failure
modes were checked by mutation and not assumed: a rule added to `config_role.toml` with
no builder fails the gate, and `cfg-dynamic-code` rewritten to `(a+)+b` fails with `inf
< 60.0` after ten seconds instead of hanging the run, because each measurement is taken
in a child process with a wall-clock limit and a canary pattern is asserted to breach
the same budget a shipped pattern is held to. 2.12, 3.1, 3.2 and 3.4 ticked;
`ARCHITECTURE.md` 12, `project_structure.md` 5 and 6 and `tests/fixtures/README.md`
corrected, including the claim that fixtures are written to a temporary directory (they
are not: only the trusted-base and bypass tests need a git repository, because there the
collector must run for real). Verified: `pytest` 433 passed (38 new), `ruff check` and
`ruff format --check` clean on 42 files, `mypy src` clean on 24 files, self-scan exit 0.
Not verified: timings on a standard GitHub runner, which is what 1.5 would give, and
whether the measured pattern cost matters on real repositories, which is the corpus gate
(0.10, 3.3)
