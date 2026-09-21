"""Tests for Counterfactual Reasoning strategy and unknown boundary."""

import pytest

from cognitia.abi.types import Observation
from cognitia.reasoning import (
    CounterfactualReasoner,
    CounterfactualScenario,
    ReasoningInput,
    ReasoningMode,
)
from cognitia.rules.types import CognitiveRule


def test_counterfactual_derivation_with_transition_rules():
    """Verify counterfactual scenario calculation under explicit intervention and transition rules."""
    baseline_obs = Observation(
        id="obs_baseline",
        payload={
            "coolant_flow_lpm": 20.0,
            "engine_load_pct": 80.0,
            "coolant_temp_c": 110.0,
        },
    )

    # Transition rule: if coolant_flow_lpm increased to 50, coolant_temp_c drops by 15 degrees
    transition_rule = CognitiveRule(
        rule_id="tr_coolant_flow",
        name="Coolant Flow Thermal Transition",
        scope="counterfactual",
        predicate={"coolant_flow_lpm": 50.0},
        recommendation={"target_variable": "coolant_temp_c", "delta": -15.0},
    )

    interventions = {"coolant_flow_lpm": 50.0}

    reasoner = CounterfactualReasoner()
    inp = ReasoningInput(
        context_id="ctx_thermal",
        reasoning_mode=ReasoningMode.COUNTERFACTUAL,
        premises=[baseline_obs],
        rules=[transition_rule],
        hypothetical_interventions=interventions,
    )

    trace, result = reasoner.reason(inp)

    assert trace.mode == ReasoningMode.COUNTERFACTUAL
    assert isinstance(trace.conclusion, CounterfactualScenario)
    scenario = trace.conclusion

    assert scenario.is_observed is False  # Invariant: Counterfactual != Observation
    assert scenario.is_hypothetical is True
    assert scenario.intervention_dict["coolant_flow_lpm"] == 50.0
    assert scenario.derived_state_dict["coolant_flow_lpm"] == 50.0
    assert scenario.derived_state_dict["coolant_temp_c"] == 95.0  # 110 - 15
    assert len(scenario.derivation_steps) >= 2


def test_counterfactual_unknown_boundary_records_residual():
    """Verify missing transition rule for requested downstream target produces residual without extrapolating."""
    baseline_obs = Observation(
        id="obs_baseline",
        payload={"inlet_pressure": 1.0, "chamber_volume": 2.0},
    )

    interventions = {"inlet_pressure": 3.0}

    # Request downstream variable 'exhaust_temperature' for which NO transition rule exists
    constraints = {"requested_downstream_variables": ["exhaust_temperature"]}

    reasoner = CounterfactualReasoner()
    inp = ReasoningInput(
        context_id="ctx_pressure",
        reasoning_mode=ReasoningMode.COUNTERFACTUAL,
        premises=[baseline_obs],
        rules=[],  # No transition rules
        hypothetical_interventions=interventions,
        constraints=constraints,
    )

    trace, result = reasoner.reason(inp)

    assert isinstance(trace.conclusion, CounterfactualScenario)
    assert "exhaust_temperature" not in trace.conclusion.derived_state_dict
    assert len(trace.conclusion.residuals) == 1
    residual = trace.conclusion.residuals[0]
    assert residual.factor_name == "exhaust_temperature"
    assert residual.residual_type == "missing_rule"
    assert "transition rule unavailable" in residual.description.lower()
