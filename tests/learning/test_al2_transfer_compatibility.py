"""Tests for AL2 Transfer Compatibility Evaluation."""

import pytest
from cognitia.learning.contract import (
    KnowledgeType,
    LearningDomain,
    LearningTransferProposal,
    TransferCompatibilityStatus,
    TransferType,
)
from cognitia.learning.service import AdaptiveLearningService
from cognitia.learning.transfer import LearningTransferEngine


def test_transfer_compatibility_evaluation_compatible():
    """Verify compatible status when domain representations and providers match."""
    service = AdaptiveLearningService()
    service.register_domain(
        LearningDomain(
            domain_id="domain_alpha",
            representation_version="1.0.0",
            declared_providers=["laya"],
        )
    )
    service.register_domain(
        LearningDomain(
            domain_id="domain_beta",
            representation_version="1.0.0",
            declared_providers=["laya"],
        )
    )

    proposal = service.create_transfer_proposal(
        source_domain_id="domain_alpha",
        target_domain_id="domain_beta",
        source_model_id="alpha_model",
        transfer_type=TransferType.FEATURE_EXTRACTOR_TRANSFER,
        knowledge_type=KnowledgeType.FEATURE_EXTRACTOR,
        transfer_payload={"layers": ["enc1", "enc2"]},
    )

    result = service.evaluate_transfer_compatibility(proposal)
    assert result.status in (TransferCompatibilityStatus.COMPATIBLE, TransferCompatibilityStatus.PARTIALLY_COMPATIBLE)
    assert result.score > 0.7
    assert result.authority == "NONE"
    assert result.compatibility_details["source_domain_id"] == "domain_alpha"
    assert result.compatibility_details["target_domain_id"] == "domain_beta"


def test_transfer_compatibility_representation_mismatch():
    """Verify incompatible evaluation on representation version mismatch."""
    service = AdaptiveLearningService()
    service.register_domain(
        LearningDomain(
            domain_id="domain_v1",
            representation_version="1.0.0",
            declared_providers=["laya"],
        )
    )
    service.register_domain(
        LearningDomain(
            domain_id="domain_v2",
            representation_version="2.0.0",
            declared_providers=["laya"],
        )
    )

    proposal = service.create_transfer_proposal(
        source_domain_id="domain_v1",
        target_domain_id="domain_v2",
        source_model_id="source_model",
        transfer_type=TransferType.FEATURE_EXTRACTOR_TRANSFER,
        knowledge_type=KnowledgeType.FEATURE_EXTRACTOR,
    )

    result = service.evaluate_transfer_compatibility(proposal)
    assert result.status == TransferCompatibilityStatus.INCOMPATIBLE
    assert any("representation" in r.lower() for r in result.risks)
    assert result.authority == "NONE"


def test_provider_declaration_alone_not_proof_of_compatibility():
    """Verify that provider declaration alone does NOT make a transfer compatible."""
    # When payload or representations are incompatible, provider declaration must not blindly approve
    engine = LearningTransferEngine()
    source_domain = LearningDomain(
        domain_id="source_dom",
        representation_version="1.0.0",
        declared_providers=["laya"],
    )
    target_domain = LearningDomain(
        domain_id="target_dom",
        representation_version="9.9.9",  # Completely incompatible representation
        declared_providers=["laya"],      # Declared provider matches
    )

    proposal = LearningTransferProposal(
        source_domain_id="source_dom",
        target_domain_id="target_dom",
        source_model_id="source_model",
        transfer_type=TransferType.WEIGHT_INITIALIZATION,
        knowledge_type=KnowledgeType.MODEL_WEIGHTS,
        transfer_payload={},
    )

    result = engine.evaluate_compatibility(proposal, source_domain, target_domain)
    # Must NOT be COMPATIBLE simply because both declare "laya"
    assert result.status == TransferCompatibilityStatus.INCOMPATIBLE
    assert result.score < 0.5
    assert len(result.risks) > 0
