"""Cognitia LLM Reasoning Provider Scaffold.

Defines the provider-neutral interface and deterministic reference mock for LLM reasoning capabilities.
MANDATORY INVARIANT: LLM outputs are strictly candidate artifacts (CandidateReasoningArtifact),
never physical truth, decisions, or domain authority.
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
class LLMReasoningProvider(Protocol):
    """Protocol for LLM reasoning capability providers."""

    provider_id: str
    provider_version: str
    model_id: str
    model_version: str

    def capabilities(self) -> tuple[AdvancedCapabilityType, ...]: ...

    def reason(
        self,
        request: ReasoningRequest,
        input_snapshot: ReasoningInput,
    ) -> CandidateReasoningArtifact: ...


class MockLLMProvider:
    """Deterministic reference mock implementing LLMReasoningProvider for contract validation."""

    def __init__(
        self,
        provider_id: str = "mock_llm_provider",
        provider_version: str = "1.0.0",
        model_id: str = "mock_reasoner_llm",
        model_version: str = "1.0.0",
    ) -> None:
        self.provider_id = provider_id
        self.provider_version = provider_version
        self.model_id = model_id
        self.model_version = model_version

    def capabilities(self) -> tuple[AdvancedCapabilityType, ...]:
        return (AdvancedCapabilityType.LLM_REASONING,)

    def reason(
        self,
        request: ReasoningRequest,
        input_snapshot: ReasoningInput,
    ) -> CandidateReasoningArtifact:
        # Formulate deterministic candidate response from snapshot premises
        premise_count = len(input_snapshot.premises)
        payload = {
            "prompt_tokens_estimated": premise_count * 50,
            "completion_tokens_estimated": 100,
            "candidate_narrative": f"LLM reasoning synthesis over {premise_count} snapshot premises under mode {request.reasoning_mode.value}",
            "generated_hypotheses": [
                f"Synthetic LLM hypothesis based on {input_snapshot.context_id}"
            ],
        }

        prov = ProvenanceRecord(
            source_type=SourceType.NEURAL_MODEL,
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
            artifact_type="llm_reasoning_candidate",
            payload=payload,
            assumptions=(
                "LLM reasoning output is a probabilistic candidate synthesis.",
                "Must undergo epistemic evaluation before belief adoption.",
            ),
            epistemic_status=EpistemicStatus.UNRESOLVED,  # Invariant: Starts UNRESOLVED
            proposal_status=ProposalLifecycleStatus.PROPOSED,
            provenance=prov,
        )
