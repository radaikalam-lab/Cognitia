"""Tests for AL2 Transfer Proposals and Target Candidate Instantiation."""

import pytest
from cognitia.learning.contract import (
    CandidateStatus,
    KnowledgeType,
    LearningDomain,
    TransferType,
)
from cognitia.learning.service import AdaptiveLearningService
from cognitia.models.registry import ModelRecord, ModelStatus


def test_transfer_proposal_creation_and_retrieval():
    """Verify transfer proposal creation between registered domains."""
    service = AdaptiveLearningService()
    service.register_domain(LearningDomain(domain_id="domain_source"))
    service.register_domain(LearningDomain(domain_id="domain_target"))

    service.register_model(
        ModelRecord(
            model_id="source_model",
            model_version="1.0.0",
            domain_id="domain_source",
            provider="laya",
            status=ModelStatus.ACTIVE,
        )
    )

    proposal = service.create_transfer_proposal(
        source_domain_id="domain_source",
        target_domain_id="domain_target",
        source_model_id="source_model",
        source_model_version="1.0.0",
        target_model_id="target_model",
        transfer_type=TransferType.FEATURE_EXTRACTOR_TRANSFER,
        knowledge_type=KnowledgeType.FEATURE_EXTRACTOR,
        rationale="Transfer harmonic feature extractor layers",
        transfer_payload={"layers": ["conv1", "conv2"], "weights": [0.1, 0.2]},
    )

    assert bool(proposal.id)
    assert proposal.source_domain_id == "domain_source"
    assert proposal.target_domain_id == "domain_target"
    assert proposal.authority == "NONE"
    assert proposal.transfer_payload["layers"] == ["conv1", "conv2"]

    proposals = service.list_transfer_proposals()
    assert len(proposals) == 1
    assert proposals[0].id == proposal.id


def test_instantiate_transfer_candidate_creates_candidate_only():
    """Verify instantiate_transfer_candidate creates target candidate ONLY and NEVER mutates active model."""
    service = AdaptiveLearningService()
    service.register_domain(LearningDomain(domain_id="domain_source"))
    service.register_domain(LearningDomain(domain_id="domain_target"))

    # Register active models in source and target
    service.register_model(
        ModelRecord(
            model_id="source_model",
            model_version="1.0.0",
            domain_id="domain_source",
            provider="laya",
            status=ModelStatus.ACTIVE,
        )
    )
    target_active_original = ModelRecord(
        model_id="target_model",
        model_version="1.0.0",
        domain_id="domain_target",
        provider="laya",
        status=ModelStatus.ACTIVE,
    )
    service.register_model(target_active_original)

    # Initial state check: target active model is 1.0.0
    active_before = service.model_registry.get_active("target_model", domain_id="domain_target")
    assert active_before is not None
    assert active_before.model_version == "1.0.0"
    assert active_before.status == ModelStatus.ACTIVE

    # Create proposal
    proposal = service.create_transfer_proposal(
        source_domain_id="domain_source",
        target_domain_id="domain_target",
        source_model_id="source_model",
        source_model_version="1.0.0",
        target_model_id="target_model",
        target_base_model_version="1.0.0",
        transfer_type=TransferType.FEATURE_EXTRACTOR_TRANSFER,
        knowledge_type=KnowledgeType.FEATURE_EXTRACTOR,
        rationale="Transfer tested feature representation",
        transfer_payload={"layers": ["layer1"], "deltas": [0.05, -0.02]},
    )

    # Instantiate transfer candidate in target domain
    candidate = service.instantiate_transfer_candidate(
        proposal_id=proposal.id,
        target_candidate_version="1.1-transfer-candidate",
        seed=123,
    )

    # Invariants Verification:
    # 1. Candidate is in target domain
    assert candidate.domain_id == "domain_target"
    assert candidate.candidate_model_id == "target_model"
    assert candidate.candidate_model_version == "1.1-transfer-candidate"
    assert candidate.status == CandidateStatus.CANDIDATE
    assert candidate.authority == "NONE"

    # 2. Candidate lineage identifies the source transfer proposal
    assert candidate.parameters.get("source_transfer_proposal_id") == proposal.id
    assert candidate.parameters.get("source_domain_id") == "domain_source"

    # 3. CRITICAL: Active target model is completely UNTOUCHED, NOT modified or activated
    active_after = service.model_registry.get_active("target_model", domain_id="domain_target")
    assert active_after is not None
    assert active_after.model_version == "1.0.0"
    assert active_after.status == ModelStatus.ACTIVE
    assert active_after.model_version != candidate.candidate_model_version


def test_transfer_decision_recording():
    """Verify recording an external transfer decision with full provenance."""
    service = AdaptiveLearningService()
    service.register_domain(LearningDomain(domain_id="domain_source"))
    service.register_domain(LearningDomain(domain_id="domain_target"))

    proposal = service.create_transfer_proposal(
        source_domain_id="domain_source",
        target_domain_id="domain_target",
        source_model_id="source_model",
        rationale="Harmonic weights transfer",
    )

    decision_rec = service.record_transfer_decision(
        proposal_id=proposal.id,
        decision="ACCEPTED",
        decider_id="domain_architect_bob",
        rationale="Passed automated target domain safety simulation",
        metadata={"review_ticket": "SEC-909"},
    )

    assert decision_rec.proposal_id == proposal.id
    assert decision_rec.decision == "ACCEPTED"
    assert decision_rec.decider_id == "domain_architect_bob"
    assert decision_rec.decision_source == "EXTERNAL"
    assert decision_rec.cognitia_authority == "NONE"

    decisions = service.list_transfer_decisions()
    assert len(decisions) == 1
    assert decisions[0].id == decision_rec.id
