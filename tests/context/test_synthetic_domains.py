"""Tests for Multi-Domain Cognitive Context Assembly using Synthetic Fixtures.

Validates domain neutrality across synthetic ERP-like, AcoustiForge-like, and FJH-like scenarios.
"""

import pytest

from cognitia.abi.types import Observation
from cognitia.context.types import ContextQuery, RelevanceReason
from cognitia.experience.record import ExperienceBuilder
from cognitia.rules.types import CognitiveRule
from cognitia.runtime.local import LocalCognitiveRuntime


def test_synthetic_erp_domain_context() -> None:
    runtime = LocalCognitiveRuntime()

    # Rule: credit risk flag
    credit_rule = CognitiveRule(
        rule_id="R-ERP-CREDIT",
        version="1.0.0",
        name="Credit Evaluation Rule",
        scope="erp.sales",
        predicate={"field": "data.overdue_days", "op": ">", "value": 30},
        author_id="human_finance_lead",
    )
    runtime.rules.create_rule(credit_rule)

    # Previous historical orders for customer CUST-88
    past_order = Observation(
        source_id="frappe:Sales Order:SO-001",
        payload={"data": {"customer": "CUST-88", "overdue_days": 45, "total": 12000.0}},
        created_at="2026-09-21T09:00:00Z",
        metadata={"source_application": "frappe", "subject_id": "CUST-88", "scope": "erp.sales"},
    )
    runtime.persistence.save_object(past_order)

    # Reference observation: new sales order for CUST-88
    current_order = Observation(
        source_id="frappe:Sales Order:SO-002",
        payload={"data": {"customer": "CUST-88", "overdue_days": 35, "total": 25000.0}},
        created_at="2026-09-21T10:00:00Z",
        metadata={"source_application": "frappe", "subject_id": "CUST-88", "scope": "erp.sales"},
    )
    runtime.persistence.save_object(current_order)

    context = runtime.assemble_context(current_order)

    assert context.reference_subject_id == "CUST-88"
    assert "R-ERP-CREDIT" in context.active_rule_ids
    assert past_order.id in context.related_observation_ids


def test_synthetic_acoustiforge_domain_context() -> None:
    runtime = LocalCognitiveRuntime()

    # Heuristic rule for acoustic target convergence
    acoustic_rule = CognitiveRule(
        rule_id="R-ACOUSTIC-01",
        version="1.0.0",
        name="Absorption Target Deviation Warning",
        scope="acoustics.optimization",
        predicate={"field": "metrics.peak_nrc_error", "op": ">", "value": 0.05},
        author_id="human_acoustician",
    )
    runtime.rules.create_rule(acoustic_rule)

    # Past optimization experience
    past_exp = (
        ExperienceBuilder(source_application="acoustiforge", episode_id="SIM-101")
        .with_metadata("source_application", "acoustiforge")
        .with_metadata("subject_id", "PANEL-DESIGN-X")
        .build()
    )
    runtime.persistence.save_object(past_exp)

    # Reference observation: optimization run completed
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

    assert context.reference_subject_id == "PANEL-DESIGN-X"
    assert "R-ACOUSTIC-01" in context.active_rule_ids
    assert past_exp.id in context.related_experience_ids


def test_synthetic_fjh_domain_context() -> None:
    runtime = LocalCognitiveRuntime()

    # Flash Joule Heating safety / parameters cognitive rule
    fjh_rule = CognitiveRule(
        rule_id="R-FJH-ENERGY",
        version="1.0.0",
        name="High Energy Discharge Inspection",
        scope="fjh.experiment",
        predicate={"field": "pulse_energy_kj", "op": ">", "value": 5.0},
        author_id="human_plasma_physicist",
    )
    runtime.rules.create_rule(fjh_rule)

    # Reference observation: pulse discharge completed
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

    assert context.reference_subject_id == "CARBON-GRAPHITE-SAMPLE-3"
    assert "R-FJH-ENERGY" in context.active_rule_ids
    assert context.metadata["source_application"] == "fjh_lab"
