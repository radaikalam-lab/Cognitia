"""Tests for Cognitive Context Contract, Types, and Immutability."""

import pytest

from cognitia.abi.types import Observation
from cognitia.context.types import (
    CognitiveContext,
    ContextItem,
    ContextQuery,
    RelevanceReason,
    TemporalContext,
)
from cognitia.provenance.record import SourceType


def test_context_types_and_relevance_reasons() -> None:
    reasons = [
        RelevanceReason.REFERENCE_OBSERVATION,
        RelevanceReason.SUBJECT_MATCH,
        RelevanceReason.EPISODE_MATCH,
        RelevanceReason.TEMPORAL_MATCH,
        RelevanceReason.RULE_MATCH,
        RelevanceReason.MEMORY_MATCH,
        RelevanceReason.EXPLICIT_QUERY,
        RelevanceReason.SOURCE_MATCH,
    ]
    assert len(reasons) == 8
    assert RelevanceReason.SUBJECT_MATCH.value == "subject_match"


def test_context_item_instantiation() -> None:
    item = ContextItem(
        item_id="obs-123",
        item_type="Observation",
        relevance_reason=RelevanceReason.SUBJECT_MATCH,
        relevance_score=0.9,
    )
    assert item.item_id == "obs-123"
    assert item.relevance_reason == RelevanceReason.SUBJECT_MATCH
    assert item.relevance_score == 0.9


def test_temporal_context_instantiation() -> None:
    temporal = TemporalContext(
        reference_timestamp="2026-09-21T10:00:00Z",
        window_seconds_before=300.0,
        window_seconds_after=60.0,
        preceding_observation_ids=("obs-1", "obs-2"),
        succeeding_observation_ids=("obs-3",),
        time_deltas=(("obs-1", -120.0), ("obs-2", -30.0), ("obs-3", 15.0)),
    )
    assert temporal.reference_timestamp == "2026-09-21T10:00:00Z"
    assert temporal.deltas_dict["obs-1"] == -120.0
    assert len(temporal.preceding_observation_ids) == 2


def test_cognitive_context_immutability() -> None:
    obs = Observation(source_id="test_sensor", payload={"temp": 25.0})
    context = CognitiveContext(
        reference_observation_id=obs.id,
        reference_subject_id="SUBJ-001",
        related_observation_ids=("obs-a", "obs-b"),
        active_rule_ids=("R-01",),
    )
    assert context.reference_observation_id == obs.id
    assert context.provenance.source_type == SourceType.COMPOSITE
    assert isinstance(context.related_observation_ids, tuple)
    assert isinstance(context.active_rule_ids, tuple)

    # Invariant: CognitiveContext is frozen and immutable
    with pytest.raises(Exception):
        context.reference_subject_id = "SUBJ-MUTATED"  # type: ignore
