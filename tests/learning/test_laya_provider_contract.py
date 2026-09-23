"""Tests for Laya Surrogate Provider Contract (AL0/AL1/AL3).

Verifies the deterministic surrogate provider contract, surrogate transparency,
offline inference, and strict authority=NONE invariants.
"""

import pytest

from cognitia.learning.contract import (
    AdaptiveInferenceRequest,
    AdaptiveLearningResult,
    CandidateStatus,
    ModelInputRepresentation,
    TaskType,
)
from cognitia.learning.laya_provider import (
    LayaProvider,
    LayaSurrogateProvider,
)
from cognitia.models.registry import ModelRecord, ModelStatus


def test_laya_surrogate_identity_and_transparency():
    """Verify surrogate provider accurately declares its provider_type as surrogate."""
    provider = LayaSurrogateProvider()
    assert provider.provider_id == "laya"
    assert provider.provider_version == "1.0.0"
    assert provider.provider_type == "surrogate"
    assert provider.is_deterministic is True

    # Test backwards compatibility alias
    alias_provider = LayaProvider()
    assert alias_provider.provider_type == "surrogate"
    assert isinstance(alias_provider, LayaSurrogateProvider)


def test_laya_surrogate_inference_contract():
    """Verify surrogate inference returns valid typed decision with authority=NONE."""
    provider = LayaSurrogateProvider(is_deterministic=True, default_seed=42)
    rep = ModelInputRepresentation(
        source_reference="test_obs_001",
        features={"spl_db": 85.0, "frequency_hz": 1200.0},
        sanitized_text="Acoustic resonance test sample",
    )
    req = AdaptiveInferenceRequest(
        model_id="laya_acoustic_v1",
        model_version="1.0.0",
        task=TaskType.CLASSIFICATION,
        representation=rep,
        is_deterministic=True,
    )
    res = provider.infer(req)

    assert isinstance(res, AdaptiveLearningResult)
    assert res.authority == "NONE"
    assert res.epistemic_status == "UNRESOLVED"
    assert res.provider_id == "laya"
    assert "decision" in res.output
    assert "scores" in res.output
    assert res.confidence > 0.0


def test_laya_surrogate_learning_preserves_active_immutability():
    """Verify learning generates candidate without mutating active model."""
    provider = LayaSurrogateProvider()
    base_rec = ModelRecord(
        model_id="laya_acoustic_v1",
        model_version="1.0.0",
        provider="laya",
        status=ModelStatus.ACTIVE,
    )
    provider.load_model(base_rec)
    base_weights_before = dict(provider._get_effective_weights("laya_acoustic_v1", "1.0.0"))

    from cognitia.learning.contract import LearningEvent
    event = LearningEvent(
        domain_id="default",
        feedback_ids=["fb_1", "fb_2"],
        model_id="laya_acoustic_v1",
        model_version="1.0.0",
        sample_count=2,
        data_fingerprint="test_fp_001",
    )

    candidate, update = provider.learn(
        events=[event],
        base_model=base_rec,
        seed=42,
    )

    assert candidate.authority == "NONE"
    assert candidate.status == CandidateStatus.CANDIDATE
    assert candidate.parent_model_version == "1.0.0"
    assert candidate.candidate_model_version.endswith("-candidate")
    assert update.authority == "NONE"

    # Verify base model weights were not mutated
    base_weights_after = provider._get_effective_weights("laya_acoustic_v1", "1.0.0")
    assert base_weights_before["bias"] == base_weights_after["bias"]
