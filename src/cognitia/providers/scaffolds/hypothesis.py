"""Cognitia Autonomous Hypothesis Generation Provider Scaffold.

Defines provider interface and mock for autonomous candidate hypothesis generation.
MANDATORY INVARIANT: Generated hypotheses are candidates (CandidateReasoningArtifact),
never automatically promoted, registered, or asserted as accepted truth.
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
class HypothesisGenerationProvider(Protocol):
    """Protocol for hypothesis generation providers."""

    provider_id: str
    provider_version: str

    def capabilities(self) -> tuple[AdvancedCapabilityType, ...]: ...

    def generate_hypotheses(
        self,
        request: ReasoningRequest,
        input_snapshot: ReasoningInput,
    ) -> CandidateReasoningArtifact: ...


class MockHypothesisProvider:
    """Deterministic reference mock implementing HypothesisGenerationProvider."""

    def __init__(
        self,
        provider_id: str = "mock_hypothesis_provider",
        provider_version: str = "1.0.0",
    ) -> None:
        self.provider_id = provider_id
        self.provider_version = provider_version

    def capabilities(self) -> tuple[AdvancedCapabilityType, ...]:
        return (AdvancedCapabilityType.HYPOTHESIS_GENERATION,)

    def generate_hypotheses(
        self,
        request: ReasoningRequest,
        input_snapshot: ReasoningInput,
    ) -> CandidateReasoningArtifact:
        payload = {
            "generation_basis": "abductive_pattern_clustering",
            "source_observations": [p.id for p in input_snapshot.premises],
            "candidate_propositions": [
                {
                    "statement": f"Hypothesis on latent dynamic in context {input_snapshot.context_id}",
                    "test_criteria": ["Validate against empirical historical trace"],
                }
            ],
            "assumptions": ["Observations reflect unperturbed system operation"],
            "unknowns": ["Unobserved external atmospheric pressure"],
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
            artifact_type="candidate_hypothesis_artifact",
            payload=payload,
            assumptions=("Generated candidate hypothesis requires independent evidential corroboration.",),
            epistemic_status=EpistemicStatus.UNRESOLVED,
            proposal_status=ProposalLifecycleStatus.PROPOSED,
            provenance=prov,
        )
