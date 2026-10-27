"""P1 detector: Soroban release-profile hygiene and `testutils` placement. Task 6.1.

Applies to contract crates only, meaning a manifest whose `crate-type` contains `cdylib`
(ADR-016). Expected profile values, build target and SDK version come from policy; nothing
is hardcoded here (ADR-011).
"""
