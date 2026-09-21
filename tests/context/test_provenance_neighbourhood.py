"""Tests for Provenance Neighbourhood Enrichment.

Validates bounded lineage traversal and connection mapping using the canonical Provenance DAG.
"""

import pytest

from cognitia.abi.types import Observation
from cognitia.runtime.local import LocalCognitiveRuntime


def test_provenance_neighbourhood_traversal() -> None:
    runtime = LocalCognitiveRuntime()

    obs = Observation(
        source_id="sensor:flow_meter",
        payload={"flow_rate": 12.5},
        created_at="2026-09-21T10:00:00Z",
        metadata={
            "source_application": "hydraulics_service",
            "parent_ids": ["parent_raw_telemetry_001"],
            "producer_id": "flow_calibrator_v1",
        },
    )
    runtime.persistence.save_object(obs)

    context = runtime.assemble_context(obs)

    assert len(context.provenance_neighbourhood) == 1
    prov_nh = context.provenance_neighbourhood[0]
    assert prov_nh.root_entity_id == obs.id
    assert "parent_raw_telemetry_001" in prov_nh.derived_from_ids
    assert "flow_calibrator_v1" in prov_nh.produced_by_ids
    assert "sensor:flow_meter" in prov_nh.measured_by_ids
