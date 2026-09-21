"""Tests for Reasoning Provenance and Lineage DAG traversal."""

import pytest

from cognitia.abi.types import Observation
from cognitia.provenance.record import LineageChain, ProvenanceRecord, SourceType
from cognitia.reasoning import (
    DeterministicReasoningEngine,
    ReasoningInput,
    ReasoningMode,
)
from cognitia.rules.types import CognitiveRule


def test_reasoning_trace_provenance_lineage():
    """Verify that ReasoningTrace and ReasoningResult establish complete parent provenance DAG."""
    obs_prov = ProvenanceRecord(id="prov_obs", source_type=SourceType.SENSOR)
    obs = Observation(id="obs_root", source_id="sensor_rpm", payload={"rpm": 3500})

    rule = CognitiveRule(
        rule_id="r_prov",
        name="RPM Rule",
        predicate={"rpm": {">": 3000}},
        recommendation={"state": "FAST"},
    )

    engine = DeterministicReasoningEngine()
    inp = ReasoningInput(
        context_id="ctx_prov_1",
        attention_result_id="att_prov_1",
        selected_item_ids=["obs_root"],
        reasoning_mode=ReasoningMode.DEDUCTION,
        premises=[obs],
        rules=[rule],
    )

    trace, result = engine.reason(inp)

    # Lineage registration
    chain = LineageChain()
    chain.add_record(obs_prov)
    chain.add_record(inp.provenance)
    chain.add_record(trace.provenance)
    chain.add_record(result.provenance)

    assert trace.provenance.source_type == SourceType.REASONING_ENGINE
    assert inp.provenance.id in trace.provenance.parent_ids
    assert "obs_root" in trace.provenance.parent_ids
    assert rule.id in trace.provenance.parent_ids

    ancestors = chain.get_ancestors(trace.provenance.id)
    ancestor_ids = {a.id for a in ancestors}
    assert inp.provenance.id in ancestor_ids
