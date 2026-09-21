"""Tests for Multi-Domain Cognitive Attention using Synthetic Fixtures.

Validates domain neutrality across synthetic ERP-like, AcoustiForge-like, and FJH-like scenarios.
Ensures the Attention engine operates strictly on Cognitia primitives without domain assumptions.
"""

import pytest

from cognitia.abi.types import Observation
from cognitia.attention.types import AttentionQuery, AttentionReason
from cognitia.experience.record import ExperienceBuilder
from cognitia.rules.types import CognitiveRule
from cognitia.runtime.local import LocalCognitiveRuntime


def test_synthetic_erp_domain_attention() -> None:
    runtime = LocalCognitiveRuntime()

    # Finance credit evaluation rule
    credit_rule = CognitiveRule(
        rule_id="R-ERP-CREDIT",
        version="1.0.0",
        name="Credit Evaluation Rule",
        scope="erp.sales",
        predicate={"field": "data.overdue_days", "op": ">", "value": 30},
        author_id="human_finance_lead",
    )
    runtime.rules.create_rule(credit_rule)

    # Reference observation: new sales order for customer CUST-88
    current_order = Observation(
        source_id="frappe:Sales Order:SO-002",
        payload={"data": {"customer": "CUST-88", "overdue_days": 35, "total": 25000.0}},
        created_at="2026-09-21T10:00:00Z",
        metadata={"source_application": "frappe", "subject_id": "CUST-88", "scope": "erp.sales"},
    )
    runtime.persistence.save_object(current_order)

    # Context assembly
    context = runtime.assemble_context(current_order)

    # Attention focus for rule evaluation task
    query = AttentionQuery(
        task_id="erp_credit_check",
        task_type="rule_evaluation",
        focus_subject_ids=["CUST-88"],
        maximum_items=3,
    )
    attention = runtime.focus_context(context, query)

    assert len(attention.attention_items) >= 1
    assert credit_rule.id in attention.selected_item_ids
    assert current_order.id in attention.selected_item_ids
    rule_item = attention.get_item(credit_rule.id)
    assert rule_item is not None
    assert AttentionReason.TASK_MATCH in rule_item.selection_reasons
    assert AttentionReason.RULE_RELEVANCE in rule_item.selection_reasons


def test_synthetic_acoustiforge_domain_attention() -> None:
    runtime = LocalCognitiveRuntime()

    acoustic_rule = CognitiveRule(
        rule_id="R-ACOUSTIC-01",
        version="1.0.0",
        name="Absorption Target Deviation Warning",
        scope="acoustics.optimization",
        predicate={"field": "metrics.peak_nrc_error", "op": ">", "value": 0.05},
        author_id="human_acoustician",
    )
    runtime.rules.create_rule(acoustic_rule)

    past_exp = (
        ExperienceBuilder(source_application="acoustiforge", episode_id="SIM-101")
        .with_metadata("source_application", "acoustiforge")
        .with_metadata("subject_id", "PANEL-DESIGN-X")
        .build()
    )
    runtime.persistence.save_object(past_exp)

    current_sim = Observation(
        source_id="acoustiforge:solver:run_404",
        payload={
            "design_id": "PANEL-DESIGN-X",
            "metrics": {"peak_nrc_error": 0.08, "alpha_avg": 0.82},
            "parameters": {"thickness_mm": 50, "flow_resistivity": 24000},
        },
        created_at="2026-09-21T14:30:00Z",
        metadata={"source_application": "acoustiforge", "subject_id": "PANEL-DESIGN-X", "scope": "acoustics.optimization"},
    )
    runtime.persistence.save_object(current_sim)

    context = runtime.assemble_context(current_sim)

    query = AttentionQuery(
        task_id="acoustic_anomaly_focus",
        task_type="anomaly_investigation",
        focus_subject_ids=["PANEL-DESIGN-X"],
        maximum_items=3,
    )
    attention = runtime.focus_context(context, query)

    assert len(attention.attention_items) >= 1
    assert current_sim.id in attention.selected_item_ids
    obs_item = attention.get_item(current_sim.id)
    assert obs_item is not None
    assert AttentionReason.REFERENCE_ITEM in obs_item.selection_reasons
    assert AttentionReason.SUBJECT_MATCH in obs_item.selection_reasons


def test_synthetic_fjh_domain_attention() -> None:
    runtime = LocalCognitiveRuntime()

    fjh_rule = CognitiveRule(
        rule_id="R-FJH-ENERGY",
        version="1.0.0",
        name="High Energy Discharge Inspection",
        scope="fjh.experiment",
        predicate={"field": "pulse_energy_kj", "op": ">", "value": 5.0},
        author_id="human_plasma_physicist",
    )
    runtime.rules.create_rule(fjh_rule)

    discharge_obs = Observation(
        source_id="fjh_lab:chamber_alpha:shot_99",
        payload={
            "material": "CARBON-GRAPHITE-SAMPLE-3",
            "pulse_energy_kj": 6.2,
            "voltage_v": 2400.0,
            "duration_ms": 10.5,
        },
        created_at="2026-09-21T16:00:00Z",
        metadata={"source_application": "fjh_lab", "subject_id": "CARBON-GRAPHITE-SAMPLE-3", "scope": "fjh.experiment"},
    )
    runtime.persistence.save_object(discharge_obs)

    context = runtime.assemble_context(discharge_obs)

    query = AttentionQuery(
        task_id="fjh_high_energy_focus",
        task_type="rule_evaluation",
        focus_subject_ids=["CARBON-GRAPHITE-SAMPLE-3"],
        maximum_items=2,
    )
    attention = runtime.focus_context(context, query)

    assert len(attention.attention_items) == 2
    assert fjh_rule.id in attention.selected_item_ids
    assert discharge_obs.id in attention.selected_item_ids
