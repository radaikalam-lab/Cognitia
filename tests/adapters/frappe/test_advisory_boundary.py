"""Tests for Frappe Advisory Presentation and Authority Boundary Enforcement."""

import copy
import pytest

from cognitia.runtime.local import LocalCognitiveRuntime
from adapters.frappe.advisory import FrappeAdvisory
from adapters.frappe.client import FrappeCognitiaAdapter
from adapters.frappe.events import FrappeEvent, FrappeEventType


def test_advisory_generation_and_strict_non_authority() -> None:
    runtime = LocalCognitiveRuntime()
    adapter = FrappeCognitiaAdapter(runtime=runtime)

    # Human creates a credit review cognitive rule
    adapter.create_human_rule(
        rule_id="R-ERP-001",
        name="Overdue Invoices Warning",
        description="Warn if customer has more than 2 overdue invoices",
        scope="erp.sales_order",
        predicate={"field": "data.customer_overdue_invoices", "op": ">", "value": 2},
        recommendation={
            "proposal_type": "credit_risk_advisory",
            "action_name": "request_credit_manager_review",
            "parameters": {"risk_level": "elevated"},
        },
        rationale="Historical default pattern for customers with >2 overdue invoices",
        author_id="human_risk_officer",
    )

    # Ingest some historical background
    adapter.ingest_event(
        FrappeEvent(
            event_type=FrappeEventType.SALES_ORDER_SUBMITTED,
            doc_type="Sales Order",
            doc_name="SO-OLD-01",
            payload={"customer": "CUST-RISKY", "customer_overdue_invoices": 3},
            subject_id="CUST-RISKY",
        )
    )

    # Simulated Frappe Document (Sales Order)
    frappe_doc_state = {
        "customer": "CUST-RISKY",
        "customer_overdue_invoices": 4,
        "grand_total": 50000.0,
        "docstatus": 0,  # Draft
        "workflow_state": "Pending Approval",
    }
    # Deepcopy to verify non-mutation invariant
    original_state_copy = copy.deepcopy(frappe_doc_state)

    # Request advisory from Cognitia
    advisory = adapter.get_advisory(
        doc_type="Sales Order",
        doc_name="SO-2026-00099",
        payload=frappe_doc_state,
        subject_id="CUST-RISKY",
    )

    assert isinstance(advisory, FrappeAdvisory)
    assert advisory.is_authoritative is False
    assert advisory.triggered_rule_id == "R-ERP-001"
    assert advisory.triggered_rule_version == "1.0.0"
    assert advisory.confidence == 1.0
    assert "request_credit_manager_review" in advisory.recommendation

    # AUTHORITY BOUNDARY VERIFICATION:
    # Cognitia MUST NOT have modified frappe_doc_state
    assert frappe_doc_state == original_state_copy
    assert frappe_doc_state["docstatus"] == 0
    assert frappe_doc_state["workflow_state"] == "Pending Approval"
    assert frappe_doc_state["grand_total"] == 50000.0


def test_superseded_human_rule_updates_advisory_without_affecting_history() -> None:
    runtime = LocalCognitiveRuntime()
    adapter = FrappeCognitiaAdapter(runtime=runtime)

    # Rule V1: threshold = 5
    adapter.create_human_rule(
        rule_id="R-LEAD-01",
        version="1.0.0",
        name="Supplier Lead Time Advisory",
        description="Warn if supplier lead time > 5 days",
        scope="erp.purchase_order",
        predicate={"field": "data.lead_time_days", "op": ">", "value": 5},
        recommendation={"action_name": "flag_supplier_lead_time"},
    )

    # With lead_time_days = 4, V1 should NOT trigger
    po_data = {"supplier": "SUPP-01", "lead_time_days": 4}
    advisory1 = adapter.get_advisory(
        doc_type="Purchase Order",
        doc_name="PO-001",
        payload=po_data,
        subject_id="SUPP-01",
    )
    assert advisory1.triggered_rule_id is None

    # Human supersedes to V2: threshold lowered to 3 days
    adapter.supersede_human_rule(
        rule_id="R-LEAD-01",
        new_version="2.0.0",
        predicate={"field": "data.lead_time_days", "op": ">", "value": 3},
        recommendation={"action_name": "flag_supplier_lead_time"},
        rationale="Stricter procurement SLA",
    )

    # With lead_time_days = 4, V2 SHOULD trigger
    advisory2 = adapter.get_advisory(
        doc_type="Purchase Order",
        doc_name="PO-001",
        payload=po_data,
        subject_id="SUPP-01",
    )
    assert advisory2.triggered_rule_id == "R-LEAD-01"
    assert advisory2.triggered_rule_version == "2.0.0"

    # History verification
    history = runtime.rules.get_rule_history("R-LEAD-01")
    assert len(history) == 2
    assert history[0].version == "1.0.0"
    assert history[1].version == "2.0.0"
