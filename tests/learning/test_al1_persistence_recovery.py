"""Tests for AL1 persistence to FilePersistenceService (P1) and complete restart recovery."""

import tempfile
from pathlib import Path

from cognitia.abi.types import Observation
from cognitia.learning.contract import OutcomeRecord
from cognitia.learning.service import AdaptiveLearningService
from cognitia.models.registry import ModelRecord, ModelStatus
from runtime.gateway.epistemic_bridge import EpistemicBridge
from runtime.persistence.file_persistence import FilePersistenceService


def test_al1_persistence_and_restart_recovery():
    """Verify that outcomes, feedback, candidates, evaluations, proposals, and decisions survive restart recovery."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)

        # 1. Initialize Persistence and Service Session 1
        pers1 = FilePersistenceService(data_dir=data_dir)
        pers1.initialize_and_recover()
        service1 = AdaptiveLearningService(persistence_service=pers1)

        # Register model
        base_model = ModelRecord(
            model_id="laya_acoustic_v1",
            model_version="1.0.0",
            provider="laya",
            status=ModelStatus.ACTIVE,
        )
        service1.register_model(base_model)

        # Prediction
        obs = Observation(source_id="mic_01", payload={"spl_db": 88.0})
        pred = service1.predict_from_observation(obs, model_id="laya_acoustic_v1")

        # Outcome
        outcome = OutcomeRecord(
            source_id="mic_01",
            target_prediction_id=pred.id,
            actual_values={"label": "resonance"},
            authority="NONE",
        )
        service1.record_outcome(outcome)

        # Feedback
        fb = service1.create_feedback_from_outcome(prediction_id=pred.id, outcome=outcome)

        # Candidate Learning
        candidate, update, event = service1.learn_from_feedback(
            feedback_ids=[fb.id],
            base_model_id="laya_acoustic_v1",
            seed=42,
        )

        # Evaluation
        eval_dataset = [{"payload": {"spl_db": 88.0}, "expected": "resonance"}]
        from cognitia.learning.representation import RepresentationAdapter
        adapted_eval_dataset = [
            {"representation": RepresentationAdapter.adapt_raw(s["payload"]), "expected": s["expected"]}
            for s in eval_dataset
        ]
        evaluation = service1.evaluate_candidate(
            candidate_version_or_id=candidate.candidate_model_version,
            dataset=adapted_eval_dataset,
        )

        # Promotion Proposal
        proposal = service1.create_promotion_proposal(
            candidate_version=candidate.candidate_model_version,
            baseline_model_version="1.0.0",
            model_id="laya_acoustic_v1",
            dataset=adapted_eval_dataset,
        )

        # Governance Decision
        decision = service1.record_promotion_decision(
            proposal_id=proposal.id,
            decision="ACCEPTED",
            decider_id="architect_charlie",
            decider_authority="Governance",
        )

        pers1.close()

        # 2. Session 2: Restart and recover from file journal via EpistemicBridge
        pers2 = FilePersistenceService(data_dir=data_dir)
        bridge = EpistemicBridge(persistence_service=pers2)

        try:
            recovered_learning = bridge.adaptive_learning
            assert len(recovered_learning.list_history()) == 1
            assert len(recovered_learning.list_outcomes()) == 1
            assert len(recovered_learning.list_feedback()) == 1
            assert len(recovered_learning.list_candidates()) == 1
            assert len(recovered_learning.list_evaluations()) == 1
            assert len(recovered_learning.list_proposals()) == 1
            assert len(recovered_learning.list_decisions()) == 1

            rec_cand = recovered_learning.list_candidates()[0]
            assert rec_cand.candidate_model_version == candidate.candidate_model_version
            assert rec_cand.parameter_fingerprint == candidate.parameter_fingerprint
            assert rec_cand.authority == "NONE"

            rec_prop = recovered_learning.list_proposals()[0]
            assert rec_prop.id == proposal.id
            assert rec_prop.authority == "NONE"

            rec_dec = recovered_learning.list_decisions()[0]
            assert rec_dec.id == decision.id
            assert rec_dec.cognitia_authority == "NONE"
            assert rec_dec.decision == "ACCEPTED"
        finally:
            pers2.close()
