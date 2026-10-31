---
date: 2026-10-31 05:38 UTC
tasks: 2.16
summary: Close #54 (task 2.16): refuse --base and --before when the resolved mode ignores them.
---

Close #54 (task 2.16). `cli._mode_for` already rejects a contradiction between `--event` and `--mode`. The same rule now applies one hop further: a flag the resolved mode discards is a `UsageError`.

`_validate_mode_flags` raises for `--base` in `full` or `push`, and for `--before` in `full` or `pr`. The message names the mode and the flag. Help text for both flags now states which mode consumes them. Accepted combinations are unchanged.

Tests in `tests/unit/test_cli.py::TestUsage` cover the ignored-flag cases and one accepted path. Existing `--event`/`--mode` tests continue to pass.
