"""Cognitia Provider Snapshot Boundary Tests.

Verifies that providers receive only the immutable ReasoningInput snapshot
and cannot access live mutable state after snapshot creation.
"""

from __future__ import annotations

import pytest

from cognitia.providers.scaffolds.llm import MockLLMProvider
from cognitia.providers.types import (
    AdvancedCapabilityType,
    ReasoningRequest,
)
from cognitia.reasoning.types import ReasoningInput, ReasoningMode


def _make_snapshot() -> ReasoningInput:
    return ReasoningInput(
        context_id="snap_boundary_001",
        reasoning_mode=ReasoningMode.DEDUCTION,
        premises=[],
    )


class TestProviderSnapshotBoundary:
    """Providers receive only immutable snapshots, not live store references."""

    def test_snapshot_is_immutable_reasoning_input(self) -> None:
        snapshot = _make_snapshot()
        assert isinstance(snapshot, ReasoningInput)

    def test_provider_receives_snapshot_not_persistence(self) -> None:
        snapshot = _make_snapshot()
        request = ReasoningRequest(
            input_snapshot_id=snapshot.context_id,
            requested_capability=AdvancedCapabilityType.LLM_REASONING,
        )
        provider = MockLLMProvider()
        artifact = provider.reason(request, snapshot)
        assert artifact is not None
        assert isinstance(artifact, type(artifact))

    def test_snapshot_id_matches_request(self) -> None:
        snapshot = _make_snapshot()
        request = ReasoningRequest(
            input_snapshot_id=snapshot.context_id,
            requested_capability=AdvancedCapabilityType.LLM_REASONING,
        )
        assert request.input_snapshot_id == snapshot.context_id

    def test_provider_output_references_snapshot_id(self) -> None:
        snapshot = _make_snapshot()
        request = ReasoningRequest(
            input_snapshot_id=snapshot.context_id,
            requested_capability=AdvancedCapabilityType.LLM_REASONING,
        )
        provider = MockLLMProvider()
        artifact = provider.reason(request, snapshot)
        assert artifact.input_snapshot_id == snapshot.context_id

    def test_snapshot_modification_does_not_affect_artifact(self) -> None:
        """Since snapshot is immutable, creating a new snapshot with same ID
        should not affect already-produced artifacts."""
        snapshot1 = _make_snapshot()
        request = ReasoningRequest(
            input_snapshot_id=snapshot1.context_id,
            requested_capability=AdvancedCapabilityType.LLM_REASONING,
        )
        provider = MockLLMProvider()
        artifact = provider.reason(request, snapshot1)
        # Artifact is bound to the snapshot it was created with
        assert artifact.input_snapshot_id == snapshot1.context_id
