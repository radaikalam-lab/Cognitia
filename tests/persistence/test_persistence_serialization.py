"""Tests for Persistence serialization, checksum integrity, and validation."""

import pytest

from cognitia.abi.types import DeterministicSerializer, Observation
from cognitia.persistence.events import CognitiveEvent, CognitiveEventType
from cognitia.persistence.store import InMemoryPersistenceStore
from cognitia.provenance.record import compute_checksum


def test_event_deterministic_serialization():
    """Verify that CognitiveEvent serializes deterministically and reproduces identical checksums."""
    event = CognitiveEvent(
        event_type=CognitiveEventType.OBSERVATION_RECORDED.value,
        source_id="sensor_1",
        subject_id="obs_101",
        payload={"b_param": 2.5, "a_param": 1.0},
    )

    s1 = DeterministicSerializer.serialize(event)
    s2 = DeterministicSerializer.serialize(event)

    assert s1 == s2
    assert compute_checksum(event) == compute_checksum(event)


def test_event_missing_schema_version_rejection():
    """Verify that an event without a schema_version is rejected upon append."""
    store = InMemoryPersistenceStore()

    # Create invalid event object with empty schema_version
    invalid_event = CognitiveEvent(schema_version="")

    with pytest.raises(ValueError, match="must declare a valid schema_version"):
        store.append_event(invalid_event)
