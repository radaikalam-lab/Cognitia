"""Tests verifying Provenance preservation in Memory retrieval."""

import pytest

from cognitia.abi.types import Observation
from cognitia.epistemic.types import Evidence, Hypothesis
from cognitia.memory.store import InMemoryMemoryStore
from cognitia.memory.types import MemoryQuery
from cognitia.persistence.store import InMemoryPersistenceStore
from cognitia.provenance.record import LineageChain, ProvenanceRecord, SourceType


def test_memory_context_provenance_preserves_parent_lineage():
    """Verify that MemoryContext creates a composite provenance record tracking all constituent IDs."""
    persistence = InMemoryPersistenceStore()

    prov_obs = ProvenanceRecord(source_type=SourceType.SENSOR, producer_id="sensor_0")
    obs = Observation(source_id="sensor_0", payload={"val": 10})

    prov_ev = ProvenanceRecord(
        source_type=SourceType.DETERMINISTIC_RULE,
        producer_id="rule_evaluator",
        parent_ids=[prov_obs.id],
    )
    ev = Evidence(target_id="hyp_0", observation_ids=[obs.id], provenance=prov_ev)

    persistence.save_object(obs)
    persistence.save_object(ev)

    memory = InMemoryMemoryStore(persistence_store=persistence)
    context = memory.get_context(MemoryQuery())

    assert context.provenance.source_type == SourceType.COMPOSITE
    assert obs.id in context.provenance.parent_ids
    assert ev.id in context.provenance.parent_ids
