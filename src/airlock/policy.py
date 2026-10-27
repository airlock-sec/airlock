"""Trusted-base resolution, policy loading and suppression application. Task 2.7 and 2.8.

Policy, suppressions and the Wasm manifest come from the trusted base (PR base in `pr`
mode, `github.event.before` in `push` mode), never from HEAD. An unresolvable base, an
invalid config or missing git must exit non-zero (ARCHITECTURE.md 6.5 and 8). This module
and `collector.py` are the only ones allowed to call `subprocess`.
"""
