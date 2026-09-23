"""Tests for Laya Reference Provider Typed Decisions and Inference."""

import pytest

from cognitia.learning.contract import (
    AdaptiveInferenceRequest,
    AdaptiveLearningFailure,
    AdaptiveLearningResult,
    ModelInputRepresentation,
    TaskType,
)
from cognitia.learning.laya_provider import LayaProvider
from cognitia.models.registry import ModelRecord


def test_laya_classification_typed_decision():
    """Verify that Laya produces structured typed classification decisions."""
    provider = LayaProvider(is_deterministic=True)
    rep = ModelInputRepresentation(
        input_type="observation",
        source_reference="obs_mic_1",
        features={"spl_db": 95.5, "frequency_hz": 440.0},
        sanitized_text="Acoustic sensor measurement",
    )

    req = AdaptiveInferenceRequest(
        model_id="laya_acoustic_v1",
        model_version="1.0.0",
        task=TaskType.CLASSIFICATION,
        representation=rep,
        is_deterministic=True,
    )

    result = provider.infer(req)
    assert isinstance(result, AdaptiveLearningResult)
    assert result.provider_id == "laya"
    assert result.authority == "NONE"
    assert result.epistemic_status == "UNRESOLVED"
    assert "decision" in result.output
    assert "scores" in result.output
    assert result.confidence > 0.0
    scores = result.output["scores"]
    assert pytest.approx(sum(scores.values()), 0.05) == 1.0


def test_laya_deterministic_reproducibility():
    """Verify that same input and random seed produce strictly identical outputs."""
    provider = LayaProvider(is_deterministic=True)
    rep = ModelInputRepresentation(
        input_type="observation",
        source_reference="obs_sensor_stable",
        features={"temperature_c": 22.4, "vibration_rms": 0.04},
    )

    req1 = AdaptiveInferenceRequest(
        model_id="laya_acoustic_v1",
        model_version="1.0.0",
        task=TaskType.CLASSIFICATION,
        representation=rep,
        random_seed=12345,
        is_deterministic=True,
    )
    req2 = AdaptiveInferenceRequest(
        model_id="laya_acoustic_v1",
        model_version="1.0.0",
        task=TaskType.CLASSIFICATION,
        representation=rep,
        random_seed=12345,
        is_deterministic=True,
    )

    res1 = provider.infer(req1)
    res2 = provider.infer(req2)

    assert res1.output == res2.output
    assert res1.confidence == res2.confidence


def test_laya_scoring_and_ranking():
    """Verify hypothesis scoring and candidate ranking tasks."""
    provider = LayaProvider(is_deterministic=True)
    rep = ModelInputRepresentation(
        input_type="evidence",
        source_reference="ev_spectral_1",
        features={"confidence": 0.85, "q_factor": 12.5},
    )

    req_score = AdaptiveInferenceRequest(
        model_id="laya_acoustic_v1",
        model_version="1.0.0",
        task=TaskType.SCORING,
        representation=rep,
        parameters={"hypotheses": ["H1_standing_wave", "H2_structural_noise"]},
    )
    res_score = provider.infer(req_score)
    assert "scores" in res_score.output
    assert "top_hypothesis" in res_score.output

    req_rank = AdaptiveInferenceRequest(
        model_id="laya_acoustic_v1",
        model_version="1.0.0",
        task=TaskType.RANKING,
        representation=rep,
        parameters={"candidates": ["opt_filter_a", "opt_filter_b", "opt_filter_c"]},
    )
    res_rank = provider.infer(req_rank)
    assert "ranked_candidates" in res_rank.output
    assert len(res_rank.output["ranked_candidates"]) == 3


def test_laya_confidence_and_anomaly_detection():
    """Verify confidence estimation and anomaly detection."""
    provider = LayaProvider()
    rep = ModelInputRepresentation(
        input_type="observation",
        source_reference="obs_temp_anomaly",
        features={"temperature_c": 120.0},
    )

    req_anom = AdaptiveInferenceRequest(
        model_id="laya_acoustic_v1",
        model_version="1.0.0",
        task=TaskType.ANOMALY_DETECTION,
        representation=rep,
        parameters={"threshold": 0.5},
    )
    res_anom = provider.infer(req_anom)
    assert "is_anomaly" in res_anom.output
    assert res_anom.output["is_anomaly"] is True
