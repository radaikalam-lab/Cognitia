"""Tests for Cognitive ABI types, identity, and deterministic serialization."""

import json

from cognitia.abi.types import (
    SCHEMA_VERSION_V1,
    Action,
    CognitiveObject,
    Decision,
    DeterministicSerializer,
    Observation,
    Outcome,
)


def test_stable_identity_and_version():
    """Verify that ABI objects generate unique stable UUIDs and default schema version."""
    obj1 = CognitiveObject()
    obj2 = CognitiveObject()

    assert obj1.id != obj2.id
    assert len(obj1.id) == 36  # UUID length
    assert obj1.schema_version == SCHEMA_VERSION_V1
    assert "T" in obj1.created_at  # ISO format timestamp


def test_deterministic_serialization_key_ordering():
    """Verify that serialization is canonical and key ordering is lexicographically sorted."""
    obs1 = Observation(source_id="sensor_a", payload={"z_key": 1, "a_key": 2, "m_key": 3})
    obs2 = Observation(source_id="sensor_a", payload={"a_key": 2, "m_key": 3, "z_key": 1})

    # When created with same id & timestamp, they serialize to identical byte strings
    dict1 = {"id": "static-id", "schema_version": "1.0.0", "payload": {"b": 2, "a": 1}}
    dict2 = {"payload": {"a": 1, "b": 2}, "schema_version": "1.0.0", "id": "static-id"}

    s1 = DeterministicSerializer.serialize(dict1)
    s2 = DeterministicSerializer.serialize(dict2)

    assert s1 == s2
    assert s1 == '{"id":"static-id","payload":{"a":1,"b":2},"schema_version":"1.0.0"}'


def test_serialization_round_trip():
    """Verify round trip deserialization."""
    action = Action(name="adjust_frequency", parameters={"delta_hz": 50.0})
    serialized = action.serialize()
    deserialized = DeterministicSerializer.deserialize(serialized)

    assert deserialized["name"] == "adjust_frequency"
    assert deserialized["parameters"]["delta_hz"] == 50.0
    assert deserialized["id"] == action.id
