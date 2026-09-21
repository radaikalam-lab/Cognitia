"""Tests for Event Journal operations, queries, and timeline reconstruction."""

import pytest

from cognitia.persistence.events import (
    CognitiveEvent,
    CognitiveEventType,
    EventQuery,
)
from cognitia.persistence.store import InMemoryPersistenceStore
from cognitia.provenance.record import SourceType


def test_append_and_get_event():
    """Verify appending and retrieving events by unique ID."""
    store = InMemoryPersistenceStore()
    event = CognitiveEvent(
        event_type=CognitiveEventType.OBSERVATION_RECORDED.value,
        source_type=SourceType.SENSOR,
        source_id="mic_0",
        subject_id="obs_101",
        payload={"frequency_hz": 440.0},
    )

    store.append_event(event)
    retrieved = store.get_event(event.id)

    assert retrieved is not None
    assert retrieved.id == event.id
    assert retrieved.event_type == CognitiveEventType.OBSERVATION_RECORDED.value
    assert retrieved.payload["frequency_hz"] == 440.0


def test_duplicate_event_rejection():
    """Verify that attempting to append an event with an existing ID is rejected."""
    store = InMemoryPersistenceStore()
    event = CognitiveEvent(id="static_event_id", event_type="test_event")
    store.append_event(event)

    with pytest.raises(ValueError, match="already exists and is immutable"):
        store.append_event(event)


def test_event_query_filtering():
    """Verify querying events by type, source, subject, and limit."""
    store = InMemoryPersistenceStore()
    e1 = CognitiveEvent(
        event_type=CognitiveEventType.OBSERVATION_RECORDED.value,
        source_id="sensor_a",
        subject_id="sub_1",
    )
    e2 = CognitiveEvent(
        event_type=CognitiveEventType.DECISION_PROPOSED.value,
        source_id="engine_x",
        subject_id="sub_1",
    )
    e3 = CognitiveEvent(
        event_type=CognitiveEventType.OUTCOME_RECORDED.value,
        source_id="sensor_a",
        subject_id="sub_2",
    )

    for e in [e1, e2, e3]:
        store.append_event(e)

    # Query by subject_id
    q_subj = store.query_events(EventQuery(subject_id="sub_1"))
    assert len(q_subj) == 2
    assert {e.id for e in q_subj} == {e1.id, e2.id}

    # Query by event_type
    q_type = store.query_events(
        EventQuery(event_type=CognitiveEventType.DECISION_PROPOSED.value)
    )
    assert len(q_type) == 1
    assert q_type[0].id == e2.id

    # Query with limit
    q_limit = store.query_events(EventQuery(limit=2))
    assert len(q_limit) == 2


def test_cognitive_timeline_preservation():
    """Verify sequential timeline reconstruction for a multi-step cognitive episode."""
    store = InMemoryPersistenceStore()
    events = [
        CognitiveEvent(
            event_type=CognitiveEventType.OBSERVATION_RECORDED.value,
            subject_id="ep_1",
            payload={"step": 1},
        ),
        CognitiveEvent(
            event_type=CognitiveEventType.EVIDENCE_REGISTERED.value,
            subject_id="ep_1",
            payload={"step": 2},
        ),
        CognitiveEvent(
            event_type=CognitiveEventType.DECISION_PROPOSED.value,
            subject_id="ep_1",
            payload={"step": 3},
        ),
        CognitiveEvent(
            event_type=CognitiveEventType.OUTCOME_RECORDED.value,
            subject_id="ep_1",
            payload={"step": 4},
        ),
    ]

    for ev in events:
        store.append_event(ev)

    timeline = store.get_timeline(subject_id="ep_1")
    assert len(timeline) == 4
    assert [e.payload["step"] for e in timeline] == [1, 2, 3, 4]
