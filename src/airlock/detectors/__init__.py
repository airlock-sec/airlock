"""Detector registry: a plain list of in-tree detector functions.

Third-party detector plugins are not supported; loading external code would defeat the
trust model (ARCHITECTURE.md 6.3). `DETECTORS` is empty until the P0 detectors land in
tasks 3.1, 3.4 and 3.6, and a scan with no registered detectors is a config error, not a
pass.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable

from ..model import Finding, ScanContext

Detector = Callable[[ScanContext], Iterable[Finding]]

DETECTORS: tuple[Detector, ...] = ()
