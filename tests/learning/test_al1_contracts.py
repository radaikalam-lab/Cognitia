"""Tests for AL1 strongly-typed contracts, schema validation, and authority invariants."""

import pytest
from cognitia.abi.types import CognitiveObject
from cognitia.learning.contract import (
    CandidateStatus,
    FeedbackRecord,
    LearningEvent,
    LearningUpdate,
    ModelCandidate,
    ModelEvaluation,
    ModelPromotionProposal,
    OutcomeRecord,
    PredictionRecord,
    PromotionDecisionRecord,
    TaskType,
)
from cognitia.provenance.record import ProvenanceRecord, SourceType


def test_outcome_record_authority_invariant():
    """Verify OutcomeRecord enforces authority == 'NONE'."""
    outcome = OutcomeRecord(
        source_id="sensor_42",
        target_prediction_id="pred_123",
        actual_values={"label": "resonance", "spl_db": 92.4},
        authority="NONE",
    )
    assert outcome.authority == "NONE"
    assert outcome.source_id == "sensor_42"
    assert outcome.is_ground_truth is True
    assert isinstance(outcome, CognitiveObject)

    with pytest.raises(ValueError, match="authority must strictly be 'NONE'"):
        OutcomeRecord(
            source_id="sensor_42",
            authority="PRODUCTION_OVERWRITE",
        )


def test_feedback_record_authority_invariant():
    """Verify FeedbackRecord enforces authority == 'NONE'."""
    fb = FeedbackRecord(
        prediction_id="pred_100",
        outcome_id="out_200",
        model_id="laya_acoustic_v1",
        loss_or_error=0.0,
        metrics={"accuracy": 1.0},
        authority="NONE",
    )
    assert fb.authority == "NONE"
    assert fb.loss_or_error == 0.0

    with pytest.raises(ValueError, match="authority must strictly be 'NONE'"):
        FeedbackRecord(
            prediction_id="pred_100",
            outcome_id="out_200",
            authority="ACTIVE_WRITE",
        )


def test_learning_event_and_update_authority_invariants():
    """Verify LearningEvent and LearningUpdate enforce authority == 'NONE'."""
    event = LearningEvent(
        event_type="outcome_feedback",
        feedback_ids=["fb_1", "fb_2"],
        model_id="laya_acoustic_v1",
        sample_count=2,
        authority="NONE",
    )
    assert event.authority == "NONE"
    assert len(event.feedback_ids) == 2

    with pytest.raises(ValueError, match="authority must strictly be 'NONE'"):
        LearningEvent(authority="ADMIN")

    update = LearningUpdate(
        learning_event_id=event.id,
        parent_model_id="laya_acoustic_v1",
        candidate_model_id="laya_acoustic_v1",
        candidate_model_version="1.1-candidate",
        parameter_deltas={"bias_0": 0.05},
        authority="NONE",
    )
    assert update.authority == "NONE"
    assert update.candidate_model_version == "1.1-candidate"

    with pytest.raises(ValueError, match="authority must strictly be 'NONE'"):
        LearningUpdate(authority="ROOT")


def test_model_candidate_and_evaluation_authority_invariants():
    """Verify ModelCandidate and ModelEvaluation enforce authority == 'NONE'."""
    candidate = ModelCandidate(
        candidate_model_id="laya_acoustic_v1",
        candidate_model_version="1.1-candidate",
        parent_model_id="laya_acoustic_v1",
        parent_model_version="1.0.0",
        status=CandidateStatus.CANDIDATE,
        parameter_fingerprint="abc123sha",
        authority="NONE",
    )
    assert candidate.authority == "NONE"
    assert candidate.status == CandidateStatus.CANDIDATE

    with pytest.raises(ValueError, match="authority must strictly be 'NONE'"):
        ModelCandidate(authority="DEPLOY")

    evaluation = ModelEvaluation(
        model_id="laya_acoustic_v1",
        model_version="1.1-candidate",
        dataset_id="eval_v1",
        metrics={"accuracy": 0.95},
        authority="NONE",
    )
    assert evaluation.authority == "NONE"

    with pytest.raises(ValueError, match="authority must strictly be 'NONE'"):
        ModelEvaluation(authority="WRITE")


def test_promotion_proposal_and_decision_records():
    """Verify ModelPromotionProposal and PromotionDecisionRecord semantics."""
    prop = ModelPromotionProposal(
        parent_model_id="laya_acoustic_v1",
        parent_model_version="1.0.0",
        candidate_model_id="laya_acoustic_v1",
        candidate_model_version="1.1-candidate",
        baseline_metrics={"accuracy": 0.80},
        candidate_metrics={"accuracy": 0.92},
        metric_deltas={"accuracy_delta": 0.12},
        rationale="12% accuracy gain on eval dataset",
        authority="NONE",
    )
    assert prop.authority == "NONE"
    assert prop.recommendation == "PROPOSE_CANDIDATE"

    with pytest.raises(ValueError, match="authority must strictly be 'NONE'"):
        ModelPromotionProposal(authority="ACTIVATE")

    decision = PromotionDecisionRecord(
        proposal_id=prop.id,
        candidate_model_id=prop.candidate_model_id,
        candidate_model_version=prop.candidate_model_version,
        decision="ACCEPTED",
        decider_id="domain_architect_alice",
        decider_authority="Acoustics Governance Committee",
        cognitia_authority="NONE",
    )
    assert decision.cognitia_authority == "NONE"
    assert decision.decision == "ACCEPTED"
    assert decision.decider_id == "domain_architect_alice"

    with pytest.raises(ValueError, match="cognitia_authority must strictly be 'NONE'"):
        PromotionDecisionRecord(cognitia_authority="AUTONOMOUS_PROMOTION")
