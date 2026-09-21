"""Tests for Cognitive Attention Epistemic Awareness.

Validates that Attention can prioritize items based on epistemic status
without reinterpreting epistemic status, conflating attention score with confidence,
or altering epistemic truths.
"""

import pytest

from cognitia.attention.engine import DeterministicAttentionEngine
from cognitia.attention.types import AttentionQuery, AttentionReason
from cognitia.context.types import CognitiveContext, ContextItem, RelevanceReason
from cognitia.epistemic.types import EpistemicStatus


def test_epistemic_status_influences_ranking_without_altering_state() -> None:
    """Targeting specific epistemic statuses boosts attention priority while preserving original epistemic status."""
    items = (
        ContextItem(
            item_id="hyp_supported",
            item_type="Hypothesis",
            relevance_reason=RelevanceReason.EXPLICIT_QUERY,
            relevance_score=0.8,
            epistemic_status=EpistemicStatus.SUPPORTED,
        ),
        ContextItem(
            item_id="hyp_refuted",
            item_type="Hypothesis",
            relevance_reason=RelevanceReason.EXPLICIT_QUERY,
            relevance_score=0.8,
            epistemic_status=EpistemicStatus.REFUTED,
        ),
    )
    context = CognitiveContext(
        reference_observation_id="ref_obs",
        context_items=items,
    )

    engine = DeterministicAttentionEngine()

    # Query targeting REFUTED items (e.g. anomaly investigation)
    query_refuted = AttentionQuery(
        task_type="anomaly_investigation",
        target_epistemic_statuses=[EpistemicStatus.REFUTED],
    )
    res_refuted = engine.focus(context, query_refuted)

    assert len(res_refuted.attention_items) == 1
    assert res_refuted.attention_items[0].item_id == "hyp_refuted"
    assert res_refuted.attention_items[0].epistemic_status == EpistemicStatus.REFUTED
    assert AttentionReason.EPISTEMIC_RELEVANCE in res_refuted.attention_items[0].selection_reasons


def test_attention_score_is_not_epistemic_confidence() -> None:
    """An item with high attention score must retain its epistemic status without conflation."""
    item = ContextItem(
        item_id="unresolved_anomaly",
        item_type="Residual",
        relevance_reason=RelevanceReason.REFERENCE_OBSERVATION,
        relevance_score=1.0,
        epistemic_status=EpistemicStatus.UNRESOLVED,
    )
    context = CognitiveContext(
        reference_observation_id="unresolved_anomaly",
        context_items=(item,),
    )

    engine = DeterministicAttentionEngine()
    result = engine.focus(context, AttentionQuery(task_type="anomaly_investigation"))

    att_item = result.attention_items[0]
    # Attention score is high because it is the reference observation and matches anomaly investigation
    assert att_item.attention_score >= 0.70
    # But epistemic status remains UNRESOLVED, not SUPPORTED or TRUE
    assert att_item.epistemic_status == EpistemicStatus.UNRESOLVED
