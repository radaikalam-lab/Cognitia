"""Tests for complete AL1 Outcome-Driven Learning Lifecycle."""

import pytest
from cognitia.abi.types import Observation
from cognitia.learning.contract import (
    CandidateStatus,
    FeedbackRecord,
    OutcomeRecord,
    TaskType,
)
from cognitia.learning.service import AdaptiveLearningService
from cognitia.models.registry import InMemoryModelRegistry, ModelRecord, ModelStatus


def test_complete_al1_learning_lifecycle():
    """Verify full AL1 lifecycle:
    Observation -> Prediction -> Outcome -> Feedback -> Learning Event -> Candidate -> Evaluation -> Proposal -> Decision.
    """
    registry = InMemoryModelRegistry()
    service = AdaptiveLearningService(model_registry=registry)

    # 1. Base Active Model Registered
    base_model = ModelRecord(
        model_id="laya_acoustic_v1",
        model_version="1.0.0",
        provider="laya",
        status=ModelStatus.ACTIVE,
    )
    service.register_model(base_model)
    active_before = registry.get_active("laya_acoustic_v1")
    assert active_before is not None
    assert active_before.model_version == "1.0.0"

    # 2. Host Observation & Inference
    obs = Observation(source_id="mic_01", payload={"spl_db": 95.0, "frequency_hz": 1200.0})
    pred = service.predict_from_observation(obs, model_id="laya_acoustic_v1")
    assert pred.authority == "NONE"
    assert pred.output.get("decision") is not None

    # 3. Ground Truth Outcome Observed
    outcome = OutcomeRecord(
        source_id="mic_01",
        target_prediction_id=pred.id,
        observation_id=obs.id,
        actual_values={"label": "resonance", "spl_db": 95.0},
        authority="NONE",
    )
    service.record_outcome(outcome)
    assert len(service.list_outcomes()) == 1

    # 4. Feedback Linkage
    feedback = service.create_feedback_from_outcome(
        prediction_id=pred.id,
        outcome=outcome,
    )
    assert feedback.authority == "NONE"
    assert feedback.prediction_id == pred.id
    assert feedback.outcome_id == outcome.id
    assert len(service.list_feedback()) == 1

    # 5. Candidate Model Generation (Learn from Feedback)
    candidate, update, event = service.learn_from_feedback(
        feedback_ids=[feedback.id],
        base_model_id="laya_acoustic_v1",
        seed=42,
    )
    assert candidate.authority == "NONE"
    assert update.authority == "NONE"
    assert event.authority == "NONE"
    assert candidate.parent_model_version == "1.0.0"
    assert "candidate" in candidate.candidate_model_version
    assert candidate.status == CandidateStatus.CANDIDATE

    # CRITICAL INVARIANT: Active model is NOT overwritten or changed!
    active_after = registry.get_active("laya_acoustic_v1")
    assert active_after is not None
    assert active_after.model_version == "1.0.0"
    assert active_after.status == ModelStatus.ACTIVE

    # Candidate is listed in registry with CANDIDATE status
    versions = registry.list_versions("laya_acoustic_v1")
    assert len(versions) >= 2
    cand_in_reg = next(v for v in versions if v.model_version == candidate.candidate_model_version)
    assert cand_in_reg.status == ModelStatus.CANDIDATE

    # 6. Candidate Evaluation on Dataset
    eval_dataset = [
        {"payload": {"spl_db": 90.0}, "expected": "resonance"},
        {"payload": {"frequency_hz": 1100.0}, "expected": "harmonic"},
    ]
    from cognitia.learning.representation import RepresentationAdapter
    adapted_eval_dataset = [
        {"representation": RepresentationAdapter.adapt_raw(s["payload"]), "expected": s["expected"]}
        for s in eval_dataset
    ]

    evaluation = service.evaluate_candidate(
        candidate_version_or_id=candidate.candidate_model_version,
        dataset=adapted_eval_dataset,
    )
    assert evaluation.authority == "NONE"
    assert evaluation.model_version == candidate.candidate_model_version
    assert "accuracy" in evaluation.metrics

    # 7. Model Promotion Proposal Generation
    proposal = service.create_promotion_proposal(
        candidate_version=candidate.candidate_model_version,
        baseline_model_version="1.0.0",
        model_id="laya_acoustic_v1",
        dataset=adapted_eval_dataset,
    )
    assert proposal.authority == "NONE"
    assert proposal.candidate_model_version == candidate.candidate_model_version
    assert proposal.parent_model_version == "1.0.0"
    assert "accuracy_delta" in proposal.metric_deltas

    # 8. External Governance Decision (Decision supplied by domain authority)
    decision = service.record_promotion_decision(
        proposal_id=proposal.id,
        decision="ACCEPTED",
        decider_id="domain_architect_bob",
        decider_authority="Acoustics Lead",
        rationale="Candidate exhibits validated improvement on resonance frequencies.",
    )
    assert decision.cognitia_authority == "NONE"
    assert decision.decision == "ACCEPTED"
    assert len(service.list_decisions()) == 1

    # CRITICAL INVARIANT: Even when ACCEPTED, Cognitia does NOT autonomously activate the model
    active_final = registry.get_active("laya_acoustic_v1")
    assert active_final is not None
    assert active_final.model_version == "1.0.0"
