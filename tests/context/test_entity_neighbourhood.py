"""Tests for Entity Neighbourhood Enrichment.

Validates discovery of structural associations (same subject, episode, source, provenance)
without converting structural co-occurrence into unfounded semantic claims.
"""

import pytest

from cognitia.abi.types import Observation
from cognitia.context.types import EntityRelationType
from cognitia.experience.record import ExperienceBuilder
from cognitia.runtime.local import LocalCognitiveRuntime


def test_entity_neighbourhood_associations() -> None:
    runtime = LocalCognitiveRuntime()

    obs_ref = Observation(
        source_id="device:node_1:sample",
        payload={"subject_id": "TURBINE-001", "pressure": 4.2},
        created_at="2026-09-21T10:00:00Z",
        metadata={
            "subject_id": "TURBINE-001",
            "episode_id": "EP-INSPECTION-9",
            "source_application": "telemetry_hub",
        },
    )
    obs_same_subject = Observation(
        source_id="device:node_2:sample",
        payload={"subject_id": "TURBINE-001", "temp": 72.0},
        created_at="2026-09-21T10:00:05Z",
        metadata={
            "subject_id": "TURBINE-001",
            "episode_id": "EP-INSPECTION-10",
            "source_application": "sensor_net",
        },
    )
    obs_same_episode = Observation(
        source_id="device:node_1:sample",
        payload={"subject_id": "TURBINE-002"},
        created_at="2026-09-21T10:00:10Z",
        metadata={
            "subject_id": "TURBINE-002",
            "episode_id": "EP-INSPECTION-9",
            "source_application": "telemetry_hub",
        },
    )

    exp_shared = (
        ExperienceBuilder(source_application="telemetry_hub", episode_id="EP-INSPECTION-9")
        .with_metadata("subject_id", "TURBINE-001")
        .build()
    )

    runtime.persistence.save_object(obs_ref)
    runtime.persistence.save_object(obs_same_subject)
    runtime.persistence.save_object(obs_same_episode)
    runtime.persistence.save_object(exp_shared)

    context = runtime.assemble_context(obs_ref)

    assert len(context.entity_neighbourhood) >= 3

    types_found = {r.relation_type for r in context.entity_neighbourhood}
    assert EntityRelationType.SAME_SUBJECT in types_found
    assert EntityRelationType.SAME_EPISODE in types_found
    assert EntityRelationType.SAME_SOURCE in types_found
    assert EntityRelationType.SHARED_PROVENANCE in types_found
