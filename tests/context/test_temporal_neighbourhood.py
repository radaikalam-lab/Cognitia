"""Tests for Temporal Neighbourhood Enrichment.

Validates that temporal relationships (BEFORE, AFTER, CONCURRENT, INTERVAL)
and time deltas are computed deterministically without causal inference.
"""

import pytest

from cognitia.abi.types import Observation
from cognitia.context.types import (
    ContextQuery,
    TemporalRelationType,
)
from cognitia.runtime.local import LocalCognitiveRuntime


def test_temporal_neighbourhood_relations_and_deltas() -> None:
    runtime = LocalCognitiveRuntime()

    obs_past = Observation(
        source_id="sensor:1",
        payload={"v": 10},
        created_at="2026-09-21T10:00:00.000000Z",
    )
    obs_ref = Observation(
        source_id="sensor:1",
        payload={"v": 20},
        created_at="2026-09-21T10:00:02.400000Z",
    )
    obs_future = Observation(
        source_id="sensor:1",
        payload={"v": 30},
        created_at="2026-09-21T10:00:05.000000Z",
    )
    obs_concurrent = Observation(
        source_id="sensor:2",
        payload={"v": 99},
        created_at="2026-09-21T10:00:02.400000Z",
    )

    runtime.persistence.save_object(obs_past)
    runtime.persistence.save_object(obs_ref)
    runtime.persistence.save_object(obs_future)
    runtime.persistence.save_object(obs_concurrent)

    context = runtime.assemble_context(obs_ref)

    assert len(context.temporal_context.relations) == 3
    rel_past = [r for r in context.temporal_context.relations if r.entity_id == obs_past.id][0]
    rel_future = [r for r in context.temporal_context.relations if r.entity_id == obs_future.id][0]
    rel_concurrent = [r for r in context.temporal_context.relations if r.entity_id == obs_concurrent.id][0]

    assert rel_past.relation_type == TemporalRelationType.BEFORE
    assert rel_past.delta_seconds == -2.4
    assert rel_future.relation_type == TemporalRelationType.AFTER
    assert rel_future.delta_seconds == 2.6
    assert rel_concurrent.relation_type == TemporalRelationType.CONCURRENT
    assert rel_concurrent.delta_seconds == 0.0


def test_temporal_neighbourhood_window_bounding() -> None:
    runtime = LocalCognitiveRuntime()

    obs_in_window = Observation(
        source_id="sensor:1",
        payload={"v": 1},
        created_at="2026-09-21T10:00:00Z",
    )
    obs_ref = Observation(
        source_id="sensor:1",
        payload={"v": 2},
        created_at="2026-09-21T10:00:10Z",
    )
    obs_outside_window = Observation(
        source_id="sensor:1",
        payload={"v": 3},
        created_at="2026-09-21T12:00:00Z",  # 2 hours later
    )

    runtime.persistence.save_object(obs_in_window)
    runtime.persistence.save_object(obs_ref)
    runtime.persistence.save_object(obs_outside_window)

    query = ContextQuery(temporal_window_seconds_after=30.0)
    context = runtime.assemble_context(obs_ref, query)

    assert obs_outside_window.id not in context.temporal_context.succeeding_observation_ids
    assert obs_in_window.id in context.temporal_context.preceding_observation_ids
