"""Occurrence-aware fingerprints. Task 2.6 (ARCHITECTURE.md 7.3).

Planned formula:

    sha256(rule_id \\0 normalized_path \\0 normalized_evidence \\0 occurrence)

Line numbers stay out so an edit above a suppressed line does not invalidate the
suppression. `occurrence` is the zero-based index of identical evidence inside the file,
so a second copy of a suppressed line is a new finding. For file-level findings the file
SHA-256 replaces the evidence.
"""
