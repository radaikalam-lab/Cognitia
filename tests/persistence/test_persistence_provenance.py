"""Tests for Provenance integration and lineage reconstruction in the Persistence Store."""

import pytest

from cognitia.abi.types import Observation
from cognitia.epistemic.types import Evidence
from cognitia.persistence.store import InMemoryPersistenceStore
from cognitia.provenance.record import LineageChain, ProvenanceRecord, SourceType


def test_persist_and_reconstruct_provenance_lineage():
    """Verify persisting a multi-stage cognitive artifact chain and reconstructing complete lineage."""
    store = InMemoryPersistenceStore()

    prov_obs1 = ProvenanceRecord(source_type=SourceType.SENSOR, producer_id="sensor_temp")
    prov_obs2 = ProvenanceRecord(source_type=SourceType.SENSOR, producer_id="sensor_vibe")

    prov_fusion = ProvenanceRecord(
        source_type=SourceType.COMPOSITE,
        producer_id="fusion_engine",
        parent_ids=[prov_obs1.id, prov_obs2.id],
    )

    prov_hypothesis = ProvenanceRecord(
        source_type=SourceType.DETERMINISTIC_RULE,
        producer_id="rule_evaluator",
        parent_ids=[prov_fusion.id],
    )

    prov_decision = ProvenanceRecord(
        source_type=SourceType.DETERMINISTIC_RULE,
        producer_id="decision_engine",
        parent_ids=[prov_hypothesis.id],
    )

    for prov in [prov_obs1, prov_obs2, prov_fusion, prov_hypothesis, prov_decision]:
        store.save_object(prov)

    # Reconstruct lineage from store
    persisted_records = {
        obj.id: obj
        for obj in store.list_all_objects()
        if isinstance(obj, ProvenanceRecord)
    }
    chain = LineageChain(persisted_records)

    ancestors = chain.get_ancestors(prov_decision.id)
    ancestor_ids = {a.id for a in ancestors}

    assert ancestor_ids == {prov_obs1.id, prov_obs2.id, prov_fusion.id, prov_hypothesis.id}
    assert prov_decision.id not in ancestor_ids
