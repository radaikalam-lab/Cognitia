"""Cognitia Self-Modifying Reasoning Strategy Evolution Provider Scaffold.

Defines provider interface and mock for proposing strategy revisions (Strategy N -> Version N+1).
MANDATORY INVARIANT: Strategy revision proposals NEVER directly mutate active runtime strategies.
Activation requires sandbox validation, governance review, and explicit Version N+1 promotion.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

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
class ReasoningStrategyEvolutionProvider(Protocol):
    """Protocol for strategy evolution and self-modifying reasoning providers."""

    provider_id: str
    provider_version: str

    def capabilities(self) -> tuple[AdvancedCapabilityType, ...]: ...

    def propose_strategy_revision(
        self,
        request: ReasoningRequest,
        input_snapshot: ReasoningInput,
    ) -> CandidateReasoningArtifact: ...


class MockStrategyEvolutionProvider:
    """Deterministic reference mock implementing ReasoningStrategyEvolutionProvider."""

    def __init__(
        self,
        provider_id: str = "mock_strategy_evolution_provider",
        provider_version: str = "1.0.0",
    ) -> None:
        self.provider_id = provider_id
        self.provider_version = provider_version

    def capabilities(self) -> tuple[AdvancedCapabilityType, ...]:
        return (AdvancedCapabilityType.SELF_MODIFYING_REASONING,)

    def propose_strategy_revision(
        self,
        request: ReasoningRequest,
        input_snapshot: ReasoningInput,
    ) -> CandidateReasoningArtifact:
        payload = {
            "target_strategy_id": "deductive_strategy_primary",
            "proposed_strategy_version": "1.1.0",
            "revision_type": "parameter_tuning",
            "proposed_modifications": {
                "threshold_relaxation": 0.05,
                "residual_tolerance": "strict",
            },
            "justification": "Observed high premise correlation across recent historical episodes",
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
            artifact_type="candidate_strategy_revision",
            payload=payload,
            assumptions=(
                "Strategy revision is an immutable proposal for Version N+1.",
                "Currently active strategies remain completely unmutated.",
            ),
            epistemic_status=EpistemicStatus.UNRESOLVED,
            proposal_status=ProposalLifecycleStatus.PROPOSED,
            provenance=prov,
        )
