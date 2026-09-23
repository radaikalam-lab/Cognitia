"""Tests for Deterministic Learning Replay and Fingerprint Verification."""

import pytest
from cognitia.learning.laya_provider import LayaProvider
from cognitia.learning.replay import LearningReplayEngine
from cognitia.learning.service import AdaptiveLearningService
from cognitia.learning.contract import OutcomeRecord, FeedbackRecord
from cognitia.models.registry import ModelRecord, ModelStatus


def test_deterministic_candidate_generation_and_replay():
    """Verify that learning with the same seed + feedback produces bit-for-bit identical candidate models and passes replay verification."""
    service = AdaptiveLearningService()
    provider = service.get_provider("laya")

    base_model = ModelRecord(
        model_id="laya_acoustic_v1",
        model_version="1.0.0",
        provider="laya",
        status=ModelStatus.ACTIVE,
    )
    service.register_model(base_model)

    # Ingest 3 outcomes and feedbacks
    for i in range(3):
        out = OutcomeRecord(
            source_id=f"sensor_{i}",
            target_prediction_id=f"pred_{i}",
            actual_values={"label": "resonance" if i % 2 == 0 else "harmonic"},
            authority="NONE",
        )
        service.record_outcome(out)
        fb = FeedbackRecord(
            prediction_id=f"pred_{i}",
            outcome_id=out.id,
            model_id="laya_acoustic_v1",
            model_version="1.0.0",
            loss_or_error=0.0 if i == 0 else 1.0,
            authority="NONE",
        )
        service.record_feedback(fb)

    feedback_ids = [f.id for f in service.list_feedback()]

    # Run 1
    cand1, update1, event1 = service.learn_from_feedback(
        feedback_ids=feedback_ids,
        base_model_id="laya_acoustic_v1",
        seed=1337,
    )

    # Replay Run using LearningReplayEngine
    replay_result = service.replay_learning(
        candidate_version=cand1.candidate_model_version,
        model_id="laya_acoustic_v1",
        seed=1337,
    )

    assert replay_result.is_replayable is True
    assert replay_result.is_exact_match is True
    assert replay_result.status == "VERIFIED"
    assert replay_result.original_fingerprint == cand1.parameter_fingerprint
    assert replay_result.replayed_fingerprint == cand1.parameter_fingerprint
    assert replay_result.parameter_parity is True
    assert replay_result.authority == "NONE"


def test_replay_fails_closed_when_provenance_is_missing():
    """Verify replay explicitly fails closed when candidate or base model is missing."""
    provider = LayaProvider()
    result = LearningReplayEngine.replay_candidate_learning(
        provider=provider,
        base_model=None,
        candidate=None,
        learning_events=[],
    )
    assert result.is_replayable is False
    assert result.is_exact_match is False
    assert result.status == "NON_REPLAYABLE"
    assert result.authority == "NONE"
