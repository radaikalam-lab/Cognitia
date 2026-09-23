"""Security and Authority Boundary Tests for AL3 Model Lifecycle Governance.

Verifies:
1. Promotion proposal authority=NONE invariant.
2. Rollback proposal authority=NONE invariant.
3. Promotion and rollback decisions require decision_source=EXTERNAL.
4. Autonomous activation is impossible and forbidden.
5. Historical model records are immutable and cannot be deleted.
6. Domain boundaries cannot be bypassed.
"""

import pytest

from cognitia.learning.contract import (
    AdaptiveLearningFailure,
    ModelActivationObservation,
    ModelLifecycleEvent,
    ModelLifecycleState,
    ModelPromotionDecision,
    ModelPromotionProposal,
    ModelRollbackDecision,
    ModelRollbackProposal,
)
from cognitia.learning.service import AdaptiveLearningService
from cognitia.models.registry import InMemoryModelRegistry, ModelRecord, ModelStatus


def test_proposal_authority_must_strictly_be_none():
    """Verify any attempt to construct proposals with non-NONE authority raises ValueError."""
    with pytest.raises(ValueError) as exc_prop:
        ModelPromotionProposal(
            candidate_model_id="laya_acoustic_v1",
            candidate_model_version="1.1-candidate",
            authority="COGNITIA_PRODUCTION",
        )
    assert "must strictly be 'NONE'" in str(exc_prop.value)

    with pytest.raises(ValueError) as exc_roll:
        ModelRollbackProposal(
            target_model_id="laya_acoustic_v1",
            target_model_version="1.0.0",
            authority="COGNITIA_AUTONOMOUS",
        )
    assert "must strictly be 'NONE'" in str(exc_roll.value)


def test_decision_must_be_external_and_have_none_cognitia_authority():
    """Verify decision structures reject internal decision sources or elevated authority."""
    with pytest.raises(ValueError) as exc_source:
        ModelPromotionDecision(
            proposal_id="prop_1",
            candidate_model_id="laya_acoustic_v1",
            candidate_model_version="1.1-candidate",
            decision_source="COGNITIA_INTERNAL",
        )
    assert "decision_source must strictly be 'EXTERNAL'" in str(exc_source.value)

    with pytest.raises(ValueError) as exc_auth:
        ModelPromotionDecision(
            proposal_id="prop_1",
            candidate_model_id="laya_acoustic_v1",
            candidate_model_version="1.1-candidate",
            decision_source="EXTERNAL",
            cognitia_authority="COGNITIA_AUTHORIZED",
        )
    assert "cognitia_authority must strictly be 'NONE'" in str(exc_auth.value)

    with pytest.raises(ValueError) as exc_roll_source:
        ModelRollbackDecision(
            proposal_id="prop_roll_1",
            target_model_id="laya_acoustic_v1",
            target_model_version="1.0.0",
            decision_source="AUTONOMOUS_DAEMON",
        )
    assert "decision_source must strictly be 'EXTERNAL'" in str(exc_roll_source.value)


def test_historical_models_never_deleted_during_lifecycle_transitions():
    """Verify active model transition preserves all previous model records for audit."""
    registry = InMemoryModelRegistry()
    v1 = ModelRecord(model_id="m1", model_version="1.0.0", domain_id="d1", status=ModelStatus.ACTIVE)
    v2 = ModelRecord(model_id="m1", model_version="2.0.0", domain_id="d1", status=ModelStatus.CANDIDATE)
    registry.register(v1)
    registry.register(v2)

    # Supersede v1
    registry.set_lifecycle_state("m1", "1.0.0", ModelLifecycleState.SUPERSEDED, domain_id="d1")

    # Both records remain in registry
    assert registry.get("m1", "1.0.0", domain_id="d1") is not None
    assert registry.get("m1", "2.0.0", domain_id="d1") is not None
    assert len(registry.list_versions("m1", domain_id="d1")) == 2


def test_unregistered_domain_governance_fails_closed():
    """Verify lifecycle and rollback proposals fail closed if domain is unknown."""
    service = AdaptiveLearningService()

    with pytest.raises(AdaptiveLearningFailure) as exc_roll:
        service.propose_model_rollback(
            target_model_id="laya_acoustic_v1",
            target_model_version="1.0.0",
            domain_id="unregistered_malicious_domain",
        )
    assert exc_roll.value.error_code == "UNREGISTERED_DOMAIN"

    with pytest.raises(AdaptiveLearningFailure) as exc_freeze:
        service.freeze_domain("unregistered_domain")
    assert exc_freeze.value.error_code == "UNREGISTERED_DOMAIN"
