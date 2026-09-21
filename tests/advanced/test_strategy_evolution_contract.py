"""Cognitia Reasoning Strategy Evolution Provider Contract Tests."""

from __future__ import annotations

import pytest

from cognitia.providers.scaffolds.evolution import (
    ReasoningStrategyEvolutionProvider,
    MockStrategyEvolutionProvider,
)
from cognitia.providers.types import (
    AdvancedCapabilityType,
    ReasoningRequest,
)
from cognitia.reasoning.types import ReasoningInput, ReasoningMode


def _make_snapshot() -> ReasoningInput:
    return ReasoningInput(
        context_id="evolution_snap",
        reasoning_mode=ReasoningMode.DEDUCTION,
        premises=[],
    )


class TestStrategyEvolutionContract:
    def test_mock_implements_protocol(self) -> None:
        provider = MockStrategyEvolutionProvider()
        assert isinstance(provider, ReasoningStrategyEvolutionProvider)

    def test_capabilities_returns_self_modifying_reasoning(self) -> None:
        provider = MockStrategyEvolutionProvider()
        assert AdvancedCapabilityType.SELF_MODIFYING_REASONING in provider.capabilities()

    def test_propose_strategy_revision_returns_candidate(self) -> None:
        from cognitia.providers.types import CandidateReasoningArtifact
        request = ReasoningRequest(
            input_snapshot_id="evolution_snap",
            requested_capability=AdvancedCapabilityType.SELF_MODIFYING_REASONING,
        )
        provider = MockStrategyEvolutionProvider()
        result = provider.propose_strategy_revision(request, _make_snapshot())
        assert isinstance(result, CandidateReasoningArtifact)

    def test_candidate_revision_is_not_active_strategy(self) -> None:
        request = ReasoningRequest(
            input_snapshot_id="evolution_snap",
            requested_capability=AdvancedCapabilityType.SELF_MODIFYING_REASONING,
        )
        provider = MockStrategyEvolutionProvider()
        artifact = provider.propose_strategy_revision(request, _make_snapshot())
        assert artifact.epistemic_status.name == "UNRESOLVED"
        assert artifact.proposal_status.name == "PROPOSED"

    def test_payload_contains_expected_keys(self) -> None:
        request = ReasoningRequest(
            input_snapshot_id="evolution_snap",
            requested_capability=AdvancedCapabilityType.SELF_MODIFYING_REASONING,
        )
        provider = MockStrategyEvolutionProvider()
        artifact = provider.propose_strategy_revision(request, _make_snapshot())
        payload = artifact.payload_dict
        assert "target_strategy_id" in payload
        assert "proposed_strategy_version" in payload
        assert "revision_type" in payload
