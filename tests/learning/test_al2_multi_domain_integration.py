"""Integration tests for AL2 multi-domain learning, explicit transfer, and persistence recovery."""

import tempfile
from pathlib import Path

from cognitia.abi.types import Observation
from cognitia.learning.contract import (
    CandidateStatus,
    KnowledgeType,
    LearningDomain,
    OutcomeRecord,
    TransferCompatibilityStatus,
    TransferType,
)
from cognitia.learning.representation import RepresentationAdapter
from cognitia.learning.service import AdaptiveLearningService
from cognitia.models.registry import ModelRecord, ModelStatus
from runtime.gateway.epistemic_bridge import EpistemicBridge
from runtime.persistence.file_persistence import FilePersistenceService


def test_three_domain_lifecycle_and_persistence_recovery():
    """Execute complete 3-domain lifecycle (Alpha, Beta, Gamma), transfer from Alpha to Beta, verify Gamma isolation, and recover from P1 journal."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)

        # ----------------------------------------------------
        # Session 1: Multi-domain operations
        # ----------------------------------------------------
        pers1 = FilePersistenceService(data_dir=data_dir)
        pers1.initialize_and_recover()
        service1 = AdaptiveLearningService(persistence_service=pers1)

        # 1. Register three explicit domains
        alpha = LearningDomain(
            domain_id="domain_alpha",
            domain_version="1.0.0",
            description="Alpha: Acoustic sensor analysis",
            representation_version="1.0.0",
            declared_providers=["laya"],
        )
        beta = LearningDomain(
            domain_id="domain_beta",
            domain_version="1.0.0",
            description="Beta: Ultrasonic analytics",
            representation_version="1.0.0",
            declared_providers=["laya"],
        )
        gamma = LearningDomain(
            domain_id="domain_gamma",
            domain_version="1.0.0",
            description="Gamma: Optical telemetry",
            representation_version="2.0.0",
            declared_providers=["laya"],
        )
        service1.register_domain(alpha)
        service1.register_domain(beta)
        service1.register_domain(gamma)

        # 2. Register Active models in Alpha, Beta, Gamma
        m_alpha = ModelRecord(
            model_id="alpha_base_model",
            model_version="1.0.0",
            domain_id="domain_alpha",
            provider="laya",
            status=ModelStatus.ACTIVE,
        )
        m_beta = ModelRecord(
            model_id="beta_base_model",
            model_version="1.0.0",
            domain_id="domain_beta",
            provider="laya",
            status=ModelStatus.ACTIVE,
        )
        m_gamma = ModelRecord(
            model_id="gamma_base_model",
            model_version="1.0.0",
            domain_id="domain_gamma",
            provider="laya",
            status=ModelStatus.ACTIVE,
        )
        service1.register_model(m_alpha)
        service1.register_model(m_beta)
        service1.register_model(m_gamma)

        # 3. Alpha Domain Learning: Observation -> Prediction -> Outcome -> Feedback -> Candidate
        obs_a = Observation(source_id="alpha_sensor_1", payload={"spl_db": 85.0})
        pred_a = service1.predict_from_observation(obs_a, model_id="alpha_base_model", domain_id="domain_alpha")
        outcome_a = OutcomeRecord(
            domain_id="domain_alpha",
            source_id="alpha_sensor_1",
            target_prediction_id=pred_a.id,
            actual_values={"label": "resonance"},
        )
        service1.record_outcome(outcome_a)
        fb_a = service1.create_feedback_from_outcome(prediction_id=pred_a.id, outcome=outcome_a, domain_id="domain_alpha")
        cand_a, update_a, event_a = service1.learn_from_feedback(
            feedback_ids=[fb_a.id],
            base_model_id="alpha_base_model",
            domain_id="domain_alpha",
            seed=42,
        )
        assert cand_a.domain_id == "domain_alpha"

        # 4. Explicit Transfer from Alpha to Beta
        proposal_ab = service1.create_transfer_proposal(
            source_domain_id="domain_alpha",
            target_domain_id="domain_beta",
            source_model_id="alpha_base_model",
            source_model_version=cand_a.candidate_model_version,
            target_model_id="beta_base_model",
            target_base_model_version="1.0.0",
            transfer_type=TransferType.FEATURE_EXTRACTOR_TRANSFER,
            knowledge_type=KnowledgeType.FEATURE_EXTRACTOR,
            rationale="Transfer acoustic resonance feature extractor to ultrasonic domain",
            transfer_payload={"layers": ["conv1"], "weights": [0.1, 0.2]},
        )
        assert proposal_ab.authority == "NONE"

        # Compatibility Evaluation
        compat_ab = service1.evaluate_transfer_compatibility(proposal_ab)
        assert compat_ab.status in (TransferCompatibilityStatus.COMPATIBLE, TransferCompatibilityStatus.PARTIALLY_COMPATIBLE)

        # Instantiate target candidate in Beta
        cand_b = service1.instantiate_transfer_candidate(
            proposal_id=proposal_ab.id,
            target_candidate_version="1.1-transferred-beta",
            seed=99,
        )
        assert cand_b.domain_id == "domain_beta"
        assert cand_b.candidate_model_id == "beta_base_model"
        assert cand_b.status == CandidateStatus.CANDIDATE
        assert cand_b.authority == "NONE"

        # Verify Beta active model remains unchanged at 1.0.0
        active_b = service1.model_registry.get_active("beta_base_model", domain_id="domain_beta")
        assert active_b.model_version == "1.0.0"

        # Evaluate candidate in Beta
        beta_eval_dataset = [{"payload": {"spl_db": 90.0}, "expected": "resonance"}]
        adapted_beta_dataset = [
            {"representation": RepresentationAdapter.adapt_raw(s["payload"]), "expected": s["expected"]}
            for s in beta_eval_dataset
        ]
        eval_b = service1.evaluate_candidate(
            candidate_version_or_id=cand_b.candidate_model_version,
            dataset=adapted_beta_dataset,
            domain_id="domain_beta",
        )
        assert eval_b.domain_id == "domain_beta"

        # Propose promotion in Beta
        prop_b = service1.create_promotion_proposal(
            candidate_version=cand_b.candidate_model_version,
            baseline_model_version="1.0.0",
            model_id="beta_base_model",
            dataset=adapted_beta_dataset,
            domain_id="domain_beta",
        )
        assert prop_b.domain_id == "domain_beta"
        assert prop_b.authority == "NONE"

        # External Governance Decision for Beta
        dec_b = service1.record_transfer_decision(
            proposal_id=proposal_ab.id,
            decision="ACCEPTED",
            decider_id="beta_governance_reviewer",
            rationale="Approved for target ultrasonic testing candidate",
        )
        assert dec_b.decision_source == "EXTERNAL"
        assert dec_b.cognitia_authority == "NONE"

        # Verify Gamma domain remained completely untouched
        gamma_cands = service1.list_candidates(domain_id="domain_gamma")
        assert len(gamma_cands) == 0
        gamma_history = service1.list_history(domain_id="domain_gamma")
        assert len(gamma_history) == 0

        pers1.close()

        # ----------------------------------------------------
        # Session 2: Complete Restart & Recovery from FilePersistence
        # ----------------------------------------------------
        pers2 = FilePersistenceService(data_dir=data_dir)
        bridge = EpistemicBridge(persistence_service=pers2)

        try:
            rec_service = bridge.adaptive_learning

            # Verify all 3 domains recovered
            recovered_domain_ids = [d.domain_id for d in rec_service.list_domains()]
            assert "domain_alpha" in recovered_domain_ids
            assert "domain_beta" in recovered_domain_ids
            assert "domain_gamma" in recovered_domain_ids

            # Verify transfer proposal recovered
            rec_props = rec_service.list_transfer_proposals()
            assert len(rec_props) == 1
            assert rec_props[0].id == proposal_ab.id
            assert rec_props[0].authority == "NONE"

            # Verify target candidate recovered with correct domain and lineage
            rec_cand_b = rec_service._candidates.get("1.1-transferred-beta")
            assert rec_cand_b is not None
            assert rec_cand_b.domain_id == "domain_beta"
            assert rec_cand_b.authority == "NONE"
            assert rec_cand_b.parameters.get("source_transfer_proposal_id") == proposal_ab.id

            # Verify external transfer decision recovered
            rec_dec = rec_service.list_transfer_decisions()[0]
            assert rec_dec.proposal_id == proposal_ab.id
            assert rec_dec.decision_source == "EXTERNAL"
            assert rec_dec.cognitia_authority == "NONE"

        finally:
            bridge.close()

