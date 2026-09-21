"""Tests for Frappe Event Translation and Observation Mapping."""

import pytest

from cognitia.abi.types import Observation
from adapters.frappe.events import FrappeEvent, FrappeEventType
from adapters.frappe.translator import FrappeEventTranslator


def test_sales_order_submitted_translation() -> None:
    event = FrappeEvent(
        event_type=FrappeEventType.SALES_ORDER_SUBMITTED,
        doc_type="Sales Order",
        doc_name="SO-2026-00042",
        payload={
            "customer": "CUST-0010",
            "grand_total": 45000.0,
            "items": [
                {"item_code": "ACOUSTIC-PANEL-A", "qty": 50, "rate": 900.0}
            ],
            "delivery_date": "2026-10-15",
        },
        timestamp="2026-09-21T10:00:00Z",
        user="sales_manager@example.com",
    )

    obs = FrappeEventTranslator.translate(event)

    assert isinstance(obs, Observation)
    assert obs.source_id == "frappe:Sales Order:SO-2026-00042"
    assert obs.created_at == "2026-09-21T10:00:00Z"

    # Payload integrity
    assert obs.payload["event_type"] == "SalesOrderSubmitted"
    assert obs.payload["doc_type"] == "Sales Order"
    assert obs.payload["doc_name"] == "SO-2026-00042"
    assert obs.payload["subject_id"] == "CUST-0010"
    assert obs.payload["user"] == "sales_manager@example.com"
    assert obs.payload["data"]["grand_total"] == 45000.0

    # Metadata for indexing and memory query
    assert obs.metadata["source_application"] == "frappe"
    assert obs.metadata["doc_type"] == "Sales Order"
    assert obs.metadata["doc_name"] == "SO-2026-00042"
    assert obs.metadata["subject_id"] == "CUST-0010"
    assert obs.metadata["event_type"] == "SalesOrderSubmitted"


def test_supplier_purchase_order_translation() -> None:
    event = FrappeEvent(
        event_type=FrappeEventType.PURCHASE_ORDER_SUBMITTED,
        doc_type="Purchase Order",
        doc_name="PO-2026-00100",
        payload={
            "supplier": "SUPP-007",
            "items": [{"item_code": "RAW-FOAM-01", "qty": 200}],
        },
    )

    obs = FrappeEventTranslator.translate(event)
    assert obs.source_id == "frappe:Purchase Order:PO-2026-00100"
    assert obs.payload["subject_id"] == "SUPP-007"
    assert obs.metadata["subject_id"] == "SUPP-007"
