"""Tests for Cognitive Context Determinism and Consistent Item Ordering."""

import pytest

from cognitia.abi.types import Observation
from cognitia.context.types import ContextQuery
from cognitia.rules.types import CognitiveRule
from cognitia.runtime.local import LocalCognitiveRuntime


def test_context_assembly_determinism() -> None:
    runtime = LocalCognitiveRuntime()

    # Create several observations and rules
    for i in range(10):
        obs = Observation(
            source_id=f"sensor_{i % 3}",
            payload={"reading": i * 1.5},
            created_at=f"2026-09-21T10:0{i}:00Z",
            metadata={"subject_id": "SYS-01", "scope": "monitoring"},
        )
        runtime.persistence.save_object(obs)

    rule1 = CognitiveRule(rule_id="R-A", version="1.0.0", scope="monitoring", confidence=0.9)
    rule2 = CognitiveRule(rule_id="R-B", version="1.0.0", scope="monitoring", confidence=0.8)
    rule3 = CognitiveRule(rule_id="R-C", version="1.0.0", scope="monitoring", confidence=0.95)
    runtime.rules.create_rule(rule1)
    runtime.rules.create_rule(rule2)
    runtime.rules.create_rule(rule3)

    ref_obs = Observation(
        source_id="sensor_0",
        payload={"reading": 5.0},
        created_at="2026-09-21T10:05:00Z",
        metadata={"subject_id": "SYS-01", "scope": "monitoring"},
    )
    runtime.persistence.save_object(ref_obs)

    query = ContextQuery(temporal_window_seconds_before=1000.0, temporal_window_seconds_after=1000.0)

    # Assemble context 5 times independently
    contexts = [runtime.assemble_context(ref_obs, query=query) for _ in range(5)]

    first_item_ids = [item.item_id for item in contexts[0].context_items]
    first_rule_ids = contexts[0].active_rule_ids
    first_obs_ids = contexts[0].related_observation_ids

    for ctx in contexts[1:]:
        assert [item.item_id for item in ctx.context_items] == first_item_ids
        assert ctx.active_rule_ids == first_rule_ids
        assert ctx.related_observation_ids == first_obs_ids
