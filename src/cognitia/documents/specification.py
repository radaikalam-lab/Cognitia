"""Cognitia Dynamic Cognitive Document Specification.

Defines the declarative specification of what a document should project,
including section specifications, filters, ordering, and visibility toggles.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence

from cognitia.abi.types import (
    SCHEMA_VERSION_V1,
    current_utc_timestamp,
    generate_entity_id,
)
from cognitia.documents.types import DocumentReference, SectionType
from cognitia.provenance.record import ProvenanceRecord, SourceType


@dataclass(frozen=True)
class SectionSpecification:
    """Declarative specification for a single document section."""

    section_type: SectionType = SectionType.TEXT
    title: str = ""
    artifact_types: tuple[str, ...] = ()
    filters: dict[str, Any] | None = None
    ordering: tuple[str, ...] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __init__(
        self,
        section_type: SectionType | str = SectionType.TEXT,
        title: str = "",
        artifact_types: Sequence[str] | None = None,
        filters: dict[str, Any] | None = None,
        ordering: Sequence[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if isinstance(section_type, str):
            section_type = SectionType(section_type)
        object.__setattr__(self, "section_type", section_type)
        object.__setattr__(self, "title", str(title))
        object.__setattr__(self, "artifact_types", tuple(artifact_types or ()))
        object.__setattr__(self, "filters", dict(filters) if filters is not None else None)
        object.__setattr__(self, "ordering", tuple(ordering) if ordering is not None else None)
        object.__setattr__(self, "metadata", dict(metadata or {}))


@dataclass(frozen=True)
class DocumentSpecification:
    """Declarative specification describing what a dynamic document should project.

    A specification describes what should be represented, not how to compute it.
    """

    specification_id: str = field(default_factory=generate_entity_id)
    document_type: str = "cognitive"
    title: str = ""
    requested_artifacts: tuple[DocumentReference, ...] = ()
    requested_sections: tuple[SectionSpecification, ...] = ()
    filters: dict[str, Any] | None = None
    ordering: tuple[str, ...] | None = None
    context_scope: dict[str, Any] | None = None
    attention_scope: dict[str, Any] | None = None
    provenance_visibility: bool = True
    epistemic_visibility: bool = True
    conflict_visibility: bool = True
    residual_visibility: bool = True
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(source_type=SourceType.DETERMINISTIC_RULE)
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    def __init__(
        self,
        document_type: str = "cognitive",
        title: str = "",
        requested_artifacts: Sequence[DocumentReference] | None = None,
        requested_sections: Sequence[SectionSpecification] | None = None,
        filters: dict[str, Any] | None = None,
        ordering: Sequence[str] | None = None,
        context_scope: dict[str, Any] | None = None,
        attention_scope: dict[str, Any] | None = None,
        provenance_visibility: bool = True,
        epistemic_visibility: bool = True,
        conflict_visibility: bool = True,
        residual_visibility: bool = True,
        provenance: ProvenanceRecord | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "specification_id", generate_entity_id())
        object.__setattr__(self, "schema_version", SCHEMA_VERSION_V1)
        object.__setattr__(self, "created_at", current_utc_timestamp())
        object.__setattr__(self, "document_type", str(document_type))
        object.__setattr__(self, "title", str(title))
        object.__setattr__(self, "requested_artifacts", tuple(requested_artifacts or ()))
        object.__setattr__(self, "requested_sections", tuple(requested_sections or ()))
        object.__setattr__(self, "filters", dict(filters) if filters is not None else None)
        object.__setattr__(self, "ordering", tuple(ordering) if ordering is not None else None)
        object.__setattr__(self, "context_scope", dict(context_scope) if context_scope is not None else None)
        object.__setattr__(self, "attention_scope", dict(attention_scope) if attention_scope is not None else None)
        object.__setattr__(self, "provenance_visibility", bool(provenance_visibility))
        object.__setattr__(self, "epistemic_visibility", bool(epistemic_visibility))
        object.__setattr__(self, "conflict_visibility", bool(conflict_visibility))
        object.__setattr__(self, "residual_visibility", bool(residual_visibility))
        prov = provenance or ProvenanceRecord(
            source_type=SourceType.DETERMINISTIC_RULE,
            producer_id="document_specification_builder",
            is_deterministic=True,
        )
        object.__setattr__(self, "provenance", prov)
        object.__setattr__(self, "metadata", dict(metadata or {}))
