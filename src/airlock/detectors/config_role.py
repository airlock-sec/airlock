"""P0 detector: capability rules over role `tooling-config`. Task 3.1.

Rules: `cfg-dynamic-code` (HIGH, not suppressible), `cfg-network-exec`, `cfg-network`,
`cfg-process-spawn`, `cfg-chain-endpoint`, `cfg-appended-tail`, `cfg-long-line`, `cfg-nul`.

Matches raw text: no comment or string masking (ADR-013). Network or spawn alone is WARN;
dynamic code, or both together, is HIGH.
"""
