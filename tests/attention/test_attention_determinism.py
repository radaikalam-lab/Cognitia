"""Tests for Cognitive Attention Determinism and Stable Tie-Breaking.

Validates that attention selection produces 100% reproducible results and strictly
ordered tie-breaking (score DESC, timestamp DESC, item_id ASC).
"""

import pytest

from cognitia.abi.types import DeterministicSerializer
from cognitia.attention.engine import DeterministicAttentionEngine
from cognitia.attention.types import AttentionQuery
from cognitia.context.types import CognitiveContext, ContextItem, RelevanceReason, TemporalContext


def test_attention_determinism_identical_runs() -> None:
    """Same context + same query produces identical rankings, scores, and selection order."""
    items = (
        ContextItem(
            item_id="obs_001",
            item_type="Observation",
            relevance_reason=RelevanceReason.REFERENCE_OBSERVATION,
            relevance_score=1.0,
        ),
        ContextItem(
            item_id="rule_001",
            item_type="CognitiveRule",
            relevance_reason=RelevanceReason.RULE_MATCH,
            relevance_score=0.9,
        ),
        ContextItem(
            item_id="exp_001",
            item_type="ExperienceRecord",
            relevance_reason=RelevanceReason.MEMORY_MATCH,
            relevance_score=0.8,
        ),
    )
    context = CognitiveContext(
        reference_observation_id="obs_001",
        context_items=items,
    )

    query = AttentionQuery(task_id="det_task", task_type="general_focus", maximum_items=3)
    engine = DeterministicAttentionEngine()

    result1 = engine.focus(context, query)
    result2 = engine.focus(context, query)

    assert result1.selected_item_ids == result2.selected_item_ids
    assert len(result1.attention_items) == len(result2.attention_items)
    for it1, it2 in zip(result1.attention_items, result2.attention_items):
        assert it1.item_id == it2.item_id
        assert it1.rank == it2.rank
        assert it1.attention_score == it2.attention_score
        assert it1.selection_reasons == it2.selection_reasons


def test_attention_stable_tie_breaking_order() -> None:
    """When attention scores are identical, items are tie-broken by time delta / timestamp DESC, then item_id ASC."""
    # Create 4 items with identical relevance scores and types
    items = (
        ContextItem(
            item_id="item_Z",
            item_type="Observation",
            relevance_reason=RelevanceReason.TEMPORAL_MATCH,
            relevance_score=0.7,
        ),
        ContextItem(
            item_id="item_A",
            item_type="Observation",
            relevance_reason=RelevanceReason.TEMPORAL_MATCH,
            relevance_score=0.7,
        ),
        ContextItem(
            item_id="item_M",
            item_type="Observation",
            relevance_reason=RelevanceReason.TEMPORAL_MATCH,
            relevance_score=0.7,
        ),
        ContextItem(
            item_id="item_B",
            item_type="Observation",
            relevance_reason=RelevanceReason.TEMPORAL_MATCH,
            relevance_score=0.7,
        ),
    )

    # All have the same temporal delta = 0.0
    temporal_ctx = TemporalContext(
        reference_timestamp="2026-09-21T12:00:00Z",
        time_deltas=(("item_A", 0.0), ("item_B", 0.0), ("item_M", 0.0), ("item_Z", 0.0)),
    )

    context = CognitiveContext(
        reference_observation_id="ref_obs",
        temporal_context=temporal_ctx,
        context_items=items,
    )

    engine = DeterministicAttentionEngine()
    result = engine.focus(context, AttentionQuery(maximum_items=10))

    # All have identical attention scores and time deltas, so item_id ASC decides order
    selected_ids = result.selected_item_ids
    assert selected_ids == ("item_A", "item_B", "item_M", "item_Z")


def test_attention_temporal_tie_breaking() -> None:
    """When attention scores are identical, items with higher temporal proximity (closer time_delta) rank higher."""
    items = (
        ContextItem(
            item_id="item_past_distant",
            item_type="Observation",
            relevance_reason=RelevanceReason.TEMPORAL_MATCH,
            relevance_score=0.7,
        ),
        ContextItem(
            item_id="item_past_recent",
            item_type="Observation",
            relevance_reason=RelevanceReason.TEMPORAL_MATCH,
            relevance_score=0.7,
        ),
    )

    temporal_ctx = TemporalContext(
        reference_timestamp="2026-09-21T12:00:00Z",
        time_deltas=(("item_past_distant", -3600.0), ("item_past_recent", -60.0)),
    )

    context = CognitiveContext(
        reference_observation_id="ref_obs",
        temporal_context=temporal_ctx,
        context_items=items,
    )

    engine = DeterministicAttentionEngine()
    result = engine.focus(context, AttentionQuery(maximum_items=2))

    # -60.0 > -3600.0, so item_past_recent should rank higher
    assert result.selected_item_ids[0] == "item_past_recent"
    assert result.selected_item_ids[1] == "item_past_distant"
