"""Cognitia Reinforcement Learning Provider Scaffold.

Defines provider interface and mock for RL policy evaluation.
MANDATORY INVARIANT: RL policy outputs are candidate action proposals,
never directly executed actions or autonomous domain actuations.
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
class ReinforcementLearningProvider(Protocol):
    """Protocol for reinforcement learning providers."""

    provider_id: str
    provider_version: str
    model_id: str
    model_version: str

    def capabilities(self) -> tuple[AdvancedCapabilityType, ...]: ...

    def evaluate_policy(
        self,
        request: ReasoningRequest,
        input_snapshot: ReasoningInput,
    ) -> CandidateReasoningArtifact: ...


class MockRLProvider:
    """Deterministic reference mock implementing ReinforcementLearningProvider."""

    def __init__(
        self,
        provider_id: str = "mock_rl_provider",
        provider_version: str = "1.0.0",
        model_id: str = "offline_actor_critic_v1",
        model_version: str = "1.0.0",
    ) -> None:
        self.provider_id = provider_id
        self.provider_version = provider_version
        self.model_id = model_id
        self.model_version = model_version

    def capabilities(self) -> tuple[AdvancedCapabilityType, ...]:
        return (AdvancedCapabilityType.REINFORCEMENT_LEARNING,)

    def evaluate_policy(
        self,
        request: ReasoningRequest,
        input_snapshot: ReasoningInput,
    ) -> CandidateReasoningArtifact:
        payload = {
            "policy_type": "discrete_action_q_policy",
            "state_dimension": len(input_snapshot.premises),
            "candidate_action_proposal": {
                "action_name": "ADJUST_VALVE_TARGET",
                "parameters": {"target_position_pct": 75.0},
                "expected_return": 8.45,
            },
            "exploration_mode": "deterministic_greedy",
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
            artifact_type="rl_policy_candidate_proposal",
            payload=payload,
            assumptions=(
                "RL output is an advisory proposal subject to safety and physical constraint checks.",
                "RL provider possesses ZERO execution or domain authority.",
            ),
            epistemic_status=EpistemicStatus.UNRESOLVED,
            proposal_status=ProposalLifecycleStatus.PROPOSED,
            provenance=prov,
        )
