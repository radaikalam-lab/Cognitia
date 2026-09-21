"""Cognitia TinyML Reasoning Provider Scaffold.

Defines provider interface and mock for local edge models (classification, anomaly detection, state estimation).
MANDATORY INVARIANT: TinyML outputs are candidate inferences, not direct actuator commands.
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol, runtime_checkable

from cognitia.abi.types import current_utc_timestamp, generate_entity_id
from cognitia.epistemic.types import EpistemicStatus
from cognitia.provenance.record import ProvenanceRecord, SourceType
from cognitia.providers.types import (
    AdvancedCapabilityType,
    CandidateReasoningArtifact,
    ProposalLifecycleStatus,
    ReasoningRequest,
)
from cognitia.reasoning.types import ReasoningInput


@runtime_checkable
class TinyMLReasoningProvider(Protocol):
    """Protocol for TinyML local edge reasoning providers."""

    provider_id: str
    provider_version: str
    model_id: str
    model_version: str
    calibration_checksum: str

    def capabilities(self) -> tuple[AdvancedCapabilityType, ...]: ...

    def infer(
        self,
        request: ReasoningRequest,
        input_snapshot: ReasoningInput,
    ) -> CandidateReasoningArtifact: ...


class MockTinyMLProvider:
    """Deterministic reference mock implementing TinyMLReasoningProvider."""

    def __init__(
        self,
        provider_id: str = "mock_tinyml_provider",
        provider_version: str = "1.0.0",
        model_id: str = "edge_anomaly_detector_v1",
        model_version: str = "1.0.0",
        calibration_checksum: str = "a1b2c3d4e5f67890",
    ) -> None:
        self.provider_id = provider_id
        self.provider_version = provider_version
        self.model_id = model_id
        self.model_version = model_version
        self.calibration_checksum = calibration_checksum

    def capabilities(self) -> tuple[AdvancedCapabilityType, ...]:
        return (AdvancedCapabilityType.TINYML_REASONING,)

    def infer(
        self,
        request: ReasoningRequest,
        input_snapshot: ReasoningInput,
    ) -> CandidateReasoningArtifact:
        payload = {
            "model_type": "quantized_decision_forest",
            "feature_vector_dimension": len(input_snapshot.premises),
            "anomaly_score": 0.12,
            "classification_label": "NORMAL_OPERATION",
            "inference_latency_us": 450,
            "calibration_checksum": self.calibration_checksum,
        }

        prov = ProvenanceRecord(
            source_type=SourceType.ML_MODEL,
            producer_id=f"{self.provider_id}:{self.provider_version}",
            model_id=self.model_id,
            model_version=self.model_version,
            parent_ids=[input_snapshot.provenance.id, request.request_id],
            is_deterministic=True,
        )

        return CandidateReasoningArtifact(
            provider_id=self.provider_id,
            provider_version=self.provider_version,
            model_id=self.model_id,
            model_version=self.model_version,
            input_snapshot_id=input_snapshot.context_id,
            artifact_type="tinyml_inference_candidate",
            payload=payload,
            assumptions=(
                "TinyML model operates on localized input features.",
                "Outputs represent candidate statistical inferences.",
            ),
            epistemic_status=EpistemicStatus.UNRESOLVED,
            proposal_status=ProposalLifecycleStatus.PROPOSED,
            provenance=prov,
        )
