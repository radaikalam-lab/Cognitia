"""Tests for Human-Governed Plasticity and Anti-Silent-Mutation Invariants."""

import pytest

from cognitia.abi.types import Observation
from cognitia.provenance.record import SourceType
from cognitia.rules.capability import RuleEvaluationCapability
from cognitia.rules.store import InMemoryRuleStore
from cognitia.rules.types import CognitiveRule, RuleStatus


def test_human_governed_plasticity_version_preservation() -> None:
    store = InMemoryRuleStore()

    # Step 1: Human defines initial cognitive rule V1
    v1_rule = CognitiveRule(
        rule_id="R-0050",
        version="1.0.0",
        name="Lead Time Heuristic",
        predicate={"field": "supplier_lead_time_days", "op": ">", "value": 20},
        recommendation={"action_name": "warn_long_lead_time"},
        rationale="Historical delivery delays from remote suppliers",
        author_id="human_procurement_expert",
    )
    store.create_rule(v1_rule)

    v1_initial_id = v1_rule.id
    v1_initial_version = v1_rule.version

    # Step 2: Human observes new business dynamics and updates threshold in V2
    v2_rule = CognitiveRule(
        rule_id="R-0050",
        version="2.0.0",
        name="Lead Time Heuristic V2",
        predicate={"field": "supplier_lead_time_days", "op": ">", "value": 15},
        recommendation={"action_name": "warn_long_lead_time"},
        rationale="Updated supplier SLA benchmarks",
        author_id="human_procurement_expert",
    )
    old_superseded, new_active = store.supersede_rule("R-0050", v2_rule, rationale="Stricter SLA")

    # Invariant: V1 remains immutable and preserved in history
    assert old_superseded.id == v1_initial_id
    assert old_superseded.version == v1_initial_version
    assert old_superseded.status == RuleStatus.SUPERSEDED

    # Invariant: V2 is a distinct cognitive object
    assert new_active.id != v1_initial_id
    assert new_active.version == "2.0.0"
    assert new_active.status == RuleStatus.ACTIVE
    assert new_active.parent_rule_version_id == v1_initial_id

    # Retrieve history confirms both versions exist
    history = store.get_rule_history("R-0050")
    assert len(history) == 2
    assert history[0].version == "1.0.0"
    assert history[0].status == RuleStatus.SUPERSEDED
    assert history[1].version == "2.0.0"
    assert history[1].status == RuleStatus.ACTIVE


def test_runtime_observation_does_not_mutate_rules() -> None:
    store = InMemoryRuleStore()
    rule = CognitiveRule(
        rule_id="R-0077",
        version="1.0.0",
        name="Supplier Anomaly Rule",
        predicate={"field": "defect_rate", "op": ">", "value": 0.05},
        author_id="human_qa_manager",
    )
    store.create_rule(rule)

    capability = RuleEvaluationCapability(rule_store=store)

    # Simulate 100 runtime observations passing through the capability
    for i in range(100):
        obs = Observation(
            source_id=f"frappe:ItemInspection:INSP-{i}",
            payload={"defect_rate": 0.08 + (i * 0.001)},
        )
        decision = capability.propose_decision(obs)
        assert decision.proposal_type is not None

    # Invariant: Rule in store MUST remain exactly identical in version, predicate, and status
    current_rule = store.get_rule("R-0077")
    assert current_rule is not None
    assert current_rule.version == "1.0.0"
    assert current_rule.status == RuleStatus.ACTIVE
    assert current_rule.predicate == {"field": "defect_rate", "op": ">", "value": 0.05}
    assert len(store.get_rule_history("R-0077")) == 1
