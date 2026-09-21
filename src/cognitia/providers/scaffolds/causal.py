"""Cognitia Learned Causal Inference Provider Scaffold.

Defines provider interface and mock for learned causal structure discovery.
MANDATORY INVARIANT: Learned causal graphs are candidate causal structures,
never established causal truth. Must pass through Epistemic Evaluation.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

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
class CausalInferenceProvider(Protocol):
    """Protocol for learned causal inference providers."""

    provider_id: str
    provider_version: str

    def capabilities(self) -> tuple[AdvancedCapabilityType, ...]: ...

    def discover_causal_structure(
        self,
        request: ReasoningRequest,
        input_snapshot: ReasoningInput,
    ) -> CandidateReasoningArtifact: ...


class MockCausalProvider:
    """Deterministic reference mock implementing CausalInferenceProvider."""

    def __init__(
        self,
        provider_id: str = "mock_causal_provider",
        provider_version: str = "1.0.0",
    ) -> None:
        self.provider_id = provider_id
        self.provider_version = provider_version

    def capabilities(self) -> tuple[AdvancedCapabilityType, ...]:
        return (AdvancedCapabilityType.CAUSAL_INFERENCE,)

    def discover_causal_structure(
        self,
        request: ReasoningRequest,
        input_snapshot: ReasoningInput,
    ) -> CandidateReasoningArtifact:
        payload = {
            "algorithm": "constraint_based_dag_discovery",
            "candidate_directed_edges": [
                {"cause": "variable_A", "effect": "variable_B", "mechanism": "inferred_directed_coupling"}
            ],
            "faithfulness_assumed": True,
            "latent_confounders_possible": True,
        }

        prov = ProvenanceRecord(
            source_type=SourceType.REASONING_ENGINE,
            producer_id=f"{self.provider_id}:{self.provider_version}",
            parent_ids=[input_snapshot.provenance.id, request.request_id],
            is_deterministic=True,
        )

        return CandidateReasoningArtifact(
            provider_id=self.provider_id,
            provider_version=self.provider_version,
            input_snapshot_id=input_snapshot.context_id,
            artifact_type="candidate_causal_structure",
            payload=payload,
            assumptions=("Learned causal graph is an advisory hypothesis subject to intervention tests.",),
            epistemic_status=EpistemicStatus.UNRESOLVED,
            proposal_status=ProposalLifecycleStatus.PROPOSED,
            provenance=prov,
        )
