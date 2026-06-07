"""Placeholder SP 16 verification layer."""

from __future__ import annotations

from pydantic import BaseModel


class VerificationResult(BaseModel):
    section_id: str
    passed: bool
    utilization_max: float | None = None
    governing_check: str = "placeholder"
    note: str = "MVP placeholder. Replace with verified SP 16 checks or LIRA verification."


def placeholder_verify(section_id: str) -> VerificationResult:
    return VerificationResult(section_id=section_id, passed=False)
