"""Tests for Cognitive Attention Provenance and Lineage.

Validates that AttentionResult maintains auditable provenance links
back to the CognitiveContext and selected context items.
"""

import pytest

from cognitia.abi.types import Observation
from cognitia.attention.engine import DeterministicAttentionEngine
from cognitia.attention.types import AttentionQuery
from cognitia.context.types import CognitiveContext, ContextItem, RelevanceReason
from cognitia.provenance.record import LineageChain, SourceType


def test_attention_provenance_records() -> None:
    obs = Observation(source_id="app:sensor:1", payload={"temp": 20.0})
    ctx_item1 = ContextItem(
        item_id=obs.id,
        item_type="Observation",
        relevance_reason=RelevanceReason.REFERENCE_OBSERVATION,
        relevance_score=1.0,
    )
    ctx_item2 = ContextItem(
        item_id="obs_related",
        item_type="Observation",
        relevance_reason=RelevanceReason.TEMPORAL_MATCH,
        relevance_score=0.8,
    )

    context = CognitiveContext(
        reference_observation_id=obs.id,
        context_items=(ctx_item1, ctx_item2),
    )

    engine = DeterministicAttentionEngine()
    result = engine.focus(context, AttentionQuery(maximum_items=2))

    prov = result.provenance
    assert prov.source_type == SourceType.COMPOSITE
    assert prov.producer_id == "deterministic_attention_engine"
    assert prov.is_deterministic is True
    assert context.id in prov.parent_ids
    assert obs.id in prov.parent_ids
    assert "obs_related" in prov.parent_ids


def test_attention_lineage_resolution() -> None:
    """LineageChain can resolve ancestry from Attention back to Context."""
    obs = Observation(source_id="app:test", payload={"x": 1})
    ctx_item = ContextItem(
        item_id=obs.id,
        item_type="Observation",
        relevance_reason=RelevanceReason.REFERENCE_OBSERVATION,
        relevance_score=1.0,
    )
    context = CognitiveContext(
        reference_observation_id=obs.id,
        context_items=(ctx_item,),
    )

    engine = DeterministicAttentionEngine()
    result = engine.focus(context, AttentionQuery(maximum_items=1))

    chain = LineageChain()
    chain.add_record(context.provenance)
    chain.add_record(result.provenance)

    ancestors = chain.get_ancestors(result.provenance.id)
    ancestor_ids = [a.id for a in ancestors]
    assert context.provenance.id in ancestor_ids
