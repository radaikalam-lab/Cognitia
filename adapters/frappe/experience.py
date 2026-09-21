"""Frappe ERP Experience Formation.

Constructs domain-neutral Cognitia ExperienceRecords from sequences
of related ERP observations across business lifecycles.
"""

from __future__ import annotations

import enum
from typing import Any

from cognitia.abi.types import Observation
from cognitia.experience.record import ExperienceBuilder, ExperienceRecord
from cognitia.provenance.record import ProvenanceRecord, SourceType


class ERPLifecycleType(str, enum.Enum):
    """Standard ERP business lifecycle workflows."""

    SALES_ORDER_LIFECYCLE = "SalesOrderLifecycle"
    PURCHASE_LIFECYCLE = "PurchaseLifecycle"
    DELIVERY_LIFECYCLE = "DeliveryLifecycle"
    PAYMENT_LIFECYCLE = "PaymentLifecycle"
    CUSTOMER_ISSUE_LIFECYCLE = "CustomerIssueLifecycle"
    PROCUREMENT_LIFECYCLE = "ProcurementLifecycle"
    MANUFACTURING_LIFECYCLE = "ManufacturingLifecycle"


class FrappeExperienceBuilder:
    """Utility for aggregating related Frappe observations into a structured ExperienceRecord."""

    @staticmethod
    def build_lifecycle_experience(
        lifecycle_id: str,
        lifecycle_type: str | ERPLifecycleType,
        observations: list[Observation],
        environment_id: str = "frappe_erpnext",
        agent_id: str = "frappe_system",
        additional_context: dict[str, Any] | None = None,
    ) -> ExperienceRecord:
        """Construct a lineage-preserving ExperienceRecord from a series of ERP observations."""
        type_str = (
            lifecycle_type.value
            if isinstance(lifecycle_type, ERPLifecycleType)
            else str(lifecycle_type)
        )

        builder = (
            ExperienceBuilder(
                source_application="frappe",
                episode_id=lifecycle_id,
            )
            .with_environment(environment_id)
            .with_agent(agent_id)
        )

        if observations:
            builder.with_observation(observations[0])

        # Extract subjects if present in observations
        subjects: set[str] = set()
        for obs in observations:
            sub = obs.metadata.get("subject_id") or obs.payload.get("subject_id")
            if sub:
                subjects.add(str(sub))

        builder.with_metadata("source_application", "frappe")
        builder.with_metadata("lifecycle_type", type_str)
        builder.with_metadata("lifecycle_id", lifecycle_id)
        builder.with_metadata("observation_count", len(observations))
        builder.with_metadata("observation_ids", [obs.id for obs in observations])

        if subjects:
            builder.with_metadata("subjects", sorted(list(subjects)))
        if additional_context:
            for k, v in additional_context.items():
                builder.with_metadata(k, v)

        # Build composite provenance linking to all source observations
        prov = ProvenanceRecord(
            source_type=SourceType.COMPOSITE,
            producer_id="frappe_adapter:experience_builder",
            parent_ids=[obs.id for obs in observations],
            is_deterministic=True,
        )
        builder.with_provenance(prov)

        return builder.build()
