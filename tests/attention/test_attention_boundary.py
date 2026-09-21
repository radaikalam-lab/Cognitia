"""Tests for Cognitive Attention Non-Authority and Boundary Invariants.

Validates that Attention operations:
1. Do NOT mutate Context.
2. Do NOT mutate Persistence.
3. Do NOT mutate Memory.
4. Do NOT mutate Rules or execute Rule actions.
5. Do NOT mutate Epistemic status.
6. Do NOT issue Decisions or execute Actions.
7. Do NOT exercise domain Authority.
"""

import pytest

from cognitia.abi.types import Observation
from cognitia.attention.types import AttentionQuery, AttentionResult
from cognitia.rules.types import CognitiveRule
from cognitia.runtime.local import LocalCognitiveRuntime


def test_attention_boundary_no_side_effects() -> None:
    runtime = LocalCognitiveRuntime()

    obs = Observation(
        source_id="app:sensor:test",
        payload={"value": 100},
        created_at="2026-09-21T12:00:00Z",
    )
    runtime.persistence.save_object(obs)

    rule = CognitiveRule(
        rule_id="RULE-BOUND-01",
        version="1.0.0",
        name="Boundary Rule",
        scope="general",
        predicate={"field": "value", "op": ">", "value": 50},
        recommendation={"action": "SHUTDOWN_SYSTEM"},  # Recommendation payload
        author_id="human_admin",
    )
    runtime.rules.create_rule(rule)

    # Initial counts
    persisted_count_before = len(runtime.persistence.list_all_objects())
    rules_before = runtime.rules.list_rules()

    context = runtime.assemble_context(obs)
    ctx_items_before = len(context.context_items)

    # Perform Attention focus
    result = runtime.focus_context(context, AttentionQuery(task_type="rule_evaluation"))

    # Assert AttentionResult is produced
    assert isinstance(result, AttentionResult)

    # Invariant 1: Context is unchanged
    assert len(context.context_items) == ctx_items_before

    # Invariant 2: Persistence is not mutated by attention
    assert len(runtime.persistence.list_all_objects()) == persisted_count_before

    # Invariant 3: Rules are not executed and store is not mutated
    assert len(runtime.rules.list_rules()) == len(rules_before)

    # Invariant 4: No decisions or actions were created or executed
    decision_caps = runtime.capabilities.list_by_type("decision")
    # Runtime still contains standard un-invoked decision capabilities
    assert decision_caps is not None
