---
date: 2026-10-28 13:34 UTC
tasks: 1.13, 1.14, 2.15, 3.9, 8.4, D-05
summary: Wave-readiness prep, drafted locally and published nowhere.
---

Wave-readiness prep, drafted locally and published nowhere. `README.md` is rewritten
around what a stranger to the project asks first (what runs, what does not, what it
costs to contribute): a status table that separates the shipped pipeline from the
unbuilt Action and the unbuilt Stellar detectors, the two severity tables for the twelve
rules, the trust model per mode, the exit-code table, and a quick start that works from
a checkout today. Two sentences written during the draft were softened before commit
because they asserted labels and issues that do not exist yet. `SUPPORT.md` gives the
exact commands CI runs and the three rules that most often close a pull request.
`docs/wave/issues/` holds fifteen issues in the program's template, each grounded in a
file and a line rather than in a roadmap bullet: 5 Trivial, 7 Medium, 3 High, 2,150
pre-multiplier points against a per-repo ceiling read as 25,000. Writing them found two
things. (a) Task 2.15: `policy._entry_problem` tests `STATE_RULE_IDS` only on the branch
where the rule is *absent*, so `cfg-long-line`, which is both scanner-state and a loaded
rule with `suppressible = true`, can be suppressed with no `suppression-invalid`
reported. Reproduced on `main` in a scratch repository: a 30,013-character line plus a
`[[suppress]]` entry printed `1 HIGH · 1 suppressed` and nothing else. (b) Three Phase 7
rows (7.3, 7.10, 7.11) appear to be satisfied by tests that already ship, so issue 06
asks for an audit against the suite rather than new code, and names the one real gap
(CRLF at collector level). Measuring the batch also corrected section 2: five of the
seven Appendix B cases fail closed on the twelve shipped rules and cases 6 and 7 exit 0,
which is why 3.9's dependency on 3.6 is now stated in the issue and the stale "six-rule
set" sentence is gone. Each body carries a `## Tech stack` block naming the files the
work touches, the test command for that area and the protected paths in the way, so the
issue is pickable without a tour. `docs/wave/settings.md` records the topics, the label
set and a ruleset naming the two real check contexts, read from the workflows and
confirmed on pull request #18's head (`checks` and `roadmap`, both from the
`github-actions` app, integration `15368`), and `docs/wave/application.md` drafts the
submission including the row that says there is no adoption evidence.
`scripts/create_wave_issues.sh` publishes the batch in filename order, dry run unless
`--apply`, and refuses to create anything while the repository has no `Stellar Wave`
label, because on an unapproved repository the label is stripped silently and the issue
scores nothing. No public state was changed to write any of this: the `gh` calls used
were reads, and the publisher was run only in dry-run mode (15 issues staged, 0
created). Verified: 475 tests pass, `ruff check` and `ruff format --check` clean on 45
files, `mypy src` clean on 24, `airlock scan --mode full .` exit 0, `roadmap_progress.py
--check` exit 0 after the table regenerated (Phase 1 8 of 14, Phase 2 14 of 15, total 32
of 92), every `github.com/airlock-sec/airlock/blob/main/...` link in the batch resolves
to a tracked path, and the repo-context banner is byte-identical across all fifteen
files. Not verified and not done: nothing is published, so no issue number exists and
the `{{issue:slug}}` references in the bodies are still tokens; no topic, label, ruleset
or tag has been applied; the publisher's `--apply` path has never called the API; task
8.4 and decision D-05 stay open, because whether to apply to this program at all is the
owner's call and a rejected repository cannot re-apply
