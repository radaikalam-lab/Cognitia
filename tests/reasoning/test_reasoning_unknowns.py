"""Tests for Explicit Unknowns and Residuals in reasoning."""

import pytest

from cognitia.abi.types import Observation
from cognitia.reasoning import (
    DeterministicReasoningEngine,
    ReasoningInput,
    ReasoningMode,
    ReasoningResidual,
)
from cognitia.rules.types import CognitiveRule


def test_missing_facts_explicitly_reported_as_residuals():
    """Verify that absent variables in deduction and abduction yield explicit residuals."""
    engine = DeterministicReasoningEngine()
    rule = CognitiveRule(
        rule_id="r_multi",
        name="Multi Variable Rule",
        predicate={"rpm": 3000, "ambient_temp": 25.0, "oil_viscosity": "SAE_5W30"},
        recommendation={"lubrication_state": "OPTIMAL"},
    )
    # Only rpm is provided
    obs = Observation(id="obs_single", payload={"rpm": 3000})

    inp = ReasoningInput(
        context_id="ctx_unknowns",
        reasoning_mode=ReasoningMode.DEDUCTION,
        premises=[obs],
        rules=[rule],
    )

    trace, result = engine.reason(inp)

    # 2 missing variables -> 2 explicit residuals
    assert len(result.residuals) == 2
    residual_names = {r.factor_name for r in result.residuals}
    assert residual_names == {"ambient_temp", "oil_viscosity"}
    for r in result.residuals:
        assert isinstance(r, ReasoningResidual)
        assert r.residual_type == "missing_observation"
