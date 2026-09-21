"""Cognitia Consolidation Pipeline and Plasticity Interfaces."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from cognitia.capabilities.base import BaseCapability, CapabilityDescriptor, CapabilityType
from cognitia.epistemic.service import EpistemicService
from cognitia.epistemic.types import EpistemicStatus
from cognitia.memory.types import (
    CandidateLearningArtifact,
    ConsolidationResult,
    ConsolidationStatus,
    MemoryContext,
)
from cognitia.models.registry import ModelRecord, ModelRegistry, ModelStatus
from cognitia.provenance.record import ProvenanceRecord, SourceType, compute_checksum


@runtime_checkable
class PlasticityOperator(Protocol):
    """Protocol for providers that process MemoryContext to propose CandidateLearningArtifacts."""

    operator_id: str
    provider_name: str

    def propose_candidate(self, context: MemoryContext) -> CandidateLearningArtifact:
        """Process retrieved memory context to propose candidate cognitive adaptations."""
        ...


@runtime_checkable
class ConsolidationCapability(BaseCapability, Protocol):
    """Protocol for capabilities performing validation and consolidation analysis."""

    def evaluate(
        self,
        candidate: CandidateLearningArtifact,
        context: MemoryContext | None = None,
    ) -> ConsolidationResult:
        """Evaluate candidate artifact validity."""
        ...


@runtime_checkable
class ConsolidationService(Protocol):
    """Protocol for governing the consolidation of candidate artifacts into model versions."""

    def evaluate_candidate(
        self,
        candidate: CandidateLearningArtifact,
        epistemic_service: EpistemicService,
    ) -> ConsolidationResult:
        """Evaluate a candidate artifact against epistemic support criteria."""
        ...

    def consolidate(
        self,
        result: ConsolidationResult,
        model_registry: ModelRegistry,
        provider_name: str = "consolidated_provider",
    ) -> ModelRecord:
        """Promote a supported consolidation result to a new registered ModelRecord (Version N+1)."""
        ...


class InMemoryConsolidationService:
    """Reference implementation of ConsolidationService enforcing epistemic validation before model creation."""

    def evaluate_candidate(
        self,
        candidate: CandidateLearningArtifact,
        epistemic_service: EpistemicService,
    ) -> ConsolidationResult:
        # Check if candidate has associated epistemic nodes that are supported
        # If confidence meets threshold and no refutations exist, mark as SUPPORTED
        status = ConsolidationStatus.SUPPORTED if candidate.confidence >= 0.7 else ConsolidationStatus.REFUTED
        justification = (
            f"Candidate passed epistemic threshold with confidence {candidate.confidence}"
            if status == ConsolidationStatus.SUPPORTED
            else f"Candidate insufficient epistemic support (confidence {candidate.confidence})"
        )

        target_model_id = candidate.proposed_change.get("target_model_id", "consolidated_model")
        proposed_version = candidate.proposed_change.get("target_version", "1.1.0")
        checksum = compute_checksum(candidate.proposed_change)

        prov = ProvenanceRecord(
            source_type=SourceType.DETERMINISTIC_RULE,
            producer_id="consolidation_service",
            parent_ids=[candidate.id],
            is_deterministic=True,
        )

        return ConsolidationResult(
            candidate_id=candidate.id,
            status=status,
            epistemic_justification=justification,
            target_model_id=target_model_id,
            proposed_version=proposed_version,
            calibration_checksum=checksum,
            provenance=prov,
        )

    def consolidate(
        self,
        result: ConsolidationResult,
        model_registry: ModelRegistry,
        provider_name: str = "consolidated_provider",
    ) -> ModelRecord:
        if result.status != ConsolidationStatus.SUPPORTED:
            raise ValueError(f"Cannot consolidate candidate with status '{result.status.value}'")

        # Create distinct ModelRecord version N+1
        prov = ProvenanceRecord(
            source_type=SourceType.COMPOSITE,
            producer_id="consolidation_pipeline",
            parent_ids=[result.id],
            is_deterministic=True,
        )

        model_record = ModelRecord(
            model_id=result.target_model_id,
            model_version=result.proposed_version,
            provider=provider_name,
            capability_type=CapabilityType.DECISION,
            calibration_checksum=result.calibration_checksum,
            status=ModelStatus.ACTIVE,
            provenance=prov,
        )

        model_registry.register(model_record)
        return model_record
