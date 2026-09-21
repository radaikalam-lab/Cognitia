"""Cognitia Provider Provenance Tests."""

from __future__ import annotations

import pytest

from cognitia.providers.scaffolds.llm import MockLLMProvider
from cognitia.providers.scaffolds.tinyml import MockTinyMLProvider
from cognitia.providers.types import (
    AdvancedCapabilityType,
    ReasoningRequest,
)
from cognitia.reasoning.types import ReasoningInput, ReasoningMode


def _make_snapshot() -> ReasoningInput:
    return ReasoningInput(
        context_id="snap_prov_001",
        reasoning_mode=ReasoningMode.DEDUCTION,
        premises=[],
    )


def _make_request() -> ReasoningRequest:
    return ReasoningRequest(
        input_snapshot_id="snap_prov_001",
        requested_capability=AdvancedCapabilityType.LLM_REASONING,
    )


class TestProviderProvenance:
    """Tests verifying that provider outputs carry correct provenance."""

    def test_artifact_has_provenance_record(self) -> None:
        provider = MockLLMProvider()
        artifact = provider.reason(_make_request(), _make_snapshot())
        assert artifact.provenance is not None
        assert artifact.provenance.producer_id is not None

    def test_artifact_provenance_has_parent_snapshot_id(self) -> None:
        provider = MockLLMProvider()
        artifact = provider.reason(_make_request(), _make_snapshot())
        parent_ids = artifact.provenance.parent_ids
        # The snapshot provenance.id (a UUID) is linked as parent
        assert len(parent_ids) >= 1

    def test_artifact_provenance_has_request_id(self) -> None:
        provider = MockLLMProvider()
        request = _make_request()
        artifact = provider.reason(request, _make_snapshot())
        assert request.request_id in artifact.provenance.parent_ids

    def test_tinyml_provenance_has_model_references(self) -> None:
        request = ReasoningRequest(
            input_snapshot_id="snap_prov_001",
            requested_capability=AdvancedCapabilityType.TINYML_REASONING,
        )
        provider = MockTinyMLProvider(
            model_id="edge_model_v2",
            model_version="3.0.0",
        )
        artifact = provider.infer(request, _make_snapshot())
        assert artifact.provenance.model_id == "edge_model_v2"
        assert artifact.provenance.model_version == "3.0.0"

    def test_provenance_is_deterministic(self) -> None:
        provider = MockLLMProvider()
        request = _make_request()
        snapshot = _make_snapshot()
        a1 = provider.reason(request, snapshot)
        a2 = provider.reason(request, snapshot)
        assert a1.provenance.is_deterministic is True

    def test_provenance_has_input_checksum(self) -> None:
        provider = MockLLMProvider()
        artifact = provider.reason(_make_request(), _make_snapshot())
        assert artifact.provenance.input_checksums is not None
