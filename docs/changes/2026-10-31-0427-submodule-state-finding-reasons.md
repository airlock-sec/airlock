---
date: 2026-10-31 04:27 UTC
tasks: 7.14
summary: Unmapped gitlink findings now name .gitmodules state-finding IDs and explain why severity remains HIGH.
---

The collector previously reduced `.gitmodules` state findings to a boolean. When the mapping file could not be used, a gitlink therefore received only the generic “no matching path and url” message, hiding whether the file was oversized, contained NUL text, or had another state finding.

The collector now preserves the sorted finding IDs from `.gitmodules` and includes them in each affected `submodule-unmapped` message. The finding remains HIGH, with the message stating that its subtree is not scanned. Regression tests use temporary Git repositories to cover oversized and NUL-containing `.gitmodules` files, and verify that a malformed section still yields both `submodule-orphan` and `submodule-unmapped`.

Updated FR-20 and the collector architecture summaries to document the diagnostic behavior.
