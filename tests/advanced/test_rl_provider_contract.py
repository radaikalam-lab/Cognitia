"""Cognitia Reinforcement Learning Provider Contract Tests."""

from __future__ import annotations

import pytest

from cognitia.providers.scaffolds.rl import ReinforcementLearningProvider, MockRLProvider
from cognitia.providers.types import (
    AdvancedCapabilityType,
    ReasoningRequest,
)
from cognitia.reasoning.types import ReasoningInput, ReasoningMode


def _make_snapshot() -> ReasoningInput:
    return ReasoningInput(
        context_id="rl_snap",
        reasoning_mode=ReasoningMode.DEDUCTION,
        premises=[],
    )


class TestRLProviderContract:
    def test_mock_implements_protocol(self) -> None:
        provider = MockRLProvider()
        assert isinstance(provider, ReinforcementLearningProvider)

    def test_capabilities_returns_reinforcement_learning(self) -> None:
        provider = MockRLProvider()
        assert AdvancedCapabilityType.REINFORCEMENT_LEARNING in provider.capabilities()

    def test_evaluate_policy_returns_candidate(self) -> None:
        from cognitia.providers.types import CandidateReasoningArtifact
        request = ReasoningRequest(
            input_snapshot_id="rl_snap",
            requested_capability=AdvancedCapabilityType.REINFORCEMENT_LEARNING,
        )
        provider = MockRLProvider()
        result = provider.evaluate_policy(request, _make_snapshot())
        assert isinstance(result, CandidateReasoningArtifact)

    def test_policy_output_is_not_executed_action(self) -> None:
        request = ReasoningRequest(
            input_snapshot_id="rl_snap",
            requested_capability=AdvancedCapabilityType.REINFORCEMENT_LEARNING,
        )
        provider = MockRLProvider()
        artifact = provider.evaluate_policy(request, _make_snapshot())
        assert artifact.epistemic_status.name == "UNRESOLVED"
        assert artifact.artifact_type == "rl_policy_candidate_proposal"

    def test_payload_contains_expected_keys(self) -> None:
        request = ReasoningRequest(
            input_snapshot_id="rl_snap",
            requested_capability=AdvancedCapabilityType.REINFORCEMENT_LEARNING,
        )
        provider = MockRLProvider()
        artifact = provider.evaluate_policy(request, _make_snapshot())
        payload = artifact.payload_dict
        assert "policy_type" in payload
        assert "candidate_action_proposal" in payload
        assert "expected_return" in payload["candidate_action_proposal"]
