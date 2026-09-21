"""Tests for Cognitive Rule Evaluation Capability and Predicate Matching."""

import pytest

from cognitia.abi.types import Observation
from cognitia.provenance.record import SourceType
from cognitia.rules.capability import RuleEvaluationCapability, evaluate_predicate
from cognitia.rules.store import InMemoryRuleStore
from cognitia.rules.types import CognitiveRule, RuleStatus


def test_evaluate_predicate_operations() -> None:
    payload = {
        "customer": {
            "name": "Acme Corp",
            "overdue_invoices": 4,
            "rating": "B",
        },
        "items": ["ITEM-A", "ITEM-B"],
        "total_amount": 15000.0,
    }

    # Direct nested equality
    assert evaluate_predicate({"customer.name": "Acme Corp"}, payload) is True
    assert evaluate_predicate({"customer.name": "Other Corp"}, payload) is False

    # Comparison >
    assert evaluate_predicate({"field": "customer.overdue_invoices", "op": ">", "value": 3}, payload) is True
    assert evaluate_predicate({"field": "customer.overdue_invoices", "op": ">", "value": 5}, payload) is False

    # Comparison <=
    assert evaluate_predicate({"field": "total_amount", "op": "<=", "value": 20000.0}, payload) is True

    # Compound 'all'
    pred_all = {
        "all": [
            {"field": "customer.overdue_invoices", "op": ">", "value": 2},
            {"field": "total_amount", "op": ">", "value": 10000.0},
        ]
    }
    assert evaluate_predicate(pred_all, payload) is True

    # Compound 'any'
    pred_any = {
        "any": [
            {"field": "customer.rating", "op": "==", "value": "A"},
            {"field": "customer.rating", "op": "==", "value": "B"},
        ]
    }
    assert evaluate_predicate(pred_any, payload) is True


def test_rule_evaluation_decision_provenance() -> None:
    store = InMemoryRuleStore()
    rule = CognitiveRule(
        rule_id="R-0042",
        version="1.0.0",
        name="Credit Risk Flag",
        description="Flag credit requests when overdue invoices exceed 3",
        scope="erp.sales",
        predicate={"field": "customer.overdue_invoices", "op": ">", "value": 3},
        recommendation={
            "proposal_type": "credit_review_advisory",
            "action_name": "flag_credit_review",
            "parameters": {"risk_level": "high"},
        },
        rationale="Overdue invoices exceed acceptable credit threshold",
        confidence=0.95,
        author_id="human_credit_risk_expert",
    )
    store.create_rule(rule)

    capability = RuleEvaluationCapability(rule_store=store)

    obs = Observation(
        source_id="frappe:Sales Order:SO-001",
        payload={
            "customer": {"name": "Test Cust", "overdue_invoices": 5},
            "doc_name": "SO-001",
        },
        metadata={"scope": "erp.sales"},
    )

    decision = capability.propose_decision(obs, context={"scope": "erp.sales"})

    assert decision.proposal_type == "credit_review_advisory"
    assert decision.proposed_action.name == "flag_credit_review"
    assert decision.confidence == 0.95
    assert "Rule R-0042 (v1.0.0) triggered" in decision.rationale
    assert decision.metadata["triggered_rule_id"] == "R-0042"
    assert decision.metadata["rule_version"] == "1.0.0"
    assert decision.metadata["input_observation_ids"] == [obs.id]

    # Provenance check
    prov = decision.provenance
    assert prov is not None
    assert prov.source_type == SourceType.DETERMINISTIC_RULE
    assert obs.id in prov.parent_ids
    assert rule.id in prov.parent_ids
    assert prov.is_deterministic is True


def test_rule_evaluation_no_match_returns_neutral() -> None:
    store = InMemoryRuleStore()
    rule = CognitiveRule(
        rule_id="R-0042",
        version="1.0.0",
        predicate={"field": "customer.overdue_invoices", "op": ">", "value": 10},
    )
    store.create_rule(rule)

    capability = RuleEvaluationCapability(rule_store=store)
    obs = Observation(
        source_id="frappe:Sales Order:SO-002",
        payload={"customer": {"overdue_invoices": 1}},
    )

    decision = capability.propose_decision(obs)
    assert decision.proposal_type == "neutral_advisory"
    assert decision.proposed_action.name == "no_advisory_flag"
    assert decision.metadata["input_observation_ids"] == [obs.id]
