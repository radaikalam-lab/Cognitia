"""Tests verifying the Persistence Contract, SPI, and Authority Boundaries."""

import pytest

from cognitia.abi.types import Observation
from cognitia.persistence.events import CognitiveEvent, CognitiveEventType
from cognitia.persistence.store import InMemoryPersistenceStore, PersistenceStore
from cognitia.runtime.local import LocalCognitiveRuntime


def test_persistence_store_protocol_compliance():
    """Verify that InMemoryPersistenceStore implements the PersistenceStore Protocol."""
    store = InMemoryPersistenceStore()
    assert isinstance(store, PersistenceStore)


def test_runtime_composes_persistence_store():
    """Verify that LocalCognitiveRuntime composes the persistence store cleanly."""
    store = InMemoryPersistenceStore()
    runtime = LocalCognitiveRuntime(persistence_store=store)

    assert runtime.persistence is store
    assert isinstance(runtime.persistence, InMemoryPersistenceStore)


def test_persistence_is_non_authoritative():
    """Verify that persistence records cognitive history without possessing execution/actuator interfaces."""
    store = InMemoryPersistenceStore()
    event = CognitiveEvent(
        event_type=CognitiveEventType.DECISION_PROPOSED.value,
        subject_id="decision_123",
        payload={"action": "reduce_flow"},
    )
    store.append_event(event)

    persisted = store.get_event(event.id)
    assert persisted is not None

    # Persistence is strictly a historical substrate without execution authority
    assert not hasattr(persisted, "execute")
    assert not hasattr(persisted, "actuate")
    assert not hasattr(store, "execute_decision")
    assert not hasattr(store, "actuate")
