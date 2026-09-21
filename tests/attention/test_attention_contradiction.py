"""Tests for Cognitive Attention Contradiction Preservation.

Validates that Attention preserves epistemic tension and does not silently
suppress or discard contradictory evidence (SUPPORT vs REFUTE).
"""

import pytest

from cognitia.attention.engine import DeterministicAttentionEngine
from cognitia.attention.types import AttentionQuery
from cognitia.context.types import CognitiveContext, ContextItem, RelevanceReason
from cognitia.epistemic.types import EpistemicStatus


def test_attention_preserves_contradictory_evidence() -> None:
    """When context contains mutually contradictory evidence (SUPPORT and REFUTE),
    Attention must preserve both items and not eliminate one in favor of the other.
    """
    evidence_support = ContextItem(
        item_id="ev_support_claim",
        item_type="Evidence",
        relevance_reason=RelevanceReason.EXPLICIT_QUERY,
        relevance_score=0.85,
        epistemic_status=EpistemicStatus.SUPPORTED,
    )
    evidence_refute = ContextItem(
        item_id="ev_refute_claim",
        item_type="Evidence",
        relevance_reason=RelevanceReason.EXPLICIT_QUERY,
        relevance_score=0.85,
        epistemic_status=EpistemicStatus.REFUTED,
    )

    context = CognitiveContext(
        reference_observation_id="ref_obs_001",
        context_items=(evidence_support, evidence_refute),
    )

    engine = DeterministicAttentionEngine()
    query = AttentionQuery(
        task_id="audit_claim_controversy",
        task_type="epistemic_audit",
        maximum_items=5,
    )
    result = engine.focus(context, query)

    # Both items must be present in the attention result
    selected_ids = result.selected_item_ids
    assert "ev_support_claim" in selected_ids
    assert "ev_refute_claim" in selected_ids

    # Verify both statuses remain intact
    item_sup = result.get_item("ev_support_claim")
    item_ref = result.get_item("ev_refute_claim")
    assert item_sup is not None and item_sup.epistemic_status == EpistemicStatus.SUPPORTED
    assert item_ref is not None and item_ref.epistemic_status == EpistemicStatus.REFUTED
