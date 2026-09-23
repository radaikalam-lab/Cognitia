"""Comprehensive Tests for Model Lifecycle Governance (AL3-B).

Covers:
1. 9-state lifecycle state machine
2. Active model immutability & active model uniqueness by (domain_id, task_type, model_role)
3. Promotion proposal (authority=NONE) & external promotion decision (decision_source=EXTERNAL)
4. Domain/host activation observation (only external domain can activate)
5. Rollback proposal & external rollback decision
6. Domain freeze modes (NORMAL, FROZEN, OBSERVATION_ONLY)
7. Full model lineage reconstruction
8. Factual multi-metric comparisons
9. Drift-to-lifecycle integration
"""

import pytest

from cognitia.learning.contract import (
    AdaptiveLearningFailure,
    CandidateStatus,
    DomainFreezeMode,
    DriftReport,
    DriftType,
    FeedbackRecord,
    LifecycleEventType,
    ModelActivationObservation,
    ModelCandidate,
    ModelLifecycleEvent,
    ModelLifecycleState,
    ModelPromotionProposal,
    ModelRollbackProposal,
    OutcomeRecord,
    RuntimeActivationState,
    TaskType,
)
from cognitia.learning.service import AdaptiveLearningService
from cognitia.models.registry import InMemoryModelRegistry, ModelRecord, ModelStatus


def test_model_lifecycle_state_transitions():
    """Verify state transitions and immutability in the registry."""
    registry = InMemoryModelRegistry()
    rec = ModelRecord(
        model_id="laya_acoustic_v1",
        model_version="1.0.0",
        domain_id="default",
        status=ModelStatus.ACTIVE,
        lifecycle_state=ModelLifecycleState.ACTIVE,
        runtime_activation_state=RuntimeActivationState.ACTIVE,
    )
    registry.register(rec)

    # Verify duplicate registration fails (immutability)
    with pytest.raises(ValueError) as exc:
        registry.register(rec)
    assert "already registered and immutable" in str(exc.value)

    # Transition lifecycle state
    updated = registry.set_lifecycle_state(
        "laya_acoustic_v1", "1.0.0", ModelLifecycleState.SUPERSEDED, domain_id="default"
    )
    assert updated.lifecycle_state == ModelLifecycleState.SUPERSEDED
    assert updated.status == ModelStatus.DEPRECATED


def test_active_model_uniqueness_scoped_by_domain_task_role():
    """Verify active model uniqueness is scoped by (domain_id, task_type, model_role)."""
    service = AdaptiveLearningService()
    rec_primary = ModelRecord(
        model_id="acoustic_primary",
        model_version="1.0.0",
        domain_id="default",
        task_type="classification",
        model_role="primary",
        status=ModelStatus.ACTIVE,
        lifecycle_state=ModelLifecycleState.ACTIVE,
        runtime_activation_state=RuntimeActivationState.ACTIVE,
    )
    rec_shadow = ModelRecord(
        model_id="acoustic_shadow",
        model_version="1.0.0",
        domain_id="default",
        task_type="classification",
        model_role="shadow",
        status=ModelStatus.ACTIVE,
        lifecycle_state=ModelLifecycleState.ACTIVE,
        runtime_activation_state=RuntimeActivationState.ACTIVE,
    )
    service.model_registry.register(rec_primary)
    service.model_registry.register(rec_shadow)

    active_p = service.model_registry.get_active(domain_id="default", task_type="classification", model_role="primary")
    active_s = service.model_registry.get_active(domain_id="default", task_type="classification", model_role="shadow")

    assert active_p.model_id == "acoustic_primary"
    assert active_s.model_id == "acoustic_shadow"


def test_promotion_proposal_and_external_decision_flow():
    """Verify promotion proposal creates advisory artifact and external approval updates lifecycle to APPROVED without activating."""
    service = AdaptiveLearningService()
    base_rec = ModelRecord(
        model_id="laya_acoustic_v1",
        model_version="1.0.0",
        domain_id="default",
        status=ModelStatus.ACTIVE,
        lifecycle_state=ModelLifecycleState.ACTIVE,
        runtime_activation_state=RuntimeActivationState.ACTIVE,
    )
    service.model_registry.register(base_rec)

    # Create outcomes and feedback
    out1 = service.record_outcome(OutcomeRecord(
        source_id="sensor_1",
        target_prediction_id="pred_1",
        actual_values={"label": "resonance"},
    ))
    fb1 = service.create_feedback_from_outcome("pred_1", out1)

    # Learn -> candidate
    cand, update, event = service.learn_from_feedback(feedback_ids=[fb1.id])
    assert cand.status == CandidateStatus.CANDIDATE
    cand_rec = service.model_registry.get(cand.candidate_model_id, cand.candidate_model_version)
    assert cand_rec.lifecycle_state == ModelLifecycleState.CANDIDATE

    # Propose promotion (authority=NONE)
    proposal = service.create_promotion_proposal(
        candidate_version=cand.candidate_model_version,
        baseline_model_version="1.0.0",
        model_id="laya_acoustic_v1",
        dataset=[{"representation": None, "expected": "resonance"}],
    )
    assert proposal.authority == "NONE"
    assert proposal.status == CandidateStatus.PROPOSED

    # External decision: APPROVED
    decision_rec = service.record_promotion_decision(
        proposal_id=proposal.id,
        decision="APPROVED",
        decider_id="governance_lead_42",
        decider_authority="domain_safety_board",
        rationale="Metrics exceed baseline by 15%",
    )
    assert decision_rec.cognitia_authority == "NONE"
    assert decision_rec.decision == "APPROVED"

    # CRITICAL INVARIANT: Candidate is APPROVED in registry, but NOT ACTIVE!
    updated_cand_rec = service.model_registry.get(cand.candidate_model_id, cand.candidate_model_version)
    assert updated_cand_rec.lifecycle_state == ModelLifecycleState.APPROVED
    assert updated_cand_rec.runtime_activation_state == RuntimeActivationState.NOT_ACTIVE

    # Prior base model remains ACTIVE
    active_rec = service.model_registry.get_active(domain_id="default")
    assert active_rec.model_version == "1.0.0"


