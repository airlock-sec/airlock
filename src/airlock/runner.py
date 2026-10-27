"""Detector orchestration. Task 2.11 (ARCHITECTURE.md 6.3).

Runs every detector in `detectors.DETECTORS` over the `ScanContext`, wraps each call so a
detector exception becomes a HIGH `detector-error` finding and the remaining detectors
still run, then applies suppressions and hands the result to the reporters.
"""
