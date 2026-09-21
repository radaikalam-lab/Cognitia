"""Cognitia Vector Similarity Provider Contract Tests."""

from __future__ import annotations

import pytest

from cognitia.providers.scaffolds.similarity import SimilarityProvider, MockSimilarityProvider
from cognitia.providers.types import (
    AdvancedCapabilityType,
    ReasoningRequest,
)
from cognitia.reasoning.types import ReasoningInput, ReasoningMode


def _make_snapshot() -> ReasoningInput:
    return ReasoningInput(
        context_id="similarity_snap",
        reasoning_mode=ReasoningMode.ANALOGY,
        premises=[],
    )


class TestSimilarityProviderContract:
    def test_mock_implements_protocol(self) -> None:
        provider = MockSimilarityProvider()
        assert isinstance(provider, SimilarityProvider)

    def test_capabilities_returns_vector_retrieval(self) -> None:
        provider = MockSimilarityProvider()
        assert AdvancedCapabilityType.VECTOR_RETRIEVAL in provider.capabilities()

    def test_find_similar_returns_candidate(self) -> None:
        from cognitia.providers.types import CandidateReasoningArtifact
        request = ReasoningRequest(
            input_snapshot_id="similarity_snap",
            requested_capability=AdvancedCapabilityType.VECTOR_RETRIEVAL,
        )
        provider = MockSimilarityProvider()
        result = provider.find_similar(request, _make_snapshot())
        assert isinstance(result, CandidateReasoningArtifact)

    def test_similarity_is_not_truth(self) -> None:
        request = ReasoningRequest(
            input_snapshot_id="similarity_snap",
            requested_capability=AdvancedCapabilityType.VECTOR_RETRIEVAL,
        )
        provider = MockSimilarityProvider()
        artifact = provider.find_similar(request, _make_snapshot())
        assert artifact.epistemic_status.name == "UNRESOLVED"

    def test_similarity_is_not_causality(self) -> None:
        request = ReasoningRequest(
            input_snapshot_id="similarity_snap",
            requested_capability=AdvancedCapabilityType.VECTOR_RETRIEVAL,
        )
        provider = MockSimilarityProvider()
        artifact = provider.find_similar(request, _make_snapshot())
        assert artifact.epistemic_status.name != "SUPPORTED"

    def test_payload_contains_expected_keys(self) -> None:
        request = ReasoningRequest(
            input_snapshot_id="similarity_snap",
            requested_capability=AdvancedCapabilityType.VECTOR_RETRIEVAL,
        )
        provider = MockSimilarityProvider()
        artifact = provider.find_similar(request, _make_snapshot())
        payload = artifact.payload_dict
        assert "similarity_basis" in payload
        assert "metric" in payload
        assert "ranked_candidates" in payload
