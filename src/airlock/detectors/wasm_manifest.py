"""P0 detector: Wasm artifacts against the hash-keyed manifest. Task 3.4.

Rules: `wasm-unlisted`, `wasm-hash-mismatch`, `wasm-path-moved`, `wasm-manifest-stale`,
`wasm-archive-skipped`. Wasm is identified by the magic bytes `00 61 73 6D`, never by file
extension (ADR-010).
"""
