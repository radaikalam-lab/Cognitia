"""Tests for 100-run Determinism across all five reasoning modes."""

import pytest

from cognitia.abi.types import Observation
from cognitia.reasoning import (
    DeterministicReasoningEngine,
    ReasoningInput,
    ReasoningMode,
)
from cognitia.rules.types import CognitiveRule


def test_deduction_100_runs_determinism():
    """Verify 100 consecutive executions of identical deductive reasoning input yield identical traces."""
    engine = DeterministicReasoningEngine()
    rule = CognitiveRule(
        rule_id="r_det",
        name="Deterministic Rule",
        predicate={"val": {">": 10}},
        recommendation={"status": "HIGH"},
    )
    obs = Observation(id="obs_det", payload={"val": 20})
    inp = ReasoningInput(
        context_id="ctx_det",
        reasoning_mode=ReasoningMode.DEDUCTION,
        premises=[obs],
        rules=[rule],
    )

    baseline_trace, baseline_result = engine.reason(inp)
    baseline_steps = [(s.step_number, s.inference_rule, s.intermediate_claim) for s in baseline_trace.steps]
    baseline_claims = [c.statement for c in baseline_result.candidate_claims]

    for _ in range(100):
        trace, result = engine.reason(inp)
        steps = [(s.step_number, s.inference_rule, s.intermediate_claim) for s in trace.steps]
        claims = [c.statement for c in result.candidate_claims]

        assert steps == baseline_steps
        assert claims == baseline_claims
        assert trace.mode == baseline_trace.mode
        assert trace.confidence == baseline_trace.confidence


def test_abduction_100_runs_determinism():
    """Verify 100 consecutive executions of identical abductive reasoning input yield identical ranked hypotheses."""
    engine = DeterministicReasoningEngine()
    rule1 = CognitiveRule(
        rule_id="r1",
        name="Hypothesis 1",
        scope="abductive",
        predicate={"temp": 100},
        recommendation={"hypothesis": "Thermal Surge"},
    )
    rule2 = CognitiveRule(
        rule_id="r2",
        name="Hypothesis 2",
        scope="abductive",
        predicate={"temp": 100, "flow": "low"},
        recommendation={"hypothesis": "Pump Failure"},
    )
    obs = Observation(id="obs_abd", payload={"temp": 100, "flow": "low"})
    inp = ReasoningInput(
        context_id="ctx_abd",
        reasoning_mode=ReasoningMode.ABDUCTION,
        premises=[obs],
        rules=[rule1, rule2],
    )

    baseline_trace, baseline_result = engine.reason(inp)
    baseline_hyp_statements = [h.statement for h in baseline_result.candidate_hypotheses]

    for _ in range(100):
        trace, result = engine.reason(inp)
        hyp_statements = [h.statement for h in result.candidate_hypotheses]
        assert hyp_statements == baseline_hyp_statements


def test_analogy_100_runs_determinism():
    """Verify 100 consecutive executions of identical analogical reasoning input yield identical mappings."""
    engine = DeterministicReasoningEngine()
    source_pattern = {
        "source_id": "filter_a",
        "elements": {"f": "freq", "a": "amp", "g": "gain"},
    }
    obs = Observation(id="obs_ana", payload={"f": 100, "a": 10, "g": 2})
    inp = ReasoningInput(
        context_id="ctx_ana",
        reasoning_mode=ReasoningMode.ANALOGY,
        premises=[obs],
        analogy_source=source_pattern,
    )

    baseline_trace, baseline_result = engine.reason(inp)
    baseline_corrs = baseline_trace.conclusion.correspondences

    for _ in range(100):
        trace, result = engine.reason(inp)
        assert trace.conclusion.correspondences == baseline_corrs


def test_causal_100_runs_determinism():
    """Verify 100 consecutive executions of identical causal reasoning input yield identical hypotheses."""
    engine = DeterministicReasoningEngine()
    obs = Observation(id="obs_caus", payload={"v": 12, "i": 2})
    inp = ReasoningInput(
        context_id="ctx_caus",
        reasoning_mode=ReasoningMode.CAUSAL,
        premises=[obs],
        causal_graph=[("v", "i", "ohms_law")],
    )

    baseline_trace, baseline_result = engine.reason(inp)
    baseline_cause = baseline_trace.conclusion.cause
    baseline_effect = baseline_trace.conclusion.effect

    for _ in range(100):
        trace, result = engine.reason(inp)
        assert trace.conclusion.cause == baseline_cause
        assert trace.conclusion.effect == baseline_effect


def test_counterfactual_100_runs_determinism():
    """Verify 100 consecutive executions of identical counterfactual reasoning input yield identical derived state."""
    engine = DeterministicReasoningEngine()
    obs = Observation(id="obs_cf", payload={"speed": 60, "gear": 4})
    inp = ReasoningInput(
        context_id="ctx_cf",
        reasoning_mode=ReasoningMode.COUNTERFACTUAL,
        premises=[obs],
        hypothetical_interventions={"speed": 100},
    )

    baseline_trace, baseline_result = engine.reason(inp)
    baseline_derived = baseline_trace.conclusion.derived_state

    for _ in range(100):
        trace, result = engine.reason(inp)
        assert trace.conclusion.derived_state == baseline_derived
