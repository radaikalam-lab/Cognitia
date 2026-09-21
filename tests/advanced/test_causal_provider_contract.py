"""Cognitia Causal Inference Provider Contract Tests."""

from __future__ import annotations

import pytest

from cognitia.providers.scaffolds.causal import CausalInferenceProvider, MockCausalProvider
from cognitia.providers.types import (
    AdvancedCapabilityType,
    ReasoningRequest,
)
from cognitia.reasoning.types import ReasoningInput, ReasoningMode


def _make_snapshot() -> ReasoningInput:
    return ReasoningInput(
        context_id="causal_snap",
        reasoning_mode=ReasoningMode.CAUSAL,
        premises=[],
    )


class TestCausalProviderContract:
    def test_mock_implements_protocol(self) -> None:
        provider = MockCausalProvider()
        assert isinstance(provider, CausalInferenceProvider)

    def test_capabilities_returns_causal_inference(self) -> None:
        provider = MockCausalProvider()
        assert AdvancedCapabilityType.CAUSAL_INFERENCE in provider.capabilities()

    def test_discover_causal_structure_returns_candidate(self) -> None:
        from cognitia.providers.types import CandidateReasoningArtifact
        request = ReasoningRequest(
            input_snapshot_id="causal_snap",
            requested_capability=AdvancedCapabilityType.CAUSAL_INFERENCE,
        )
        provider = MockCausalProvider()
        result = provider.discover_causal_structure(request, _make_snapshot())
        assert isinstance(result, CandidateReasoningArtifact)

    def test_learned_causal_graph_is_not_truth(self) -> None:
        request = ReasoningRequest(
            input_snapshot_id="causal_snap",
            requested_capability=AdvancedCapabilityType.CAUSAL_INFERENCE,
        )
        provider = MockCausalProvider()
        artifact = provider.discover_causal_structure(request, _make_snapshot())
        assert artifact.epistemic_status.name == "UNRESOLVED"

    def test_payload_contains_expected_keys(self) -> None:
        request = ReasoningRequest(
            input_snapshot_id="causal_snap",
            requested_capability=AdvancedCapabilityType.CAUSAL_INFERENCE,
        )
        provider = MockCausalProvider()
        artifact = provider.discover_causal_structure(request, _make_snapshot())
        payload = artifact.payload_dict
        assert "candidate_directed_edges" in payload
        assert "algorithm" in payload
