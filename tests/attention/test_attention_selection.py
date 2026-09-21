"""Tests for Cognitive Attention Selection and Budgeting.

Validates budget limiting, filtering, task-driven selection, and score thresholds.
"""

import pytest

from cognitia.attention.engine import DeterministicAttentionEngine
from cognitia.attention.types import (
    AttentionQuery,
    AttentionReason,
)
from cognitia.context.types import CognitiveContext, ContextItem, RelevanceReason
from cognitia.epistemic.types import EpistemicStatus


def test_basic_selection_budget_limiting() -> None:
    """Context has 10 items. Query requests maximum_items = 3. Verify exactly 3 are selected."""
    items = []
    for i in range(10):
        items.append(
            ContextItem(
                item_id=f"item_{i:02d}",
                item_type="Observation",
                relevance_reason=RelevanceReason.TEMPORAL_MATCH if i > 0 else RelevanceReason.REFERENCE_OBSERVATION,
                relevance_score=1.0 - (i * 0.05),
            )
        )

    context = CognitiveContext(
        reference_observation_id="item_00",
        context_items=tuple(items),
    )

    engine = DeterministicAttentionEngine()
    result = engine.focus(context, AttentionQuery(maximum_items=3))

    assert len(result.attention_items) == 3
    assert len(result.selected_item_ids) == 3
    assert result.budget_limit == 3
    assert [item.rank for item in result.attention_items] == [1, 2, 3]


def test_selection_fewer_than_budget() -> None:
    """If fewer items exist in context than requested maximum, return all eligible items."""
    items = (
        ContextItem(
            item_id="item_01",
            item_type="Observation",
            relevance_reason=RelevanceReason.REFERENCE_OBSERVATION,
            relevance_score=1.0,
        ),
        ContextItem(
            item_id="item_02",
            item_type="CognitiveRule",
            relevance_reason=RelevanceReason.RULE_MATCH,
            relevance_score=0.9,
        ),
    )
    context = CognitiveContext(
        reference_observation_id="item_01",
        context_items=items,
    )

    engine = DeterministicAttentionEngine()
    result = engine.focus(context, AttentionQuery(maximum_items=10))

    assert len(result.attention_items) == 2
    assert result.selected_item_ids == ("item_01", "item_02")


def test_minimum_score_threshold_filtering() -> None:
    """Items below minimum_score are excluded prior to budget capping."""
    items = (
        ContextItem(
            item_id="high_score",
            item_type="Observation",
            relevance_reason=RelevanceReason.REFERENCE_OBSERVATION,
            relevance_score=1.0,
        ),
        ContextItem(
            item_id="low_score",
            item_type="Observation",
            relevance_reason=RelevanceReason.TEMPORAL_MATCH,
            relevance_score=0.1,
        ),
    )
    context = CognitiveContext(
        reference_observation_id="high_score",
        context_items=items,
    )

    engine = DeterministicAttentionEngine()
    result = engine.focus(context, AttentionQuery(minimum_score=0.70))

    assert len(result.attention_items) == 1
    assert result.attention_items[0].item_id == "high_score"


def test_requested_item_types_filtering() -> None:
    """Filter context items to requested types only."""
    items = (
        ContextItem(
            item_id="obs_1",
            item_type="Observation",
            relevance_reason=RelevanceReason.REFERENCE_OBSERVATION,
            relevance_score=1.0,
        ),
        ContextItem(
            item_id="rule_1",
            item_type="CognitiveRule",
            relevance_reason=RelevanceReason.RULE_MATCH,
            relevance_score=0.95,
        ),
        ContextItem(
            item_id="exp_1",
            item_type="ExperienceRecord",
            relevance_reason=RelevanceReason.MEMORY_MATCH,
            relevance_score=0.90,
        ),
    )
    context = CognitiveContext(
        reference_observation_id="obs_1",
        context_items=items,
    )

    engine = DeterministicAttentionEngine()
    query = AttentionQuery(requested_item_types=["CognitiveRule"])
    result = engine.focus(context, query)

    assert len(result.attention_items) == 1
    assert result.attention_items[0].item_id == "rule_1"


def test_task_dependent_selection_divergence() -> None:
    """Different tasks select and rank different items from the same context."""
    items = (
        ContextItem(
            item_id="obs_ref",
            item_type="Observation",
            relevance_reason=RelevanceReason.REFERENCE_OBSERVATION,
            relevance_score=0.8,
        ),
        ContextItem(
            item_id="rule_audit",
            item_type="CognitiveRule",
            relevance_reason=RelevanceReason.RULE_MATCH,
            relevance_score=0.8,
        ),
        ContextItem(
            item_id="exp_past",
            item_type="ExperienceRecord",
            relevance_reason=RelevanceReason.MEMORY_MATCH,
            relevance_score=0.8,
        ),
        ContextItem(
            item_id="residual_anomaly",
            item_type="Residual",
            relevance_reason=RelevanceReason.EXPLICIT_QUERY,
            relevance_score=0.8,
            epistemic_status=EpistemicStatus.REFUTED,
        ),
    )
    context = CognitiveContext(
        reference_observation_id="obs_ref",
        context_items=items,
    )

    engine = DeterministicAttentionEngine()

    # Task A: Rule evaluation
    res_rules = engine.focus(context, AttentionQuery(task_type="rule_evaluation", maximum_items=1))
    assert res_rules.attention_items[0].item_id == "rule_audit"

    # Task B: Anomaly investigation
    res_anomaly = engine.focus(context, AttentionQuery(task_type="anomaly_investigation", maximum_items=1))
    assert res_anomaly.attention_items[0].item_id == "residual_anomaly"

    # Task C: Memory retrieval
    res_memory = engine.focus(context, AttentionQuery(task_type="memory_retrieval", maximum_items=1))
    assert res_memory.attention_items[0].item_id == "exp_past"


def test_end_to_end_observation_context_attention() -> None:
    """Proves the entire pipeline Observation -> Persistence -> Memory -> Context -> Attention works cleanly."""
    from cognitia.abi.types import Observation
    from cognitia.runtime.local import LocalCognitiveRuntime

    runtime = LocalCognitiveRuntime()

    # 1. New Observation
    obs = Observation(
        source_id="domain:sensor:alpha",
        payload={"value": 42.0},
        created_at="2026-09-21T12:00:00Z",
    )
    runtime.persistence.save_object(obs)

    # 2. Context Assembly
    context = runtime.assemble_context(obs)
    assert context.reference_observation_id == obs.id

    # 3. Attention Focus
    attention = runtime.focus_context(context, AttentionQuery(maximum_items=5))
    assert attention.reference_observation_id == obs.id
    assert obs.id in attention.selected_item_ids
