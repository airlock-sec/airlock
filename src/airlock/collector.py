"""File collection: `git ls-files -z --stage`, reads, decoding and limits. Task 2.2 and 2.3.

Planned behavior (ARCHITECTURE.md 6.1): no default directory skips, size and line caps,
BOM-aware strict decoding, symlinks recorded not followed, submodules reported. This module
is one of only two allowed to call `subprocess`, with a fixed argument list and no shell.
"""
