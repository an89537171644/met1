"""Section-selection helpers."""

from __future__ import annotations

from collections.abc import Iterable

from .checks_sp16 import VerificationResult


def first_passing_result(results: Iterable[VerificationResult]) -> VerificationResult | None:
    for result in results:
        if result.passed:
            return result
    return None
