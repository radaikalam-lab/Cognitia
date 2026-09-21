"""Cognitia Semantic Graph Provider Contract Tests."""

from __future__ import annotations

import pytest

from cognitia.providers.scaffolds.semantic_graph import (
    SemanticGraphProvider,
    MockSemanticGraphProvider,
)
from cognitia.providers.types import (
    AdvancedCapabilityType,
    ReasoningRequest,
)
from cognitia.reasoning.types import ReasoningInput, ReasoningMode


def _make_snapshot() -> ReasoningInput:
    return ReasoningInput(
        context_id="semantic_snap",
        reasoning_mode=ReasoningMode.DEDUCTION,
        premises=[],
    )


class TestSemanticGraphContract:
    def test_mock_implements_protocol(self) -> None:
        provider = MockSemanticGraphProvider()
        assert isinstance(provider, SemanticGraphProvider)

    def test_capabilities_returns_semantic_graph(self) -> None:
        provider = MockSemanticGraphProvider()
        assert AdvancedCapabilityType.SEMANTIC_GRAPH in provider.capabilities()

    def test_query_graph_returns_candidate(self) -> None:
        from cognitia.providers.types import CandidateReasoningArtifact
        request = ReasoningRequest(
            input_snapshot_id="semantic_snap",
            requested_capability=AdvancedCapabilityType.SEMANTIC_GRAPH,
        )
        provider = MockSemanticGraphProvider()
        result = provider.query_graph(request, _make_snapshot())
        assert isinstance(result, CandidateReasoningArtifact)

    def test_graph_edge_is_not_established_fact(self) -> None:
        request = ReasoningRequest(
            input_snapshot_id="semantic_snap",
            requested_capability=AdvancedCapabilityType.SEMANTIC_GRAPH,
        )
        provider = MockSemanticGraphProvider()
        artifact = provider.query_graph(request, _make_snapshot())
        assert artifact.epistemic_status.name == "UNRESOLVED"

    def test_payload_contains_expected_keys(self) -> None:
        request = ReasoningRequest(
            input_snapshot_id="semantic_snap",
            requested_capability=AdvancedCapabilityType.SEMANTIC_GRAPH,
        )
        provider = MockSemanticGraphProvider()
        artifact = provider.query_graph(request, _make_snapshot())
        payload = artifact.payload_dict
        assert "graph_nodes" in payload
        assert "graph_edges" in payload
