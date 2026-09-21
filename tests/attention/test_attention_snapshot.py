"""Tests for Cognitive Attention Snapshot Immutability.

Validates that AttentionResult objects remain immutable and unaffected
by subsequent changes to persistence, memory, rules, or newly assembled contexts.
"""

import pytest

from cognitia.abi.types import Observation
from cognitia.attention.types import AttentionQuery
from cognitia.experience.record import ExperienceBuilder
from cognitia.rules.types import CognitiveRule
from cognitia.runtime.local import LocalCognitiveRuntime


def test_attention_snapshot_isolation() -> None:
    """Modifying underlying runtime stores does NOT mutate a previously produced AttentionResult."""
    runtime = LocalCognitiveRuntime()

    # Create initial observation and rule
    obs1 = Observation(
        source_id="app:sensor:1",
        payload={"temperature": 25.0},
        created_at="2026-09-21T10:00:00Z",
    )
    runtime.persistence.save_object(obs1)

    rule1 = CognitiveRule(
        rule_id="RULE-TEMP-01",
        version="1.0.0",
        name="Temp Rule",
        scope="general",
        predicate={"field": "temperature", "op": ">", "value": 20.0},
        author_id="human_operator",
    )
    runtime.rules.create_rule(rule1)

    # Assemble Context C1 and Focus Attention A1
    ctx1 = runtime.assemble_context(obs1)
    att1 = runtime.focus_context(ctx1, AttentionQuery(task_id="t1", maximum_items=5))

    initial_item_ids = att1.selected_item_ids
    initial_items_count = len(att1.attention_items)
    initial_scores = [item.attention_score for item in att1.attention_items]

    # Mutate persistence with new observations and experiences at T2
    obs2 = Observation(
        source_id="app:sensor:2",
        payload={"temperature": 99.0},
        created_at="2026-09-21T10:05:00Z",
    )
    runtime.persistence.save_object(obs2)

    exp2 = (
        ExperienceBuilder(source_application="app", episode_id="EP-02")
        .with_observation(obs2)
        .build()
    )
    runtime.persistence.save_object(exp2)

    # Add new rule
    rule2 = CognitiveRule(
        rule_id="RULE-OVERHEAT",
        version="1.0.0",
        name="Overheat Rule",
        scope="general",
        predicate={"field": "temperature", "op": ">", "value": 50.0},
        author_id="human_operator",
    )
    runtime.rules.create_rule(rule2)

    # Assemble new Context C2 and Attention A2
    ctx2 = runtime.assemble_context(obs2)
    att2 = runtime.focus_context(ctx2, AttentionQuery(task_id="t2", maximum_items=5))

    # Verify A1 is completely unchanged
    assert att1.selected_item_ids == initial_item_ids
    assert len(att1.attention_items) == initial_items_count
    assert [item.attention_score for item in att1.attention_items] == initial_scores
    assert att1.task_id == "t1"
    assert "RULE-OVERHEAT" not in att1.selected_item_ids

    # Verify A2 has new items
    assert att2.task_id == "t2"
    assert att2.reference_observation_id == obs2.id
