"""Tests for Event Immutability and Historical Preservation in Persistence."""

import dataclasses
import pytest

from cognitia.abi.types import Action, Decision, Observation
from cognitia.models.registry import ModelRecord, ModelStatus
from cognitia.persistence.events import CognitiveEvent, CognitiveEventType
from cognitia.persistence.store import InMemoryPersistenceStore


def test_event_immutability():
    """Verify that CognitiveEvent is frozen and cannot be mutated post-creation."""
    event = CognitiveEvent(
        event_type=CognitiveEventType.DECISION_PROPOSED.value,
        subject_id="dec_001",
        payload={"flow_delta": 10},
    )

    with pytest.raises(dataclasses.FrozenInstanceError):
        event.event_type = "mutated_event_type"  # type: ignore[misc]

    with pytest.raises(dataclasses.FrozenInstanceError):
        event.payload = {"flow_delta": 20}  # type: ignore[misc]


def test_historical_epistemic_transitions_preserved():
    """Verify that sequential epistemic transitions appended as events are preserved immutably."""
    store = InMemoryPersistenceStore()

    # Step 1: Hypothesis registered
    e1 = CognitiveEvent(
        event_type=CognitiveEventType.HYPOTHESIS_REGISTERED.value,
        subject_id="node_hyp_1",
        payload={"status": "hypothesis"},
    )
    # Step 2: Transitioned to SUPPORTED
    e2 = CognitiveEvent(
        event_type=CognitiveEventType.EPISTEMIC_TRANSITION_RECORDED.value,
        subject_id="node_hyp_1",
        payload={"from_status": "hypothesis", "to_status": "supported"},
    )
    # Step 3: Challenged and transitioned to UNRESOLVED
    e3 = CognitiveEvent(
        event_type=CognitiveEventType.EPISTEMIC_TRANSITION_RECORDED.value,
        subject_id="node_hyp_1",
        payload={"from_status": "supported", "to_status": "unresolved"},
    )

    store.append_event(e1)
    store.append_event(e2)
    store.append_event(e3)

    history = store.get_timeline(subject_id="node_hyp_1")
    assert len(history) == 3
    assert history[0].event_type == CognitiveEventType.HYPOTHESIS_REGISTERED.value
    assert history[1].payload["to_status"] == "supported"
    assert history[2].payload["to_status"] == "unresolved"


def test_historical_model_versions_preserved():
    """Verify that historical model version records and status changes are preserved."""
    store = InMemoryPersistenceStore()

    m1 = ModelRecord(model_id="acoustic_mod", model_version="1.0.0", status=ModelStatus.DEPRECATED)
    m2 = ModelRecord(model_id="acoustic_mod", model_version="2.0.0", status=ModelStatus.ACTIVE)

    store.save_object(m1)
    store.save_object(m2)

    retrieved_v1 = store.get_object(m1.id)
    retrieved_v2 = store.get_object(m2.id)

    assert retrieved_v1 is not None and isinstance(retrieved_v1, ModelRecord)
    assert retrieved_v2 is not None and isinstance(retrieved_v2, ModelRecord)
    assert retrieved_v1.model_version == "1.0.0"
    assert retrieved_v2.model_version == "2.0.0"
