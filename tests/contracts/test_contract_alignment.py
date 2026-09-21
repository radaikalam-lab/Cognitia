"""Regression and alignment tests for Phase 0 Contract Freeze."""

import dataclasses
import uuid
import pytest

from cognitia.abi.types import (
    Action,
    CognitiveObject,
    Decision,
    DeterministicSerializer,
    Observation,
)
from cognitia.capabilities.base import CapabilityType
from cognitia.epistemic.service import InMemoryEpistemicService
from cognitia.epistemic.types import (
    Claim,
    EpistemicStatus,
    Evidence,
    EvidenceDirection,
    Hypothesis,
    TransitionOutcome,
)
from cognitia.models.registry import (
    InMemoryModelRegistry,
    ModelRecord,
    ModelStatus,
)
from cognitia.provenance.record import (
    LineageChain,
    ProvenanceRecord,
    SourceType,
    compute_checksum,
)
from cognitia.reasoning.types import (
    ReasoningMode,
    ReasoningStep,
    ReasoningTrace,
)


def test_evidence_supports_multiple_observations():
    """Verify Evidence can encapsulate multiple upstream observation IDs (COG-003)."""
    obs1 = Observation(source_id="temp_sensor", payload={"temp_c": 82.5})
    obs2 = Observation(source_id="vibe_sensor", payload={"rms_g": 4.1})
    obs3 = Observation(source_id="acoustic_mic", payload={"spl_db": 98.2})

    hypothesis = Hypothesis(statement="Bearing cavitation occurs under high thermal load")

    prov = ProvenanceRecord(
        source_type=SourceType.COMPOSITE,
        producer_id="epistemic_evaluator",
        parent_ids=[obs1.id, obs2.id, obs3.id],
        input_checksums={
            obs1.id: compute_checksum(obs1),
            obs2.id: compute_checksum(obs2),
            obs3.id: compute_checksum(obs3),
        },
    )

    evidence = Evidence(
        target_id=hypothesis.id,
        observation_ids=[obs1.id, obs2.id, obs3.id],
        direction=EvidenceDirection.SUPPORT,
        confidence=0.92,
        provenance=prov,
    )

    assert len(evidence.observation_ids) == 3
    assert obs1.id in evidence.observation_ids
    assert obs2.id in evidence.observation_ids
    assert obs3.id in evidence.observation_ids
    assert evidence.provenance.parent_ids == [obs1.id, obs2.id, obs3.id]


def test_evidence_lineage_is_complete():
    """Verify that multi-observation evidence lineage can be traversed cleanly in a LineageChain."""
    obs1 = Observation(source_id="s1")
    obs2 = Observation(source_id="s2")

    prov_obs1 = ProvenanceRecord(producer_id="s1")
    prov_obs2 = ProvenanceRecord(producer_id="s2")

    prov_ev = ProvenanceRecord(
        source_type=SourceType.COMPOSITE,
        producer_id="sensor_fusion",
        parent_ids=[prov_obs1.id, prov_obs2.id],
    )

    chain = LineageChain()
    chain.add_record(prov_obs1)
    chain.add_record(prov_obs2)
    chain.add_record(prov_ev)

    ancestors = chain.get_ancestors(prov_ev.id)
    ancestor_ids = {a.id for a in ancestors}

    assert prov_obs1.id in ancestor_ids
    assert prov_obs2.id in ancestor_ids
    assert len(ancestor_ids) == 2


def test_decision_provenance_is_canonical():
    """Verify that Decision carries a canonical ProvenanceRecord directly (COG-005)."""
    prov = ProvenanceRecord(
        source_type=SourceType.DETERMINISTIC_RULE,
        producer_id="decision_engine",
        capability_id="policy_v1",
        is_deterministic=True,
    )
    action = Action(name="throttle_flow", parameters={"pct": 20})
    decision = Decision(
        proposal_type="flow_control_proposal",
        proposed_action=action,
        confidence=0.95,
        rationale="Nominal pressure threshold exceeded",
        provenance=prov,
    )

    assert isinstance(decision.provenance, ProvenanceRecord)
    assert decision.provenance.producer_id == "decision_engine"
    assert decision.provenance.capability_id == "policy_v1"
    assert decision.provenance.is_deterministic is True


def test_decision_lineage_is_reconstructable():
    """Verify complete lineage reconstruction from Observation -> Evidence -> Trace -> Decision."""
    prov_obs = ProvenanceRecord(source_type=SourceType.SENSOR, producer_id="sensor_0")
    prov_ev = ProvenanceRecord(
        source_type=SourceType.DETERMINISTIC_RULE,
        producer_id="rule_evaluator",
        parent_ids=[prov_obs.id],
    )
    prov_trace = ProvenanceRecord(
        source_type=SourceType.REASONING_ENGINE,
        producer_id="reasoner_v1",
        parent_ids=[prov_ev.id],
    )
    prov_dec = ProvenanceRecord(
        source_type=SourceType.DETERMINISTIC_RULE,
        producer_id="policy_v1",
        parent_ids=[prov_trace.id],
    )

    chain = LineageChain({p.id: p for p in [prov_obs, prov_ev, prov_trace, prov_dec]})
    ancestors = chain.get_ancestors(prov_dec.id)
    ancestor_ids = [a.id for a in ancestors]

    assert ancestor_ids == [prov_obs.id, prov_ev.id, prov_trace.id]


