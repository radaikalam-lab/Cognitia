"""Cognitia Dynamic Cognitive Document Service.

Provides service-layer operations for projecting, refreshing, and diffing
dynamic cognitive documents. Documents remain projections; this service
introduces no new authority or persistence semantics.
"""

from __future__ import annotations

from typing import Any

from cognitia.documents.diff import ChangeEntry, ChangeType, DocumentChange
from cognitia.documents.projection import DeterministicDocumentProjection
from cognitia.documents.specification import DocumentSpecification
from cognitia.documents.types import DocumentVersion, DynamicDocument
from cognitia.epistemic.types import (
    Claim,
    Evidence,
    Hypothesis,
    Residual,
)
from cognitia.memory.types import MemoryContext
from cognitia.provenance.record import ProvenanceRecord, SourceType
from cognitia.reasoning.types import ReasoningTrace


class DocumentService:
    """Service layer for dynamic cognitive document operations.

    Operates deterministically and read-only with respect to source state.
    """

    def __init__(
        self,
        projection: DeterministicDocumentProjection | None = None,
    ) -> None:
        self._projection = projection or DeterministicDocumentProjection()
        self._documents: dict[str, DynamicDocument] = {}
        self._versions: dict[str, list[DocumentVersion]] = {}

    def project(
        self,
        specification: DocumentSpecification,
        memory_context: MemoryContext | None = None,
        conflicts: list[Any] | None = None,
    ) -> DynamicDocument:
        """Project canonical state into a new DynamicDocument.

        Args:
            specification: declarative projection specification.
            memory_context: optional assembled memory context.
            conflicts: optional list of cognitive conflicts.

        Returns:
            New DynamicDocument projection.
        """
        document = self._projection.project(
            specification=specification,
            memory_context=memory_context,
            conflicts=conflicts,
        )
        self._documents[document.id] = document
        return document

    def refresh(
        self,
        specification: DocumentSpecification,
        document: DynamicDocument,
        memory_context: MemoryContext | None = None,
        conflicts: list[Any] | None = None,
    ) -> DynamicDocument:
        """Refresh an existing document projection deterministically.

        Refresh does not mutate source artifacts. It produces a new
        deterministic representation from specification and current state.
        """
        new_document = self._projection.project(
            specification=specification,
            memory_context=memory_context,
            conflicts=conflicts,
        )
        self._documents[document.id] = new_document
        return new_document

    def diff(
        self,
        from_document: DynamicDocument,
        to_document: DynamicDocument,
    ) -> DocumentChange:
        """Compute structural changes between two document versions.

        Returns descriptive change entries; no epistemic judgment is made.
        """
        changes: list[ChangeEntry] = []

        changes.extend(
            self._diff_field(
                path="document_version",
                old_value=from_document.document_version,
                new_value=to_document.document_version,
            )
        )
        changes.extend(
            self._diff_field(
                path="title",
                old_value=from_document.title,
                new_value=to_document.title,
            )
        )
        changes.extend(
            self._diff_field(
                path="document_type",
                old_value=from_document.document_type,
                new_value=to_document.document_type,
            )
        )

        changes.extend(
            self._diff_sections(
                from_sections=from_document.sections,
                to_sections=to_document.sections,
            )
        )

        return DocumentChange(
            document_id=from_document.id,
            from_version=from_document.document_version,
            to_version=to_document.document_version,
            changes=tuple(changes),
            provenance=ProvenanceRecord(
                source_type=SourceType.DETERMINISTIC_RULE,
                producer_id="document_service",
                is_deterministic=True,
            ),
        )

    def version(
        self,
        document: DynamicDocument,
        specification_hash: str = "",
        state_hash: str = "",
    ) -> DocumentVersion:
        """Create a versioned snapshot of a document."""
        doc_version = self._projection.version_document(
            document=document,
            specification_hash=specification_hash,
            state_hash=state_hash,
        )
        versions = self._versions.setdefault(document.id, [])
        versions.append(doc_version)
        return doc_version

    def get_document(self, document_id: str) -> DynamicDocument | None:
        """Retrieve a previously projected document by id."""
        return self._documents.get(document_id)

    def get_versions(self, document_id: str) -> list[DocumentVersion]:
        """Retrieve version history for a document."""
        return list(self._versions.get(document_id, []))

    def _diff_field(
        self,
        path: str,
        old_value: Any,
        new_value: Any,
    ) -> list[ChangeEntry]:
        if old_value == new_value:
            return [
                ChangeEntry(
                    change_type=ChangeType.UNCHANGED,
                    path=path,
                    old_value=old_value,
                    new_value=new_value,
                )
            ]
        return [
            ChangeEntry(
                change_type=ChangeType.CHANGED,
                path=path,
                old_value=old_value,
                new_value=new_value,
            )
        ]

    def _diff_sections(
        self,
        from_sections: tuple[Any, ...],
        to_sections: tuple[Any, ...],
    ) -> list[ChangeEntry]:
        changes: list[ChangeEntry] = []

        from_types = {section.section_type.value: section for section in from_sections}
        to_types = {section.section_type.value: section for section in to_sections}

        for section_type in set(from_types.keys()) | set(to_types.keys()):
            from_section = from_types.get(section_type)
            to_section = to_types.get(section_type)

            if from_section is None:
                changes.append(
                    ChangeEntry(
                        change_type=ChangeType.ADDED,
                        path=f"sections.{section_type}",
                        old_value=None,
                        new_value=to_section.title if to_section else None,
                    )
                )
            elif to_section is None:
                changes.append(
                    ChangeEntry(
                        change_type=ChangeType.REMOVED,
                        path=f"sections.{section_type}",
                        old_value=from_section.title if from_section else None,
                        new_value=None,
                    )
                )
            elif from_section.title != to_section.title:
                changes.append(
                    ChangeEntry(
                        change_type=ChangeType.CHANGED,
                        path=f"sections.{section_type}.title",
                        old_value=from_section.title,
                        new_value=to_section.title,
                    )
                )

        return changes


class InMemoryDocumentService(DocumentService):
    """In-memory reference implementation of DocumentService."""

    pass