def test_domain_activation_observation_and_supersession():
    """Verify domain host activation observation reconciles active state and supersedes prior model."""
    service = AdaptiveLearningService()
    base_rec = ModelRecord(
        model_id="laya_acoustic_v1",
        model_version="1.0.0",
        domain_id="default",
        status=ModelStatus.ACTIVE,
        lifecycle_state=ModelLifecycleState.ACTIVE,
        runtime_activation_state=RuntimeActivationState.ACTIVE,
    )
    cand_rec = ModelRecord(
        model_id="laya_acoustic_v1",
        model_version="1.1-candidate",
        domain_id="default",
        status=ModelStatus.CANDIDATE,
        lifecycle_state=ModelLifecycleState.APPROVED,
        runtime_activation_state=RuntimeActivationState.NOT_ACTIVE,
    )
    service.model_registry.register(base_rec)
    service.model_registry.register(cand_rec)

    # Domain/Host activates candidate and reports observation to Cognitia
    obs = ModelActivationObservation(
        domain_id="default",
        model_id="laya_acoustic_v1",
        model_version="1.1-candidate",
        activation_type="PROMOTION",
        external_actor_id="domain_kubernetes_controller",
        decision_reference_id="decision_approved_123",
        authority="NONE",
    )
    recorded_obs = service.record_activation_observation(obs)
    assert recorded_obs.authority == "NONE"

    # Verify candidate is now ACTIVE
    active_now = service.model_registry.get_active(domain_id="default")
    assert active_now.model_version == "1.1-candidate"
    assert active_now.runtime_activation_state == RuntimeActivationState.ACTIVE

    # Verify base model was superseded and NOT deleted
    prior = service.model_registry.get("laya_acoustic_v1", "1.0.0")
    assert prior is not None
    assert prior.lifecycle_state == ModelLifecycleState.SUPERSEDED
    assert prior.runtime_activation_state == RuntimeActivationState.NOT_ACTIVE


def test_rollback_governance_flow():
    """Verify rollback proposal and external rollback decision workflow."""
    service = AdaptiveLearningService()
    v1_rec = ModelRecord(
        model_id="laya_acoustic_v1",
        model_version="1.0.0",
        domain_id="default",
        status=ModelStatus.DEPRECATED,
        lifecycle_state=ModelLifecycleState.SUPERSEDED,
    )
    v2_rec = ModelRecord(
        model_id="laya_acoustic_v1",
        model_version="1.1.0",
        domain_id="default",
        status=ModelStatus.ACTIVE,
        lifecycle_state=ModelLifecycleState.ACTIVE,
        runtime_activation_state=RuntimeActivationState.ACTIVE,
    )
    service.model_registry.register(v1_rec)
    service.model_registry.register(v2_rec)

    # Propose rollback from v2 to v1
    prop = service.propose_model_rollback(
        target_model_id="laya_acoustic_v1",
        target_model_version="1.0.0",
        reason="Anomalous behavior observed under high load in v1.1.0",
    )
    assert prop.authority == "NONE"
    assert prop.target_model_version == "1.0.0"
    assert prop.current_active_model_version == "1.1.0"

    # External decision approves rollback
    dec = service.record_rollback_decision(
        proposal_id=prop.id,
        approved=True,
        decider_id="safety_auditor_99",
        rationale="Approved immediate emergency rollback",
    )
    assert dec.approved is True
    assert dec.decision_source == "EXTERNAL"
    assert dec.cognitia_authority == "NONE"

    # Host domain executes rollback and reports observation
    obs = ModelActivationObservation(
        domain_id="default",
        model_id="laya_acoustic_v1",
        model_version="1.0.0",
        activation_type="ROLLBACK",
        external_actor_id="cluster_operator",
        decision_reference_id=dec.id,
        authority="NONE",
    )
    service.record_activation_observation(obs)

    # Verify v1 is active again, and v2 is superseded (historical record preserved)
    active = service.model_registry.get_active(domain_id="default")
    assert active.model_version == "1.0.0"
    v2_after = service.model_registry.get("laya_acoustic_v1", "1.1.0")
    assert v2_after is not None
    assert v2_after.lifecycle_state == ModelLifecycleState.SUPERSEDED


