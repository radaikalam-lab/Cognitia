"""Tests for Object Store persistence across canonical Cognitia entities."""

import pytest

from cognitia.abi.types import Action, Decision, Observation, Outcome
from cognitia.epistemic.types import Claim, Evidence, Hypothesis
from cognitia.experience.record import ExperienceBuilder
from cognitia.models.registry import ModelRecord, ModelStatus
from cognitia.persistence.events import ObjectQuery
from cognitia.persistence.store import InMemoryPersistenceStore
from cognitia.provenance.record import ProvenanceRecord
from cognitia.reasoning.types import ReasoningMode, ReasoningStep, ReasoningTrace


def test_persist_and_retrieve_all_canonical_objects():
    """Verify storing and retrieving all 10 canonical Cognitia object types."""
    store = InMemoryPersistenceStore()

    obs = Observation(source_id="flow_sensor_1", payload={"flow_rate": 3.4})
    ev = Evidence(target_id="hypo_1", observation_ids=[obs.id], confidence=0.88)
    exp = (
        ExperienceBuilder("app_test", "ep_42")
        .with_observation(obs)
        .with_action(Action(name="valve_open"))
        .build()
    )
    hyp = Hypothesis(statement="Flow rate increases with pressure")
    claim = Claim(statement="Pressure drop indicates blockage", confidence=0.91)
    prov = ProvenanceRecord(producer_id="sensor_node_0")
    trace = ReasoningTrace(
        mode=ReasoningMode.DEDUCTION,
        steps=[ReasoningStep(step_number=1, inference_rule="axiom", confidence=1.0)],
        confidence=1.0,
    )
    dec = Decision(
        proposal_type="flow_adjustment",
        proposed_action=Action(name="set_speed"),
        confidence=0.95,
        provenance=prov,
    )
    model = ModelRecord(
        model_id="fluid_model",
        model_version="1.0.0",
        calibration_checksum="checksum_abc",
        status=ModelStatus.ACTIVE,
    )

    objects = [obs, ev, exp, hyp, claim, prov, trace, dec, model]

    for obj in objects:
        store.save_object(obj)

    assert len(store.list_all_objects()) == len(objects)

    for obj in objects:
        retrieved = store.get_object(obj.id)
        assert retrieved is not None
        assert retrieved.id == obj.id
        assert retrieved.schema_version == obj.schema_version


def test_object_query_filtering():
    """Verify filtering persisted objects by schema version and entity type."""
    store = InMemoryPersistenceStore()
    obs1 = Observation(source_id="s1")
    obs2 = Observation(source_id="s2")
    claim = Claim(statement="System is operational")

    store.save_object(obs1)
    store.save_object(obs2)
    store.save_object(claim)

    q_obs = store.query_objects(ObjectQuery(entity_type="observation"))
    assert len(q_obs) == 2
    assert {o.id for o in q_obs} == {obs1.id, obs2.id}

    q_all_v1 = store.query_objects(ObjectQuery(schema_version="1.0.0"))
    assert len(q_all_v1) == 3
