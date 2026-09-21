"""Tests for Consolidation Pipeline, Candidate Artifacts, and Versioned Plasticity."""

import dataclasses
import pytest

from cognitia.epistemic.service import InMemoryEpistemicService
from cognitia.memory.consolidation import (
    InMemoryConsolidationService,
    PlasticityOperator,
)
from cognitia.memory.types import (
    CandidateLearningArtifact,
    CandidateType,
    ConsolidationResult,
    ConsolidationStatus,
    MemoryContext,
)
from cognitia.models.registry import (
    InMemoryModelRegistry,
    ModelRecord,
    ModelStatus,
)
from cognitia.provenance.record import ProvenanceRecord, SourceType


class MockPlasticityOperator:
    """Reference plasticity operator mining candidate patterns from MemoryContext."""

    def __init__(self) -> None:
        self.operator_id = "mock_pattern_detector"
        self.provider_name = "tiny_ml_miner"

    def propose_candidate(self, context: MemoryContext) -> CandidateLearningArtifact:
        prov = ProvenanceRecord(
            source_type=SourceType.ML_MODEL,
            producer_id=f"{self.provider_name}:{self.operator_id}",
            parent_ids=[context.id],
            is_deterministic=True,
        )
        return CandidateLearningArtifact(
            candidate_type=CandidateType.MODEL_REVISION,
            source_memory_ids=[e.id for e in context.experiences],
            proposed_change={"target_model_id": "acoustic_model", "target_version": "1.1.0"},
            rationale="Aggregated 50 episodes of resonance frequency drift",
            confidence=0.88,
            provider=self.provider_name,
            provenance=prov,
        )


def test_candidate_creation_and_provenance():
    """Verify Plasticity Operator generates a CandidateLearningArtifact with complete lineage."""
    operator = MockPlasticityOperator()
    context = MemoryContext()
    candidate = operator.propose_candidate(context)

    assert isinstance(candidate, CandidateLearningArtifact)
    assert candidate.candidate_type == CandidateType.MODEL_REVISION
    assert candidate.confidence == 0.88
    assert candidate.provenance.producer_id == "tiny_ml_miner:mock_pattern_detector"
    assert context.id in candidate.provenance.parent_ids


def test_candidate_does_not_mutate_model_or_registry():
    """Verify that creating a candidate learning artifact leaves the active ModelRegistry untouched."""
    registry = InMemoryModelRegistry()
    initial_model = ModelRecord(
        model_id="acoustic_model",
        model_version="1.0.0",
        calibration_checksum="chk_v1",
        status=ModelStatus.ACTIVE,
    )
    registry.register(initial_model)

    operator = MockPlasticityOperator()
    candidate = operator.propose_candidate(MemoryContext())

    # Invariant: Active model registry still only contains version 1.0.0
    assert len(registry.list_versions("acoustic_model")) == 1
    assert registry.get_active("acoustic_model").model_version == "1.0.0"


def test_candidate_can_be_refuted():
    """Verify that candidates with insufficient epistemic support are marked REFUTED/REJECTED."""
    consolidation_service = InMemoryConsolidationService()
    epistemic_service = InMemoryEpistemicService()

    weak_candidate = CandidateLearningArtifact(
        candidate_type=CandidateType.PATTERN,
        confidence=0.45,  # Below threshold
        proposed_change={"target_model_id": "acoustic_model", "target_version": "1.0.1"},
    )

    result = consolidation_service.evaluate_candidate(weak_candidate, epistemic_service)
    assert result.status == ConsolidationStatus.REFUTED

    # Attempting to consolidate a non-supported candidate must raise ValueError
    registry = InMemoryModelRegistry()
    with pytest.raises(ValueError, match="Cannot consolidate candidate with status 'refuted'"):
        consolidation_service.consolidate(result, registry)


def test_validated_candidate_consolidates_into_distinct_version_n_plus_one():
    """Verify that supported candidates consolidate into Version N+1, preserving Version N (Versioned Plasticity)."""
    registry = InMemoryModelRegistry()
    v1_model = ModelRecord(
        model_id="acoustic_model",
        model_version="1.0.0",
        calibration_checksum="chk_v1",
        status=ModelStatus.ACTIVE,
    )
    registry.register(v1_model)

    operator = MockPlasticityOperator()
    candidate = operator.propose_candidate(MemoryContext())

    consolidation_service = InMemoryConsolidationService()
    epistemic_service = InMemoryEpistemicService()

    eval_result = consolidation_service.evaluate_candidate(candidate, epistemic_service)
    assert eval_result.status == ConsolidationStatus.SUPPORTED

    # Consolidate into version 1.1.0
    v2_model = consolidation_service.consolidate(eval_result, registry, provider_name="tiny_ml_miner")

    assert v2_model.model_id == "acoustic_model"
    assert v2_model.model_version == "1.1.0"

    # Both versions must be queryable in registry
    versions = registry.list_versions("acoustic_model")
    assert len(versions) == 2
    version_numbers = {v.model_version for v in versions}
    assert version_numbers == {"1.0.0", "1.1.0"}

    # Historical V1 record must remain strictly immutable and retrievable
    retrieved_v1 = registry.get("acoustic_model", "1.0.0")
    assert retrieved_v1 is not None
    assert retrieved_v1.calibration_checksum == "chk_v1"
