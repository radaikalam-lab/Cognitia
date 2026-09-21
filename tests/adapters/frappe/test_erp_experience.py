"""Tests for ERP Lifecycle Experience Formation and Cross-Document Correlation."""

import pytest

from cognitia.experience.record import ExperienceRecord
from cognitia.provenance.record import SourceType
from adapters.frappe.events import FrappeEvent, FrappeEventType
from adapters.frappe.experience import ERPLifecycleType, FrappeExperienceBuilder
from adapters.frappe.translator import FrappeEventTranslator


def test_sales_lifecycle_experience_aggregation() -> None:
    # 1. Quotation
    e1 = FrappeEvent(
        event_type=FrappeEventType.QUOTATION_SUBMITTED,
        doc_type="Quotation",
        doc_name="QTN-001",
        payload={"customer": "CUST-001", "items": [{"item_code": "ITEM-A", "qty": 10}]},
    )
    # 2. Sales Order
    e2 = FrappeEvent(
        event_type=FrappeEventType.SALES_ORDER_SUBMITTED,
        doc_type="Sales Order",
        doc_name="SO-001",
        payload={"customer": "CUST-001", "quotation": "QTN-001", "items": [{"item_code": "ITEM-A", "qty": 10}]},
    )
    # 3. Delivery Note
    e3 = FrappeEvent(
        event_type=FrappeEventType.DELIVERY_NOTE_SUBMITTED,
        doc_type="Delivery Note",
        doc_name="DN-001",
        payload={"customer": "CUST-001", "sales_order": "SO-001", "delivery_status": "delayed"},
    )
    # 4. Customer Issue
    e4 = FrappeEvent(
        event_type=FrappeEventType.ISSUE_CREATED,
        doc_type="Issue",
        doc_name="ISSUE-001",
        payload={"customer": "CUST-001", "subject": "Delayed delivery of acoustic foam"},
    )

    observations = [
        FrappeEventTranslator.translate(e1),
        FrappeEventTranslator.translate(e2),
        FrappeEventTranslator.translate(e3),
        FrappeEventTranslator.translate(e4),
    ]

    experience = FrappeExperienceBuilder.build_lifecycle_experience(
        lifecycle_id="SALES-CYCLE-SO-001",
        lifecycle_type=ERPLifecycleType.SALES_ORDER_LIFECYCLE,
        observations=observations,
        agent_id="sales_coordinator",
        additional_context={"sales_order_id": "SO-001"},
    )

    assert isinstance(experience, ExperienceRecord)
    assert experience.episode_id == "SALES-CYCLE-SO-001"
    assert experience.environment_id == "frappe_erpnext"
    assert experience.metadata["observation_count"] == 4
    assert len(experience.metadata["observation_ids"]) == 4

    # Metadata verification
    assert experience.metadata["source_application"] == "frappe"
    assert experience.metadata["lifecycle_type"] == "SalesOrderLifecycle"
    assert experience.metadata["sales_order_id"] == "SO-001"
    assert "CUST-001" in experience.metadata["subjects"]

    # Provenance verification
    prov = experience.provenance
    assert prov is not None
    assert prov.source_type == SourceType.COMPOSITE
    assert len(prov.parent_ids) == 4
    for obs in observations:
        assert obs.id in prov.parent_ids