def test_model_timestamp_semantics():
    """Verify distinct semantics of created_at (artifact creation) vs registered_at (ingestion) (COG-006)."""
    model = ModelRecord(
        model_id="acoustic_resonator",
        model_version="1.0.0",
        calibration_checksum="checksum_abc",
        status=ModelStatus.ACTIVE,
    )

    assert "T" in model.created_at
    assert "T" in model.registered_at
    assert model.created_at is not None
    assert model.registered_at is not None


def test_model_identity_content_is_immutable():
    """Verify that ModelRecord parameters, checksum, and identity cannot be mutated."""
    model = ModelRecord(
        model_id="fluid_model",
        model_version="1.0.0",
        calibration_checksum="hash_123",
    )

    with pytest.raises(dataclasses.FrozenInstanceError):
        model.calibration_checksum = "mutated_hash"  # type: ignore[misc]

    with pytest.raises(dataclasses.FrozenInstanceError):
        model.model_version = "2.0.0"  # type: ignore[misc]


def test_model_status_lifecycle_does_not_mutate_identity():
    """Verify set_status() modifies lifecycle status while preserving immutable parameters and timestamps (Section 11)."""
    registry = InMemoryModelRegistry()
    initial_model = ModelRecord(
        model_id="fluid_model",
        model_version="1.0.0",
        calibration_checksum="hash_123",
        status=ModelStatus.ACTIVE,
    )
    registry.register(initial_model)

    # Transition status to DEPRECATED
    registry.set_status("fluid_model", "1.0.0", ModelStatus.DEPRECATED)

    updated_model = registry.get("fluid_model", "1.0.0")
    assert updated_model is not None
    assert updated_model.status == ModelStatus.DEPRECATED

    # Invariants: identity, timestamps, and calibration checksum MUST remain strictly identical
    assert updated_model.id == initial_model.id
    assert updated_model.created_at == initial_model.created_at
    assert updated_model.registered_at == initial_model.registered_at
    assert updated_model.calibration_checksum == initial_model.calibration_checksum
    assert updated_model.model_id == initial_model.model_id
    assert updated_model.model_version == initial_model.model_version


def test_confidence_is_bounded():
    """Verify confidence values are bounded between 0.0 and 1.0 (COG-007)."""
    claim = Claim(statement="Resonance at 440 Hz", confidence=0.85)
    evidence = Evidence(confidence=0.9)
    decision = Decision(confidence=0.75)
    step = ReasoningStep(step_number=1, inference_rule="rule_a", confidence=1.0)
    trace = ReasoningTrace(confidence=0.95)

    for c in [claim.confidence, evidence.confidence, decision.confidence, step.confidence, trace.confidence]:
        assert 0.0 <= c <= 1.0


def test_confidence_semantics_are_subsystem_specific():
    """Verify confidence fields belong to their specific cognitive contexts without mathematical conflation (COG-007)."""
    # Claim confidence = epistemic support
    claim = Claim(statement="Hypothesis supported by 5 trials", confidence=0.9)
    # Decision confidence = capability proposal confidence
    decision = Decision(confidence=0.6, rationale="Heuristic boundary proximity")
    # Step confidence = logical validity
    step = ReasoningStep(step_number=1, inference_rule="modus_ponens", confidence=1.0)

    assert claim.confidence != decision.confidence
    assert step.confidence == 1.0


def test_canonical_entity_identity():
    """Verify canonical entity ID is strictly a valid UUIDv4 string (COG-001)."""
    obj = CognitiveObject()
    # Validate UUID formatting
    parsed_uuid = uuid.UUID(obj.id, version=4)
    assert str(parsed_uuid) == obj.id


def test_deterministic_float_serialization():
    """Verify deterministic float serialization across edge-case values (COG-002)."""
    test_cases = [
        {"val": 0.0},
        {"val": -0.0},
        {"val": 1e-08},
        {"val": 1.23456789},
        {"val": 999999999.99999},
    ]

    for tc in test_cases:
        s1 = DeterministicSerializer.serialize(tc)
        s2 = DeterministicSerializer.serialize(tc)
        assert s1 == s2
        assert compute_checksum(tc) == compute_checksum(tc)


def test_transition_outcome_semantics():
    """Verify TransitionOutcome enum represents governance outcomes distinct from EpistemicStatus (COG-004)."""
    assert TransitionOutcome.REVISION_PROPOSED.value == "revision_proposed"
    assert TransitionOutcome.ACCEPTED.value == "accepted"
    assert TransitionOutcome.REJECTED.value == "rejected"

    # Epistemic status is distinct
    assert EpistemicStatus.SUPPORTED.value == "supported"
    assert EpistemicStatus.REFUTED.value == "refuted"
    assert EpistemicStatus.SUPPORTED.value != TransitionOutcome.ACCEPTED.value
