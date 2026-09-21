# Cognitia Frappe / ERPNext Adapter

## 1. Architectural Role

The **Frappe Adapter** bridges Frappe / ERPNext with Cognitia.

```text
┌──────────────────────────────┐              ┌──────────────────────────────┐
│       Frappe / ERPNext       │              │        Cognitia Core         │
│  (Authoritative Domain App)  │              │      (Cognitive Plane)       │
│                              │              │                              │
│  • Sales Orders              │ Document     │  • Observations              │
│  • Purchase Orders           │ Events       │  • ERP Experiences           │
│  • Stock Entries             │ ──────────>  │  • Cognitive Memory          │
│  • Invoices & Payments       │              │  • Human Cognitive Rules     │
│  • Workflows & Accounting    │              │  • Epistemic Validation      │
│                              │              │                              │
│  • Read-Only Advisories      │ <──────────  │  • Advisory Decisions        │
│  • Human Rule Authoring      │              │  • Lineage Provenance        │
└──────────────────────────────┘              └──────────────────────────────┘
```

## 2. Core Invariants

1. **Strict Dependency Direction**:
   The Frappe adapter depends on Cognitia contracts and SPIs. Cognitia Core contains **zero** imports or dependencies on Frappe or ERPNext.
2. **Authority Boundary**:
   Frappe remains the sole business authority. Cognitia emits **non-authoritative advisories** and never mutates Frappe records, prices, stock, or workflow states.
3. **Auditability & Provenance**:
   All observations, experiences, and human rules carry cryptographic checksums, author identity, timestamp, and lineage parent links.
4. **Human-Governed Plasticity**:
   Cognitive rules are authored or modified by humans, versioned immutably ($N \to N+1$), and cannot be silently mutated by runtime observations.

## 3. Event Vocabulary

The adapter translates key lifecycle events into Cognitia `Observation` objects:
- `CustomerCreated` / `CustomerUpdated`
- `SupplierCreated` / `SupplierUpdated`
- `QuotationCreated` / `QuotationSubmitted`
- `SalesOrderCreated` / `SalesOrderSubmitted`
- `PurchaseOrderCreated` / `PurchaseOrderSubmitted`
- `StockEntryCreated` / `StockEntrySubmitted`
- `DeliveryNoteCreated` / `DeliveryNoteSubmitted`
- `SalesInvoiceCreated` / `SalesInvoiceSubmitted`
- `PaymentEntryCreated` / `PaymentEntrySubmitted`
- `IssueCreated` / `IssueResolved`
- `WorkOrderCreated` / `WorkOrderCompleted`

## 4. ERP Experience Formation

Correlated observations across a business workflow are aggregated into `ExperienceRecord`s:
- `SalesOrderLifecycle` (Quotation $\to$ Order $\to$ Delivery $\to$ Invoice $\to$ Payment $\to$ Issue)
- `ProcurementLifecycle`
- `ManufacturingLifecycle`

## 5. Advisory Presentation

Advisories return `FrappeAdvisory` objects containing:
- Historical context summary
- Relevant similar experiences count
- Epistemic status
- Supporting evidence count
- Triggered rule identifier & version
- Recommendation text
- Explicit `is_authoritative: False` flag
