import pytest

from steel_frame_designer.ml_model import FrequencySectionRecommender


def test_frequency_recommender_returns_top_k() -> None:
    model = FrequencySectionRecommender(top_k=2)
    model.fit(["30B1", "30B1", "35B1", "40B1"])

    assert model.predict_top_k() == ["30B1", "35B1"]


def test_frequency_recommender_requires_fit() -> None:
    model = FrequencySectionRecommender(top_k=2)

    with pytest.raises(RuntimeError):
        model.predict_top_k()
