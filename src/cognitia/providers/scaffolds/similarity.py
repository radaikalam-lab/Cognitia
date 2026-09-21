"""Cognitia Vector Similarity Provider Scaffold.

Defines provider interface and mock for vector embedding and nearest-neighbor retrieval.
MANDATORY INVARIANT: Vector similarity != Semantic Truth != Causality != Attention.
Similarity ranking must never silently override cognitive attention or epistemic validation.
"""

from __future__ import annotations

from typing import Any, Protocol, Sequence, runtime_checkable

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
class SimilarityProvider(Protocol):
    """Protocol for vector similarity and retrieval providers."""

    provider_id: str
    provider_version: str
    model_id: str
    model_version: str

    def capabilities(self) -> tuple[AdvancedCapabilityType, ...]: ...

    def find_similar(
        self,
        request: ReasoningRequest,
        input_snapshot: ReasoningInput,
    ) -> CandidateReasoningArtifact: ...


class MockSimilarityProvider:
    """Deterministic reference mock implementing SimilarityProvider."""

    def __init__(
        self,
        provider_id: str = "mock_similarity_provider",
        provider_version: str = "1.0.0",
        model_id: str = "synthetic_embedder_v1",
        model_version: str = "1.0.0",
    ) -> None:
        self.provider_id = provider_id
        self.provider_version = provider_version
        self.model_id = model_id
        self.model_version = model_version

    def capabilities(self) -> tuple[AdvancedCapabilityType, ...]:
        return (AdvancedCapabilityType.VECTOR_RETRIEVAL,)

    def find_similar(
        self,
        request: ReasoningRequest,
        input_snapshot: ReasoningInput,
    ) -> CandidateReasoningArtifact:
        # Generate deterministic synthetic similarity scores
        candidates = [
            {"candidate_id": "item_alpha", "score": 0.94, "metric": "cosine"},
            {"candidate_id": "item_beta", "score": 0.81, "metric": "cosine"},
        ]

        payload = {
            "similarity_basis": "deterministic_token_hash_projection",
            "metric": "cosine",
            "dimension": 128,
            "ranked_candidates": candidates,
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
            artifact_type="vector_similarity_candidate",
            payload=payload,
            assumptions=(
                "Vector similarity indicates geometric proximity in embedding space.",
                "Similarity does NOT imply factual truth, causality, or task attention priority.",
            ),
            epistemic_status=EpistemicStatus.UNRESOLVED,
            proposal_status=ProposalLifecycleStatus.PROPOSED,
            provenance=prov,
        )
