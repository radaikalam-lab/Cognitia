"""Tests verifying the Cognitive Memory and Consolidation Contracts and Invariants."""

import pytest

from cognitia.abi.types import Observation
from cognitia.memory.consolidation import (
    ConsolidationService,
    InMemoryConsolidationService,
)
from cognitia.memory.store import InMemoryMemoryStore, MemoryStore
from cognitia.memory.types import MemoryQuery
from cognitia.persistence.store import InMemoryPersistenceStore
from cognitia.runtime.local import LocalCognitiveRuntime


def test_memory_store_protocol_compliance():
    """Verify that InMemoryMemoryStore implements the MemoryStore Protocol."""
    persistence = InMemoryPersistenceStore()
    memory = InMemoryMemoryStore(persistence_store=persistence)
    assert isinstance(memory, MemoryStore)


def test_runtime_composes_memory_and_consolidation():
    """Verify that LocalCognitiveRuntime composes MemoryStore and ConsolidationService."""
    runtime = LocalCognitiveRuntime()
    assert isinstance(runtime.memory, MemoryStore)
    assert isinstance(runtime.consolidation, ConsolidationService)


def test_memory_retrieval_does_not_mutate_state_or_authority():
    """Verify that memory retrieval is strictly read-oriented and produces no side-effects on models."""
    persistence = InMemoryPersistenceStore()
    obs = Observation(source_id="flow_sensor_0", payload={"val": 42})
    persistence.save_object(obs)

    memory = InMemoryMemoryStore(persistence_store=persistence)
    context = memory.get_context(MemoryQuery(object_types=["observation"]))

    assert len(context.observations) == 1
    assert context.observations[0].id == obs.id

    # Memory context carries no actuator or direct domain execution authority
    assert not hasattr(context, "execute")
    assert not hasattr(context, "actuate")
