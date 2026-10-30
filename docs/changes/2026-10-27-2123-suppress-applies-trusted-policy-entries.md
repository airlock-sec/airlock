---
date: 2026-10-27 21:23 UTC
tasks: 2.8, 2.6, 2.7, 7.6
summary: `suppress()` applies the trusted policy's entries after numbering and before the reporters: matching needs rule, path and fingerprint together, so a second copy of a suppressed line returns unsuppressed (B5).
---

`suppress()` applies the trusted policy's entries after numbering and before the
reporters: matching needs rule, path and fingerprint together, so a second copy of a
suppressed line is its own occurrence and returns unsuppressed (B5); an expired entry
stops applying and says nothing else, because the returning finding is the signal (B10);
`expires` inside 30 days, the day itself included, yields `suppression-expiring` (WARN);
the clock is a parameter, so a run is reproducible. An entry naming a rule that is
missing, non-suppressible or a scanner-state id yields `suppression-invalid` (HIGH), and
on the first run of this task it covered the finding as well while the report complained
about it: validity is now decided before matching, which is what 7.6 said all along.
Entries are checked against the rule data rather than against this scan's findings, so a
renamed or retightened rule is reported even when the entry matched nothing. Suppressed
findings stay in the result carrying the entry's reason, since a reader has to see what
a policy hid. Verified: `pytest` 317 passed (33 new), `ruff check` and `ruff format
--check` clean on 36 files, `mypy src` clean on 24 files. Not verified: suppressions
reached through a real CLI run, which is 2.10
