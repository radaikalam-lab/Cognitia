"""Tests for AL2 Domain Contracts and Authority Invariants."""

import pytest
from cognitia.learning.contract import (
    KnowledgeType,
    LearningDomain,
    LearningTransferProposal,
    ModelCandidate,
    ModelPromotionProposal,
    TransferCompatibilityResult,
    TransferCompatibilityStatus,
    TransferDecisionRecord,
    TransferType,
)


def test_learning_domain_scope_contract():
    """Verify that LearningDomain represents scope/metadata and does not require authority='NONE'."""
    domain = LearningDomain(
        domain_id="domain_acoustic_lab",
        domain_version="1.2.0",
        description="Acoustic sensor analytics domain",
        representation_version="1.0.0",
        declared_providers=["laya"],
        metadata={"facility": "Bldg-4"},
    )
    assert domain.domain_id == "domain_acoustic_lab"
    assert domain.domain_version == "1.2.0"
    assert domain.description == "Acoustic sensor analytics domain"
    assert domain.representation_version == "1.0.0"
    assert domain.declared_providers == ["laya"]
    assert domain.metadata["facility"] == "Bldg-4"
    # LearningDomain is scope metadata, not an execution authority artifact


def test_transfer_proposal_authority_invariant():
    """Verify that LearningTransferProposal strictly enforces authority='NONE'."""
    proposal = LearningTransferProposal(
        source_domain_id="domain_a",
        target_domain_id="domain_b",
        source_model_id="acoustic_v1",
        transfer_type=TransferType.FEATURE_EXTRACTOR_TRANSFER,
        knowledge_type=KnowledgeType.FEATURE_EXTRACTOR,
        rationale="Transfer harmonic feature extractor",
    )
    assert proposal.authority == "NONE"

    # Must reject any attempt to grant authority on proposal
    with pytest.raises(ValueError, match="authority.*NONE"):
        LearningTransferProposal(
            source_domain_id="domain_a",
            target_domain_id="domain_b",
            source_model_id="acoustic_v1",
            authority="FULL_AUTHORITY",
        )


def test_transfer_compatibility_result_authority_invariant():
    """Verify that TransferCompatibilityResult strictly enforces authority='NONE'."""
    result = TransferCompatibilityResult(
        proposal_id="prop_001",
        source_domain_id="domain_a",
        target_domain_id="domain_b",
        status=TransferCompatibilityStatus.COMPATIBLE,
        score=0.92,
        advisory_recommendation="Safe for target candidate creation",
    )
    assert result.authority == "NONE"

    with pytest.raises(ValueError, match="authority.*NONE"):
        TransferCompatibilityResult(
            proposal_id="prop_001",
            source_domain_id="domain_a",
            target_domain_id="domain_b",
            status=TransferCompatibilityStatus.COMPATIBLE,
            authority="APPROVED",
        )


def test_target_candidate_and_promotion_authority_invariants():
    """Verify that ModelCandidate and ModelPromotionProposal retain authority='NONE'."""
    candidate = ModelCandidate(
        candidate_model_id="candidate_b",
        candidate_model_version="1.1-transferred",
        parent_model_id="base_b",
        domain_id="domain_b",
        parameter_fingerprint="fp_abc123",
    )
    assert candidate.authority == "NONE"

    prop = ModelPromotionProposal(
        candidate_model_id="candidate_b",
        candidate_model_version="1.1-transferred",
        parent_model_id="base_b",
        domain_id="domain_b",
        rationale="Superior performance",
    )
    assert prop.authority == "NONE"


def test_transfer_decision_record_external_provenance():
    """Verify TransferDecisionRecord distinguishes external decider and cognitia_authority='NONE'."""
    decision = TransferDecisionRecord(
        proposal_id="prop_001",
        decision="ACCEPTED",
        decider_id="domain_lead_alice",
        decision_source="EXTERNAL",
        rationale="Validated on target hardware",
    )
    assert decision.decision == "ACCEPTED"
    assert decision.decider_id == "domain_lead_alice"
    assert decision.decision_source == "EXTERNAL"
    assert decision.cognitia_authority == "NONE"

    with pytest.raises(ValueError, match="cognitia_authority.*NONE"):
        TransferDecisionRecord(
            proposal_id="prop_001",
            decision="ACCEPTED",
            decider_id="domain_lead_alice",
            cognitia_authority="AUTONOMOUS",
        )
