"""Tests for AL2 Domain Isolation across all learning operations."""

import pytest
from cognitia.abi.types import Observation
from cognitia.learning.contract import (
    AdaptiveLearningFailure,
    LearningDomain,
    OutcomeRecord,
)
from cognitia.learning.service import AdaptiveLearningService
from cognitia.models.registry import InMemoryModelRegistry, ModelRecord, ModelStatus


def test_multi_domain_registration_and_listing():
    """Verify explicit domain registration and scoped retrieval."""
    service = AdaptiveLearningService()

    domain_a = LearningDomain(
        domain_id="domain_alpha",
        domain_version="1.0.0",
        description="Alpha sensor domain",
        declared_providers=["laya"],
    )
    domain_b = LearningDomain(
        domain_id="domain_beta",
        domain_version="1.0.0",
        description="Beta sensor domain",
        declared_providers=["laya"],
    )

    service.register_domain(domain_a)
    service.register_domain(domain_b)

    domains = service.list_domains()
    domain_ids = [d.domain_id for d in domains]
    assert "default" in domain_ids
    assert "domain_alpha" in domain_ids
    assert "domain_beta" in domain_ids

    assert service.get_domain("domain_alpha").description == "Alpha sensor domain"
    assert service.get_domain("domain_beta").description == "Beta sensor domain"


def test_domain_scoped_models_in_registry():
    """Verify model registry stores and retrieves models scoped by domain."""
    registry = InMemoryModelRegistry()

    m_alpha = ModelRecord(
        model_id="alpha_model",
        model_version="1.0.0",
        domain_id="domain_alpha",
        provider="laya",
        status=ModelStatus.ACTIVE,
    )
    m_beta = ModelRecord(
        model_id="beta_model",
        model_version="1.0.0",
        domain_id="domain_beta",
        provider="laya",
        status=ModelStatus.ACTIVE,
    )

    registry.register(m_alpha)
    registry.register(m_beta)

    alpha_models = registry.list_by_domain("domain_alpha")
    assert len(alpha_models) == 1
    assert alpha_models[0].model_id == "alpha_model"

    beta_models = registry.list_by_domain("domain_beta")
    assert len(beta_models) == 1
    assert beta_models[0].model_id == "beta_model"

    assert registry.get_active("alpha_model", domain_id="domain_alpha") is not None
    assert registry.get_active("alpha_model", domain_id="domain_beta") is None


def test_cross_domain_feedback_isolation():
    """Verify that feedback computation rejects mixing predictions and outcomes from different domains."""
    service = AdaptiveLearningService()

    service.register_domain(LearningDomain(domain_id="domain_alpha"))
    service.register_domain(LearningDomain(domain_id="domain_beta"))

    service.register_model(
        ModelRecord(
            model_id="model_alpha",
            model_version="1.0.0",
            domain_id="domain_alpha",
            provider="laya",
            status=ModelStatus.ACTIVE,
        )
    )
    service.register_model(
        ModelRecord(
            model_id="model_beta",
            model_version="1.0.0",
            domain_id="domain_beta",
            provider="laya",
            status=ModelStatus.ACTIVE,
        )
    )

    # Predict in Alpha
    obs_alpha = Observation(source_id="alpha_sensor", payload={"spl_db": 82.0})
    pred_alpha = service.predict_from_observation(obs_alpha, model_id="model_alpha", domain_id="domain_alpha")
    assert pred_alpha.domain_id == "domain_alpha"

    # Outcome in Beta (mismatched domain)
    outcome_beta = OutcomeRecord(
        domain_id="domain_beta",
        source_id="beta_sensor",
        target_prediction_id=pred_alpha.id,
        actual_values={"label": "resonance"},
    )
    service.record_outcome(outcome_beta)

    # Attempting to create feedback across domains must fail closed
    with pytest.raises(AdaptiveLearningFailure, match="Domain mismatch.*Cross-domain feedback is forbidden"):
        service.create_feedback_from_outcome(
            prediction_id=pred_alpha.id,
            outcome=outcome_beta,
            domain_id="domain_alpha",
        )


def test_domain_scoped_learning_and_candidates():
    """Verify candidates and evaluations remain strictly within their registered domain."""
    service = AdaptiveLearningService()
    service.register_domain(LearningDomain(domain_id="domain_alpha"))

    service.register_model(
        ModelRecord(
            model_id="model_alpha",
            model_version="1.0.0",
            domain_id="domain_alpha",
            provider="laya",
            status=ModelStatus.ACTIVE,
        )
    )

    obs = Observation(source_id="alpha_sensor", payload={"spl_db": 88.0})
    pred = service.predict_from_observation(obs, model_id="model_alpha", domain_id="domain_alpha")

    outcome = OutcomeRecord(
        domain_id="domain_alpha",
        source_id="alpha_sensor",
        target_prediction_id=pred.id,
        actual_values={"label": "resonance"},
    )
    service.record_outcome(outcome)

    fb = service.create_feedback_from_outcome(prediction_id=pred.id, outcome=outcome, domain_id="domain_alpha")

    candidate, update, event = service.learn_from_feedback(
        feedback_ids=[fb.id],
        base_model_id="model_alpha",
        domain_id="domain_alpha",
        seed=42,
    )

    assert candidate.domain_id == "domain_alpha"
    assert update.domain_id == "domain_alpha"
    assert event.domain_id == "domain_alpha"

    # Scoped candidate listing
    alpha_cands = service.list_candidates(domain_id="domain_alpha")
    assert len(alpha_cands) == 1
    assert alpha_cands[0].id == candidate.id

    beta_cands = service.list_candidates(domain_id="domain_beta")
    assert len(beta_cands) == 0
