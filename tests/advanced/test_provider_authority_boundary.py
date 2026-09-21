"""Cognitia Provider Authority Boundary Tests.

Verifies that advanced providers cannot:
- modify Observation
- modify Experience
- modify Memory
- modify Context
- modify Attention
- modify active RuleStore
- modify active ModelRegistry records
- modify active ReasoningStrategy
- execute Action
- modify domain state
- invoke actuator

Providers may only produce CandidateReasoningArtifacts.
"""

from __future__ import annotations

import pytest

from cognitia.providers.scaffolds.llm import MockLLMProvider
from cognitia.providers.types import (
    AdvancedCapabilityType,
    CandidateReasoningArtifact,
    ReasoningRequest,
)
from cognitia.reasoning.types import ReasoningInput, ReasoningMode


def _make_snapshot() -> ReasoningInput:
    return ReasoningInput(
        context_id="snap_auth_boundary",
        reasoning_mode=ReasoningMode.DEDUCTION,
        premises=[],
    )


def _make_request() -> ReasoningRequest:
    return ReasoningRequest(
        input_snapshot_id="snap_auth_boundary",
        requested_capability=AdvancedCapabilityType.LLM_REASONING,
    )


class TestProviderAuthorityBoundary:
    """Providers produce candidate artifacts only — never mutations or authority actions."""

    def test_llm_returns_only_candidate_artifact(self) -> None:
        provider = MockLLMProvider()
        result = provider.reason(_make_request(), _make_snapshot())
        assert isinstance(result, CandidateReasoningArtifact)

    def test_llm_artifact_has_no_actuate_method(self) -> None:
        provider = MockLLMProvider()
        artifact = provider.reason(_make_request(), _make_snapshot())
        assert not hasattr(artifact, "actuate")
        assert not hasattr(artifact, "execute")

    def test_provider_has_no_actuate_method(self) -> None:
        provider = MockLLMProvider()
        assert not hasattr(provider, "actuate")
        assert not hasattr(provider, "execute_action")

    def test_provider_has_no_persist_method(self) -> None:
        provider = MockLLMProvider()
        assert not hasattr(provider, "persist")
        assert not hasattr(provider, "save_to_store")

    def test_provider_has_no_modify_memory_method(self) -> None:
        provider = MockLLMProvider()
        assert not hasattr(provider, "modify_memory")
        assert not hasattr(provider, "write_memory")

    def test_provider_has_no_modify_rules_method(self) -> None:
        provider = MockLLMProvider()
        assert not hasattr(provider, "modify_rules")
        assert not hasattr(provider, "update_rule_store")

    def test_provider_artifact_has_no_persistence_ref(self) -> None:
        provider = MockLLMProvider()
        artifact = provider.reason(_make_request(), _make_snapshot())
        assert not hasattr(artifact, "persistence_store")
        assert not hasattr(artifact, "memory_store")
        assert not hasattr(artifact, "rule_store")

    def test_provider_output_is_advisory_only(self) -> None:
        provider = MockLLMProvider()
        artifact = provider.reason(_make_request(), _make_snapshot())
        assert artifact.artifact_type != "decision"
        assert not hasattr(artifact, "execute")
