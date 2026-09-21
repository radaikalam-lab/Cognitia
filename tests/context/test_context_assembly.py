"""Tests for Cognitive Context Assembly across Temporal, Subject, Memory, and Rule dimensions."""

import pytest

from cognitia.abi.types import Observation
from cognitia.context.types import ContextQuery, RelevanceReason
from cognitia.epistemic.types import Claim, EpistemicStatus
from cognitia.experience.record import ExperienceBuilder
from cognitia.rules.types import CognitiveRule
from cognitia.runtime.local import LocalCognitiveRuntime


def test_context_assembly_temporal_and_subject_matching() -> None:
    runtime = LocalCognitiveRuntime()

    # Create a sequence of observations around reference observation O_ref (T=10:00:00)
    o_prev_far = Observation(
        source_id="sensor_a",
        payload={"val": 1},
        created_at="2026-09-21T08:00:00Z",  # 2 hours before
        metadata={"subject_id": "BATCH-01"},
    )
    o_prev_near = Observation(
        source_id="sensor_a",
        payload={"val": 2},
        created_at="2026-09-21T09:55:00Z",  # 5 mins before
        metadata={"subject_id": "BATCH-01"},
    )
    o_ref = Observation(
        source_id="sensor_a",
        payload={"val": 3},
        created_at="2026-09-21T10:00:00Z",
        metadata={"subject_id": "BATCH-01", "scope": "quality_control"},
    )
    o_succ_near = Observation(
        source_id="sensor_b",
        payload={"val": 4},
        created_at="2026-09-21T10:01:00Z",  # 1 min after
        metadata={"subject_id": "BATCH-01"},
    )
    o_succ_far = Observation(
        source_id="sensor_b",
        payload={"val": 5},
        created_at="2026-09-21T12:00:00Z",  # 2 hours after
        metadata={"subject_id": "BATCH-01"},
    )

    for o in [o_prev_far, o_prev_near, o_ref, o_succ_near, o_succ_far]:
        runtime.persistence.save_object(o)

    # Context query with window: 15 mins before (900s), 5 mins after (300s)
    query = ContextQuery(
        temporal_window_seconds_before=900.0,
        temporal_window_seconds_after=300.0,
    )
    context = runtime.assemble_context(o_ref, query=query)

    assert context.reference_observation_id == o_ref.id
    assert context.reference_subject_id == "BATCH-01"

    # Temporal context should contain o_prev_near and o_succ_near, but not the far ones
    temporal = context.temporal_context
    assert o_prev_near.id in temporal.preceding_observation_ids
    assert o_prev_far.id not in temporal.preceding_observation_ids
    assert o_succ_near.id in temporal.succeeding_observation_ids
    assert o_succ_far.id not in temporal.succeeding_observation_ids

    # Check time deltas
    assert temporal.deltas_dict[o_prev_near.id] < 0
    assert temporal.deltas_dict[o_succ_near.id] > 0


def test_context_assembly_rule_discovery_and_memory() -> None:
    runtime = LocalCognitiveRuntime()

    # Register an active rule relevant to scope
    rule1 = CognitiveRule(
        rule_id="R-QC-01",
        version="1.0.0",
        name="High Vibration Flag",
        scope="quality_control",
        predicate={"field": "vibration_level", "op": ">", "value": 7.5},
        author_id="human_engineer",
    )
    rule2 = CognitiveRule(
        rule_id="R-FIN-01",
        version="1.0.0",
        name="Credit Check",
        scope="finance",
        predicate={"field": "credit", "op": "<", "value": 0},
    )
    runtime.rules.create_rule(rule1)
    runtime.rules.create_rule(rule2)

    # Persist an experience into memory
    exp = (
        ExperienceBuilder(source_application="test_app", episode_id="EPISODE-10")
        .with_metadata("source_application", "test_app")
        .with_metadata("subject_id", "MACHINE-42")
        .build()
    )
    runtime.persistence.save_object(exp)

    # Reference observation matching rule1
    o_ref = Observation(
        source_id="sensor_vibe",
        payload={"vibration_level": 8.2},
        metadata={"subject_id": "MACHINE-42", "scope": "quality_control", "episode_id": "EPISODE-10", "source_application": "test_app"},
    )
    runtime.persistence.save_object(o_ref)

    context = runtime.assemble_context(o_ref)

    # Rule discovery: rule1 matches scope and predicate; rule2 does not match scope
    assert "R-QC-01" in context.active_rule_ids
    assert "R-FIN-01" not in context.active_rule_ids

    # Memory inclusion
    assert len(context.related_experience_ids) >= 1
    assert exp.id in context.related_experience_ids

    # Context items contain audit reasons
    reasons = {item.item_id: item.relevance_reason for item in context.context_items}
    assert reasons[o_ref.id] == RelevanceReason.REFERENCE_OBSERVATION
    assert reasons[rule1.id] == RelevanceReason.RULE_MATCH
    assert reasons[exp.id] == RelevanceReason.MEMORY_MATCH
