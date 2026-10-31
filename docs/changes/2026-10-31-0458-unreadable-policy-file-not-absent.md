---
date: 2026-10-31 04:58 UTC
tasks: 7.15
summary: Close #55 (task 7.15): an unreadable working-tree policy or manifest file is reported as unreadable at WARN, not as absent.
---

Close #55 (task 7.15). In `full` mode `policy._working_text` folded every `OSError` into
"absent", so a policy file the scanner could not open (mode 000, a directory in its place, an I/O
error) produced `no airlock.toml in the working tree, so the shipped defaults apply`. The new
`policy._read_working` treats only `FileNotFoundError` and `NotADirectoryError` as absent. Any
other `OSError` still falls back to `BOOTSTRAP_POLICY` (or the empty manifest), as before, but `untrusted-policy-source` now says the file is in the working tree but could not be
read and names `type(exc).__name__` and the errno name (never `str(exc)`, as `skipped-unreadable`
does). Severity is WARN rather than INFO because the maintainer's suppressions and settings are not
being applied and they may not know. It is not HIGH because the scan still runs on the shipped
defaults; those are not always stricter (a policy that lowers `max_file_bytes` is not applied), so
the finding says which settings apply rather than calling the fallback fail-closed.
The absent case keeps its INFO text, which `README.md` relies on. The rule ID is unchanged, so
`ARCHITECTURE_ESSENTIALS.md` needs no new ID. Whether a scan should stop on an unreadable policy is
left out of scope as the issue asks; falling back and saying so remains the answer.
Tests in `tests/unit/test_policy.py::TestFullMode` cover absent (exact message), unreadable as a
directory in place of the file and as mode 000 (skipped on Windows and when running as root, where a
mode 000 file is still readable) and over-cap, for both `airlock.toml` and `wasm-manifest.toml`.
Updated `ARCHITECTURE.md` 6.5 pseudo-code, `site/trust.html` and `ROADMAP.md`.
