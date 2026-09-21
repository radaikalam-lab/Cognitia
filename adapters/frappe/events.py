"""Frappe ERP Event Vocabulary and Schemas.

Defines standard ERPNext / Frappe event types and data containers.
This file lives strictly in the adapter boundary and is not imported by Cognitia Core.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any


class FrappeEventType(str, enum.Enum):
    """Standard Frappe / ERPNext lifecycle events."""

    CUSTOMER_CREATED = "CustomerCreated"
    CUSTOMER_UPDATED = "CustomerUpdated"
    SUPPLIER_CREATED = "SupplierCreated"
    SUPPLIER_UPDATED = "SupplierUpdated"

    QUOTATION_CREATED = "QuotationCreated"
    QUOTATION_SUBMITTED = "QuotationSubmitted"

    SALES_ORDER_CREATED = "SalesOrderCreated"
    SALES_ORDER_SUBMITTED = "SalesOrderSubmitted"

    PURCHASE_ORDER_CREATED = "PurchaseOrderCreated"
    PURCHASE_ORDER_SUBMITTED = "PurchaseOrderSubmitted"

    STOCK_ENTRY_CREATED = "StockEntryCreated"
    STOCK_ENTRY_SUBMITTED = "StockEntrySubmitted"

    DELIVERY_NOTE_CREATED = "DeliveryNoteCreated"
    DELIVERY_NOTE_SUBMITTED = "DeliveryNoteSubmitted"

    SALES_INVOICE_CREATED = "SalesInvoiceCreated"
    SALES_INVOICE_SUBMITTED = "SalesInvoiceSubmitted"

    PAYMENT_ENTRY_CREATED = "PaymentEntryCreated"
    PAYMENT_ENTRY_SUBMITTED = "PaymentEntrySubmitted"

    ISSUE_CREATED = "IssueCreated"
    ISSUE_RESOLVED = "IssueResolved"

    WORK_ORDER_CREATED = "WorkOrderCreated"
    WORK_ORDER_COMPLETED = "WorkOrderCompleted"


@dataclass(frozen=True)
class FrappeEvent:
    """Container for an incoming Frappe business event."""

    event_type: str | FrappeEventType
    doc_type: str
    doc_name: str
    payload: dict[str, Any] = field(default_factory=dict)
    subject_id: str | None = None
    timestamp: str | None = None
    user: str = "Administrator"