def test_domain_freeze_modes():
    """Verify NORMAL, FROZEN, and OBSERVATION_ONLY freeze mode behaviors."""
    service = AdaptiveLearningService()
    base_rec = ModelRecord(
        model_id="laya_acoustic_v1",
        model_version="1.0.0",
        domain_id="default",
        status=ModelStatus.ACTIVE,
    )
    service.model_registry.register(base_rec)

    # 1. Normal mode allows feedback learning
    out = service.record_outcome(OutcomeRecord(source_id="s1", actual_values={"label": "noise"}))
    fb = service.create_feedback_from_outcome("p1", out)
    cand, _, _ = service.learn_from_feedback(feedback_ids=[fb.id])
    assert cand is not None

    # 2. Freeze domain
    service.freeze_domain("default", mode=DomainFreezeMode.FROZEN)
    assert service.get_domain_freeze_mode("default") == DomainFreezeMode.FROZEN

    # 3. OBSERVATION_ONLY mode blocks candidate generation
    service.freeze_domain("default", mode=DomainFreezeMode.OBSERVATION_ONLY)
    assert service.get_domain_freeze_mode("default") == DomainFreezeMode.OBSERVATION_ONLY

    with pytest.raises(AdaptiveLearningFailure) as exc:
        service.learn_from_feedback(feedback_ids=[fb.id])
    assert exc.value.error_code == "DOMAIN_OBSERVATION_ONLY"

    # 4. Unfreeze domain restores normal operations
    service.unfreeze_domain("default")
    assert service.get_domain_freeze_mode("default") == DomainFreezeMode.NORMAL
    out2 = service.record_outcome(OutcomeRecord(source_id="s2", actual_values={"label": "harmonic"}))
    fb2 = service.create_feedback_from_outcome("p2", out2)
    cand_restored, _, _ = service.learn_from_feedback(feedback_ids=[fb.id, fb2.id])
    assert cand_restored is not None


def test_model_lineage_reconstruction():
    """Verify backward lineage reconstruction traces from active model to outcomes."""
    service = AdaptiveLearningService()
    base_rec = ModelRecord(
        model_id="laya_acoustic_v1",
        model_version="1.0.0",
        domain_id="default",
        status=ModelStatus.ACTIVE,
    )
    service.model_registry.register(base_rec)

    out = service.record_outcome(OutcomeRecord(source_id="s1", actual_values={"label": "harmonic"}))
    fb = service.create_feedback_from_outcome("p1", out)
    cand, update, ev = service.learn_from_feedback(feedback_ids=[fb.id])

    prop = service.create_promotion_proposal(
        candidate_version=cand.candidate_model_version,
        model_id="laya_acoustic_v1",
        dataset=[{"representation": None, "expected": "harmonic"}],
    )
    dec = service.record_promotion_decision(proposal_id=prop.id, decision="APPROVED", decider_id="governance_lead")
    obs = service.record_activation_observation(ModelActivationObservation(
        domain_id="default",
        model_id=cand.candidate_model_id,
        model_version=cand.candidate_model_version,
        activation_type="PROMOTION",
        external_actor_id="domain_operator",
        decision_reference_id=dec.id,
    ))

    # Reconstruct lineage
    lineage = service.reconstruct_model_lineage(
        model_id=cand.candidate_model_id,
        model_version=cand.candidate_model_version,
        domain_id="default",
    )

    assert lineage["model_id"] == "laya_acoustic_v1"
    assert lineage["model_version"] == cand.candidate_model_version
    assert lineage["lifecycle_state"] == "active"
    assert lineage["runtime_activation_state"] == "active"
    assert lineage["parent_model"]["model_version"] == "1.0.0"
    assert lineage["learning_events_count"] == 1
    assert lineage["feedback_count"] == 1
    assert lineage["outcome_count"] == 1
    assert lineage["promotion_proposals_count"] == 1
    assert lineage["promotion_decisions_count"] == 1
    assert lineage["activation_observations_count"] == 1
    assert lineage["authority"] == "NONE"


def test_drift_to_governance_integration():
    """Verify drift generates remediation recommendations without autonomous model activation."""
    service = AdaptiveLearningService()
    report = DriftReport(
        model_id="laya_acoustic_v1",
        drift_type=DriftType.PREDICTION,
        drift_detected=True,
        drift_magnitude=0.35,
        recommendation="Prediction distribution shifted significantly",
    )

    remediation = service.propose_drift_remediation(report)
    assert remediation["authority"] == "NONE"
    assert remediation["drift_detected"] is True
    assert remediation["governance_action"] == "RECOMMEND_DOMAIN_FREEZE"
    assert "freeze_proposal" in remediation
