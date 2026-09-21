"""Tests for Provenance records, lineage chains, and checksum calculation."""

import dataclasses
import pytest

from cognitia.provenance.record import (
    LineageChain,
    ProvenanceRecord,
    SourceType,
    compute_checksum,
)


def test_provenance_immutability():
    """Verify that ProvenanceRecord is immutable."""
    prov = ProvenanceRecord(source_type=SourceType.SENSOR, producer_id="node_1")

    with pytest.raises(dataclasses.FrozenInstanceError):
        prov.producer_id = "node_2"  # type: ignore[misc]


def test_compute_checksum_deterministic():
    """Verify that compute_checksum is deterministic for identical data structures."""
    data_a = {"alpha": [1, 2, 3], "beta": "test"}
    data_b = {"beta": "test", "alpha": [1, 2, 3]}

    hash_a = compute_checksum(data_a)
    hash_b = compute_checksum(data_b)

    assert hash_a == hash_b
    assert len(hash_a) == 64  # SHA-256 hex string


def test_lineage_chain_traversal():
    """Verify DAG ancestor traversal in LineageChain."""
    prov1 = ProvenanceRecord(producer_id="p1")
    prov2 = ProvenanceRecord(producer_id="p2", parent_ids=[prov1.id])
    prov3 = ProvenanceRecord(producer_id="p3", parent_ids=[prov2.id])

    chain = LineageChain()
    chain.add_record(prov1)
    chain.add_record(prov2)
    chain.add_record(prov3)

    ancestors = chain.get_ancestors(prov3.id)
    ancestor_ids = [a.id for a in ancestors]

    assert prov1.id in ancestor_ids
    assert prov2.id in ancestor_ids
    assert prov3.id not in ancestor_ids
