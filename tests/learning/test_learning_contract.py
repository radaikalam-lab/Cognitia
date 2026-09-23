"""Tests for Adaptive Learning Provider Contract and Registry."""

import pytest

from cognitia.learning.contract import (
    AdaptiveInferenceRequest,
    AdaptiveLearningFailure,
    AdaptiveLearningResult,
    ModelInputRepresentation,
    TaskType,
)
from cognitia.learning.laya_provider import LayaProvider
from cognitia.models.registry import InMemoryModelRegistry, ModelRecord, ModelStatus
from cognitia.provenance.record import ProvenanceRecord, SourceType


def test_laya_implements_adaptive_provider_protocol():
    """Verify that LayaProvider conforms to AdaptiveLearningProvider protocol."""
    provider = LayaProvider()

    assert provider.provider_id == "laya"
    assert provider.provider_version == "1.0.0"
    assert TaskType.CLASSIFICATION in provider.supported_tasks
    assert TaskType.SCORING in provider.supported_tasks
    assert TaskType.RANKING in provider.supported_tasks
    assert TaskType.CONFIDENCE_ESTIMATION in provider.supported_tasks
    assert TaskType.ANOMALY_DETECTION in provider.supported_tasks
    assert TaskType.INTERPRETATION in provider.supported_tasks
    assert provider.is_deterministic is True


def test_model_record_registration_and_status():
    """Verify model record registration and lifecycle states."""
    registry = InMemoryModelRegistry()
    record = ModelRecord(
        model_id="laya_acoustic_v1",
        model_version="1.0.0",
        provider="laya",
        status=ModelStatus.ACTIVE,
        is_deterministic=True,
    )
    registry.register(record)

    fetched = registry.get("laya_acoustic_v1", "1.0.0")
    assert fetched is not None
    assert fetched.model_id == "laya_acoustic_v1"
    assert fetched.status == ModelStatus.ACTIVE

    with pytest.raises(ValueError):
        registry.register(record)


def test_adaptive_learning_result_authority_invariant():
    """Verify that AdaptiveLearningResult strictly enforces authority='NONE'."""
    prov = ProvenanceRecord(source_type=SourceType.NEURAL_MODEL)
    
    valid_res = AdaptiveLearningResult(
        model_id="laya_acoustic_v1",
        task=TaskType.CLASSIFICATION,
        output={"decision": "resonance"},
        confidence=0.88,
        provenance=prov,
        authority="NONE",
    )
    assert valid_res.authority == "NONE"

    with pytest.raises(ValueError, match="must strictly be 'NONE'"):
        AdaptiveLearningResult(
            model_id="laya_acoustic_v1",
            task=TaskType.CLASSIFICATION,
            output={"decision": "resonance"},
            authority="FULL_EXECUTION",
        )
