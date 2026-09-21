"""Tests for Cognitive Context Snapshot Semantics and Historical Independence."""

import pytest

from cognitia.abi.types import Observation
from cognitia.context.types import CognitiveContext
from cognitia.rules.types import CognitiveRule
from cognitia.runtime.local import LocalCognitiveRuntime


def test_context_snapshot_immutability_across_state_mutations() -> None:
    runtime = LocalCognitiveRuntime()

    # T1: Initial state with one rule and one reference observation
    r1 = CognitiveRule(
        rule_id="R-SNAP-01",
        version="1.0.0",
        scope="diagnostics",
        predicate={"field": "voltage", "op": ">", "value": 100},
    )
    runtime.rules.create_rule(r1)

    obs1 = Observation(
        source_id="meter_alpha",
        payload={"voltage": 120},
        created_at="2026-09-21T10:00:00Z",
        metadata={"subject_id": "SYS-T1", "scope": "diagnostics"},
    )
    runtime.persistence.save_object(obs1)

    # Assemble Context C1 at T1
    c1 = runtime.assemble_context(obs1)
    assert isinstance(c1, CognitiveContext)
    assert c1.reference_observation_id == obs1.id
    assert "R-SNAP-01" in c1.active_rule_ids
    assert len(c1.related_observation_ids) == 0

    c1_rule_ids = c1.active_rule_ids
    c1_items_count = len(c1.context_items)

    # T2: State mutation in underlying stores
    # 1. Supersede rule R-SNAP-01 with V2 (stricter threshold not matching voltage=120)
    r2 = CognitiveRule(
        rule_id="R-SNAP-01",
        version="2.0.0",
        scope="diagnostics",
        predicate={"field": "voltage", "op": ">", "value": 200},
    )
    runtime.rules.supersede_rule("R-SNAP-01", r2, rationale="Updated threshold")

    # 2. Add new observation in temporal neighborhood (30s after)
    obs2 = Observation(
        source_id="meter_beta",
        payload={"voltage": 130},
        created_at="2026-09-21T10:00:30Z",
        metadata={"subject_id": "SYS-T1", "scope": "diagnostics"},
    )
    runtime.persistence.save_object(obs2)

    # CRITICAL INVARIANT: C1 snapshot MUST remain unchanged
    assert c1.active_rule_ids == c1_rule_ids
    assert len(c1.context_items) == c1_items_count
    assert len(c1.related_observation_ids) == 0

    # Assembling at T2 produces a new snapshot C2 reflecting T2 state
    c2 = runtime.assemble_context(obs1)
    assert c2.id != c1.id
    # Rule R-SNAP-01 v2 threshold=200 does not match voltage=120, so active_rule_ids is empty in C2
    assert "R-SNAP-01" not in c2.active_rule_ids
    # C2 now includes obs2 in temporal context
    assert obs2.id in c2.temporal_context.succeeding_observation_ids
    assert obs2.id in c2.related_observation_ids
