"""Cognitia Dynamic Cognitive Document Types.

Defines deterministic, provenance-aware document models, section types,
references, and versions. Documents are projections of canonical state,
never sources of truth or authority mechanisms.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any

from cognitia.abi.types import (
    CognitiveObject,
    SCHEMA_VERSION_V1,
    current_utc_timestamp,
    generate_entity_id,
)
from cognitia.provenance.record import ProvenanceRecord, SourceType


class SectionType(str, enum.Enum):
    """Categories of document sections for human-facing projections."""

    TEXT = "text"
    TABLE = "table"
    TIMELINE = "timeline"
    GRAPH = "graph"
    METRICS = "metrics"
    OBSERVATIONS = "observations"
    EVIDENCE = "evidence"
    HYPOTHESES = "hypotheses"
    CLAIMS = "claims"
    REASONING = "reasoning"
    DECISIONS = "decisions"
    DIRECTION = "direction"
    CONFLICTS = "conflicts"
    PROVENANCE = "provenance"
    RESIDUALS = "residuals"


@dataclass(frozen=True)
class DocumentReference:
    """Canonical reference to a cognitive artifact preserved within a document."""

    reference_id: str = field(default_factory=generate_entity_id)
    artifact_id: str = ""
    artifact_type: str = ""
    schema_version: str = SCHEMA_VERSION_V1
    source_node_id: str | None = None
    origin_node_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __init__(
        self,
        artifact_id: str = "",
        artifact_type: str = "",
        schema_version: str = SCHEMA_VERSION_V1,
        source_node_id: str | None = None,
        origin_node_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "reference_id", generate_entity_id())
        object.__setattr__(self, "artifact_id", str(artifact_id))
        object.__setattr__(self, "artifact_type", str(artifact_type))
        object.__setattr__(self, "schema_version", str(schema_version))
        object.__setattr__(self, "source_node_id", source_node_id)
        object.__setattr__(self, "origin_node_id", origin_node_id)
        object.__setattr__(self, "metadata", dict(metadata or {}))


@dataclass(frozen=True)
class SectionContent:
    """Atomic content unit within a document section."""

    content_id: str = field(default_factory=generate_entity_id)
    content_type: str = "text"
    reference: DocumentReference | None = None
    text: str | None = None
    data: tuple[tuple[str, Any], ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def __init__(
        self,
        content_type: str = "text",
        reference: DocumentReference | None = None,
        text: str | None = None,
        data: Sequence[tuple[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "content_id", generate_entity_id())
        object.__setattr__(self, "content_type", str(content_type))
        object.__setattr__(self, "reference", reference)
        object.__setattr__(self, "text", text)
        object.__setattr__(self, "data", tuple(data or ()))
        object.__setattr__(self, "metadata", dict(metadata or {}))


@dataclass(frozen=True)
class DocumentSection:
    """Structured section of a dynamic cognitive document."""

    section_id: str = field(default_factory=generate_entity_id)
    section_type: SectionType = SectionType.TEXT
    title: str = ""
    content: tuple[SectionContent, ...] = ()
    ordering: tuple[str, ...] | None = None
    filters: dict[str, Any] | None = None
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(source_type=SourceType.DETERMINISTIC_RULE)
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    def __init__(
        self,
        section_type: SectionType | str = SectionType.TEXT,
        title: str = "",
        content: Sequence[SectionContent] | None = None,
        ordering: Sequence[str] | None = None,
        filters: dict[str, Any] | None = None,
        provenance: ProvenanceRecord | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "section_id", generate_entity_id())
        if isinstance(section_type, str):
            section_type = SectionType(section_type)
        object.__setattr__(self, "section_type", section_type)
        object.__setattr__(self, "title", str(title))
        object.__setattr__(self, "content", tuple(content or ()))
        object.__setattr__(self, "ordering", tuple(ordering) if ordering is not None else None)
        object.__setattr__(self, "filters", dict(filters) if filters is not None else None)
        prov = provenance or ProvenanceRecord(
            source_type=SourceType.DETERMINISTIC_RULE,
            producer_id="document_section_builder",
            is_deterministic=True,
        )
        object.__setattr__(self, "provenance", prov)
        object.__setattr__(self, "metadata", dict(metadata or {}))


@dataclass(frozen=True)
class DocumentVersion(CognitiveObject):
    """Versioned snapshot of a dynamic cognitive document."""

    version_id: str = field(default_factory=generate_entity_id)
    document_id: str = ""
    document_version: str = "1.0.0"
    specification_hash: str = ""
    state_hash: str = ""
    created_at: str = field(default_factory=current_utc_timestamp)
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(source_type=SourceType.DETERMINISTIC_RULE)
    )

    def __init__(
        self,
        document_id: str = "",
        document_version: str = "1.0.0",
        specification_hash: str = "",
        state_hash: str = "",
        created_at: str | None = None,
        provenance: ProvenanceRecord | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "version_id", generate_entity_id())
        object.__setattr__(self, "document_id", str(document_id))
        object.__setattr__(self, "document_version", str(document_version))
        object.__setattr__(self, "specification_hash", str(specification_hash))
        object.__setattr__(self, "state_hash", str(state_hash))
        object.__setattr__(self, "created_at", created_at or current_utc_timestamp())
        prov = provenance or ProvenanceRecord(
            source_type=SourceType.DETERMINISTIC_RULE,
            producer_id="document_version_builder",
            is_deterministic=True,
        )
        object.__setattr__(self, "provenance", prov)
        object.__setattr__(self, "metadata", dict(metadata or {}))


@dataclass(frozen=True)
class DynamicDocument(CognitiveObject):
    """Human-facing projection of structured Cognitia state.

    A document is never the source of truth, never authority, and never memory.
    """

    document_version: str = "1.0.0"
    title: str = ""
    document_type: str = "cognitive"
    source_references: tuple[DocumentReference, ...] = ()
    sections: tuple[DocumentSection, ...] = ()
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(source_type=SourceType.DETERMINISTIC_RULE)
    )

    def __init__(
        self,
        document_version: str = "1.0.0",
        title: str = "",
        document_type: str = "cognitive",
        source_references: Sequence[DocumentReference] | None = None,
        sections: Sequence[DocumentSection] | None = None,
        provenance: ProvenanceRecord | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "id", generate_entity_id())
        object.__setattr__(self, "schema_version", SCHEMA_VERSION_V1)
        object.__setattr__(self, "created_at", current_utc_timestamp())
        object.__setattr__(self, "document_version", str(document_version))
        object.__setattr__(self, "title", str(title))
        object.__setattr__(self, "document_type", str(document_type))
        object.__setattr__(self, "source_references", tuple(source_references or ()))
        object.__setattr__(self, "sections", tuple(sections or ()))
        prov = provenance or ProvenanceRecord(
            source_type=SourceType.DETERMINISTIC_RULE,
            producer_id="dynamic_document_builder",
            is_deterministic=True,
        )
        object.__setattr__(self, "provenance", prov)
        object.__setattr__(self, "metadata", dict(metadata or {}))
