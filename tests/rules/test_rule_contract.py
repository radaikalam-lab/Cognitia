"""Tests for Cognitive Rule Contract, Immutability, and Rule Store Lifecycle."""

import pytest

from cognitia.provenance.record import SourceType
from cognitia.rules.store import InMemoryRuleStore, RuleStore
from cognitia.rules.types import CognitiveRule, RuleStatus


def test_rule_creation_and_retrieval() -> None:
    store = InMemoryRuleStore()
    rule = CognitiveRule(
        rule_id="R-0042",
        version="1.0.0",
        name="Credit Check Rule",
        description="Flag credit requests if overdue invoices > 3",
        scope="erp.sales",
        predicate={"field": "customer.overdue_invoices", "op": ">", "value": 3},
        recommendation={"proposal_type": "credit_review", "action_name": "flag_credit_review"},
        rationale="High default risk detected",
        author_id="human_credit_officer",
    )

    created = store.create_rule(rule)
    assert created.rule_id == "R-0042"
    assert created.version == "1.0.0"
    assert created.status == RuleStatus.ACTIVE
    assert created.provenance.source_type == SourceType.HUMAN

    # Retrieve by ID (active)
    retrieved = store.get_rule("R-0042")
    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.description == "Flag credit requests if overdue invoices > 3"


def test_rule_immutability_duplicate_rejection() -> None:
    store = InMemoryRuleStore()
    rule1 = CognitiveRule(rule_id="R-0001", version="1.0.0", name="Rule 1")
    store.create_rule(rule1)

    # Attempting to re-register same (rule_id, version) must fail
    rule2 = CognitiveRule(rule_id="R-0001", version="1.0.0", name="Rule 1 Modified")
    with pytest.raises(ValueError, match="already exists"):
        store.create_rule(rule2)


def test_rule_supersession_lifecycle() -> None:
    store = InMemoryRuleStore()
    r_v1 = CognitiveRule(
        rule_id="R-0010",
        version="1.0.0",
        name="Lead Time Rule V1",
        predicate={"field": "lead_time_days", "op": ">", "value": 14},
    )
    store.create_rule(r_v1)

    # Supersede with V2 (lowering threshold to 10 days)
    r_v2 = CognitiveRule(
        rule_id="R-0010",
        version="2.0.0",
        name="Lead Time Rule V2",
        predicate={"field": "lead_time_days", "op": ">", "value": 10},
        rationale="Stricter procurement policy",
    )

    old_sup, new_v2 = store.supersede_rule("R-0010", r_v2, rationale="Updated threshold")

    assert old_sup.status == RuleStatus.SUPERSEDED
    assert old_sup.version == "1.0.0"
    assert new_v2.status == RuleStatus.ACTIVE
    assert new_v2.version == "2.0.0"
    assert new_v2.parent_rule_version_id == r_v1.id

    # Active lookup returns V2
    active = store.get_rule("R-0010")
    assert active is not None
    assert active.version == "2.0.0"

    # Specific version lookup still returns V1 in superseded state
    v1_retrieved = store.get_rule("R-0010", version="1.0.0")
    assert v1_retrieved is not None
    assert v1_retrieved.status == RuleStatus.SUPERSEDED

    # History preserves order
    history = store.get_rule_history("R-0010")
    assert len(history) == 2
    assert history[0].version == "1.0.0"
    assert history[1].version == "2.0.0"


def test_rule_retirement() -> None:
    store = InMemoryRuleStore()
    rule = CognitiveRule(rule_id="R-0099", version="1.0.0", name="Temporary Rule")
    store.create_rule(rule)

    retired = store.retire_rule("R-0099", rationale="Policy no longer needed")
    assert retired.status == RuleStatus.RETIRED

    # Active lookup now returns latest version if none active, with status RETIRED
    retrieved = store.get_rule("R-0099")
    assert retrieved is not None
    assert retrieved.status == RuleStatus.RETIRED


def test_list_rules_filtering() -> None:
    store = InMemoryRuleStore()
    store.create_rule(CognitiveRule(rule_id="R-1", version="1.0.0", scope="erp.sales"))
    store.create_rule(CognitiveRule(rule_id="R-2", version="1.0.0", scope="erp.procurement"))
    store.create_rule(CognitiveRule(rule_id="R-3", version="1.0.0", scope="erp.sales", status=RuleStatus.DRAFT))

    sales_active = store.list_rules(status=RuleStatus.ACTIVE, scope="erp.sales")
    assert len(sales_active) == 1
    assert sales_active[0].rule_id == "R-1"

    all_sales = store.list_rules(scope="erp.sales")
    assert len(all_sales) == 2
