"""Baseline ML helpers."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable


class FrequencySectionRecommender:
    """Simple smoke-test baseline. This is not an engineering verification method."""

    def __init__(self, top_k: int = 5) -> None:
        if top_k < 1:
            raise ValueError("top_k must be at least 1")
        self.top_k = top_k
        self._labels: list[str] = []

    def fit(self, selected_section_ids: Iterable[str]) -> "FrequencySectionRecommender":
        labels = [label for label in selected_section_ids if label]
        if not labels:
            raise ValueError("No labels for training")
        counter = Counter(labels)
        self._labels = [label for label, _ in counter.most_common(self.top_k)]
        return self

    def predict_top_k(self) -> list[str]:
        if not self._labels:
            raise RuntimeError("Model is not fitted")
        return self._labels[: self.top_k]
