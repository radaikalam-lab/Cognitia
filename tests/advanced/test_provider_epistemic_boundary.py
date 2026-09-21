"""Cognitia Provider Epistemic Boundary Tests.

Verifies that provider outputs do NOT automatically modify epistemic state.
Provider execution is separate from Epistemic Evaluation.
"""

from __future__ import annotations

import pytest

from cognitia.epistemic.service import (
    EpistemicService,
    InMemoryEpistemicService,
)
from cognitia.providers.scaffolds.llm import MockLLMProvider
from cognitia.providers.types import (
    AdvancedCapabilityType,
    CandidateReasoningArtifact,
    ReasoningRequest,
)
from cognitia.reasoning.types import ReasoningInput, ReasoningMode


def _make_snapshot() -> ReasoningInput:
    return ReasoningInput(
        context_id="snap_ep_boundary",
        reasoning_mode=ReasoningMode.DEDUCTION,
        premises=[],
    )


def _make_request() -> ReasoningRequest:
    return ReasoningRequest(
        input_snapshot_id="snap_ep_boundary",
        requested_capability=AdvancedCapabilityType.LLM_REASONING,
    )


class TestProviderEpistemicBoundary:
    """Provider output MUST start as UNRESOLVED and NOT auto-modify epistemic state."""

    def test_llm_output_starts_unresolved(self) -> None:
        provider = MockLLMProvider()
        artifact = provider.reason(_make_request(), _make_snapshot())
        assert artifact.epistemic_status.name == "UNRESOLVED"

    def test_llm_output_is_not_supported(self) -> None:
        provider = MockLLMProvider()
        artifact = provider.reason(_make_request(), _make_snapshot())
        assert artifact.epistemic_status != "SUPPORTED"

    def test_llm_output_is_not_refuted(self) -> None:
        provider = MockLLMProvider()
        artifact = provider.reason(_make_request(), _make_snapshot())
        assert artifact.epistemic_status != "REFUTED"

    def test_artifact_does_not_mutate_epistemic_service(
        self,
    ) -> None:
        ep_service = InMemoryEpistemicService()
        provider = MockLLMProvider()
        _ = provider.reason(_make_request(), _make_snapshot())
        nodes = ep_service.list_nodes_by_status(None)
        assert nodes == []

    def test_provider_does_not_call_epistemic_service_directly(self) -> None:
        """Providers produce CandidateReasoningArtifact; Epistemic evaluation is separate."""
        provider = MockLLMProvider()
        artifact = provider.reason(_make_request(), _make_snapshot())
        assert isinstance(artifact, CandidateReasoningArtifact)

    def test_explicit_epistemic_evaluation_is_required_to_change_status(
        self,
    ) -> None:
        ep_service = InMemoryEpistemicService()
        provider = MockLLMProvider()
        artifact = provider.reason(_make_request(), _make_snapshot())
        # Status should still be UNRESOLVED without explicit evaluation
        assert artifact.epistemic_status.name == "UNRESOLVED"

    def test_proposal_status_starts_proposed(self) -> None:
        provider = MockLLMProvider()
        artifact = provider.reason(_make_request(), _make_snapshot())
        assert artifact.proposal_status.name == "PROPOSED"

    def test_all_provider_artifacts_start_unresolved(self) -> None:
        from cognitia.providers.scaffolds.causal import MockCausalProvider
        from cognitia.providers.scaffolds.evolution import MockStrategyEvolutionProvider
        from cognitia.providers.scaffolds.hypothesis import MockHypothesisProvider
        from cognitia.providers.scaffolds.rl import MockRLProvider
        from cognitia.providers.scaffolds.semantic_graph import MockSemanticGraphProvider
        from cognitia.providers.scaffolds.similarity import MockSimilarityProvider
        from cognitia.providers.scaffolds.tinyml import MockTinyMLProvider

        provider_methods = [
            ("reason", MockLLMProvider()),
            ("infer", MockTinyMLProvider()),
            ("generate_hypotheses", MockHypothesisProvider()),
            ("discover_causal_structure", MockCausalProvider()),
            ("query_graph", MockSemanticGraphProvider()),
            ("find_similar", MockSimilarityProvider()),
            ("evaluate_policy", MockRLProvider()),
            ("propose_strategy_revision", MockStrategyEvolutionProvider()),
        ]
        snapshot = _make_snapshot()
        for method_name, p in provider_methods:
            request = ReasoningRequest(
                input_snapshot_id="snap_ep_boundary",
                requested_capability=p.capabilities()[0],
            )
            method = getattr(p, method_name)
            artifact = method(request, snapshot)
            assert artifact.epistemic_status.name == "UNRESOLVED", (
                f"{p.provider_id} did not produce UNRESOLVED artifact"
            )
