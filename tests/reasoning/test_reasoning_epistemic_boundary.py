"""Tests for Epistemic Boundary separation."""

import pytest

from cognitia.abi.types import Observation
from cognitia.epistemic.service import InMemoryEpistemicService
from cognitia.epistemic.types import EpistemicStatus
from cognitia.reasoning import (
    DeterministicReasoningEngine,
    ReasoningInput,
    ReasoningMode,
)
from cognitia.rules.types import CognitiveRule


def test_reasoning_does_not_mutate_epistemic_service_automatically():
    """Verify that executing reasoning produces candidate results without auto-mutating EpistemicService."""
    ep_service = InMemoryEpistemicService()
    obs = Observation(id="obs_ep_1", payload={"temp": 120})
    ep_node = ep_service.record_observation(obs)
    assert ep_node.status == EpistemicStatus.OBSERVED

    rule = CognitiveRule(
        rule_id="r_overheat",
        name="Overheat Explanation",
        scope="abductive",
        predicate={"temp": 120},
        recommendation={"hypothesis": "Thermal Overload Event"},
    )

    engine = DeterministicReasoningEngine()
    inp = ReasoningInput(
        context_id="ctx_ep",
        reasoning_mode=ReasoningMode.ABDUCTION,
        premises=[obs],
        rules=[rule],
    )

    trace, result = engine.reason(inp)

    # Invariant: Epistemic service store remains untouched by reasoner
    assert len(ep_service.list_nodes_by_status(EpistemicStatus.HYPOTHESIS)) == 0

    # Explicit downstream registration
    assert len(result.candidate_hypotheses) == 1
    candidate_hyp = result.candidate_hypotheses[0]
    registered_node = ep_service.register_hypothesis(candidate_hyp)
    assert registered_node.status == EpistemicStatus.HYPOTHESIS
    assert len(ep_service.list_nodes_by_status(EpistemicStatus.HYPOTHESIS)) == 1
