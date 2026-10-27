"""GitHub annotation reporter. Task 2.9.

Emits `::error` and `::warning` commands, escaping `%`, CR, LF, `:` and `,` in properties.
HIGH comes first and WARN annotations are capped, because per-step annotation limits are
hit by real findings (ARCHITECTURE.md 6.6, limits confirmed by task 0.9).
"""
