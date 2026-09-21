"""Tests for Cognitive Context Provenance and Lineage Preservation."""

import pytest

from cognitia.abi.types import Observation
from cognitia.provenance.record import LineageChain, ProvenanceRecord, SourceType
from cognitia.rules.types import CognitiveRule
from cognitia.runtime.local import LocalCognitiveRuntime


def test_context_provenance_links_all_constituent_entities() -> None:
    runtime = LocalCognitiveRuntime()

    obs_past = Observation(
        source_id="sensor_temp",
        payload={"temperature": 100.0},
        created_at="2026-09-21T09:59:00Z",
    )
    runtime.persistence.save_object(obs_past)

    rule = CognitiveRule(
        rule_id="R-HEAT-01",
        version="1.0.0",
        name="Overheat Alert",
        scope="thermal",
        predicate={"field": "temperature", "op": ">", "value": 90.0},
        provenance=ProvenanceRecord(
            source_type=SourceType.HUMAN,
            producer_id="human_thermal_specialist",
            is_deterministic=True,
        ),
    )
    runtime.rules.create_rule(rule)

    obs_ref = Observation(
        source_id="sensor_temp",
        payload={"temperature": 95.0},
        created_at="2026-09-21T10:00:00Z",
        metadata={"scope": "thermal"},
    )
    runtime.persistence.save_object(obs_ref)

    context = runtime.assemble_context(obs_ref)

    # Provenance verification
    prov = context.provenance
    assert prov.source_type == SourceType.COMPOSITE
    assert prov.producer_id == "context_assembly_engine"
    assert obs_ref.id in prov.parent_ids
    assert obs_past.id in prov.parent_ids
    assert rule.id in prov.parent_ids

    # Lineage chain resolution
    lineage = LineageChain()
    lineage.add_record(prov)
    lineage.add_record(rule.provenance)

    assert lineage.get_record(prov.id) == prov
