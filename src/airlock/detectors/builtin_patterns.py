"""P0 family: the data rules ported from `malware_scan.py`. Task 3.6 and 3.7.

This module holds no code and registers no detector, which is the point rather than an oversight.
Every rule in `rules/builtin/builtin_patterns.toml` declares `detector = "pattern"`, so the engine's
line pass in `rules.apply_patterns` is the only reporter for the family, and a code detector here
would be a second path for the same text to be judged. What is ported so far is the text-side slice:
`pat-decode-eval`, `pat-invisible-unicode`, `pat-exfil-endpoint` and `pat-obfuscator-id`. The CI
surface shapes still wait on a `workflow` role, and the `build.rs` and native-binary families belong
with the Cargo work in 6.4.

Task 3.8's parity harness compares this set against the old script on a shared corpus, which needs
0.10's corpus before it can say anything. Scope, residuals and the measured per-line cost of each
pattern are recorded in `ARCHITECTURE.md` 9.6.
"""
