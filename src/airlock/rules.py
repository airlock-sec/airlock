"""Rule loading and validation, the pattern engine and the line cap. Task 2.5 and 2.12.

Rules are TOML data validated in code at load time; an invalid rule file is a config error
that exits 2, never a silently dropped rule (ARCHITECTURE.md 6.4). Regexes run only on
lines at or under `policy.line_cap`; longer lines become `cfg-long-line` findings.
"""
