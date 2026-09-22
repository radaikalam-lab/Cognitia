"""Cognitia Dynamic Cognitive Document Projection.

Provides deterministic, read-only, reproducible transformation of canonical
Cognitia state into DynamicDocument representations.
"""

from __future__ import annotations

from typing import Any

from cognitia.documents.specification import DocumentSpecification, SectionSpecification
from cognitia.documents.types import (
    DocumentReference,
    DocumentSection,
    DocumentVersion,
    DynamicDocument,
    SectionContent,
    SectionType,
)
from cognitia.epistemic.types import (
    Claim,
    EpistemicStatus,
    Evidence,
    Hypothesis,
    Residual,
)
from cognitia.memory.types import MemoryContext
from cognitia.provenance.record import ProvenanceRecord, SourceType
from cognitia.reasoning.types import ReasoningTrace


class DeterministicDocumentProjection:
    """Deterministic projection of canonical Cognitia state into DynamicDocument.

    A projection is a pure function of source state and specification.
    No external providers, models, or randomness are introduced.
    """

    def __init__(
        self,
        projection_id: str = "deterministic_document_projection",
    ) -> None:
        self._projection_id = projection_id

    def project(
        self,
        specification: DocumentSpecification,
        memory_context: MemoryContext | None = None,
        conflicts: list[Any] | None = None,
    ) -> DynamicDocument:
        """Project canonical state into a DynamicDocument.

        Args:
            specification: declarative projection specification.
            memory_context: optional assembled memory context.
            conflicts: optional list of cognitive conflicts to preserve.

        Returns:
            Deterministic DynamicDocument projection.
        """
        sections = self._build_sections(
            specification=specification,
            memory_context=memory_context,
            conflicts=conflicts,
        )

        source_references = self._build_source_references(
            memory_context=memory_context,
            conflicts=conflicts,
        )

        provenance = ProvenanceRecord(
            source_type=SourceType.DETERMINISTIC_RULE,
            producer_id=self._projection_id,
            parent_ids=[specification.specification_id],
            is_deterministic=True,
        )

        return DynamicDocument(
            document_version="1.0.0",
            title=specification.title or "Dynamic Cognitive Document",
            document_type=specification.document_type,
            source_references=tuple(source_references),
            sections=tuple(sections),
            provenance=provenance,
            metadata={"specification_id": specification.specification_id},
        )

    def _build_sections(
        self,
        specification: DocumentSpecification,
        memory_context: MemoryContext | None,
        conflicts: list[Any] | None,
    ) -> list[DocumentSection]:
        sections: list[DocumentSection] = []

        if specification.requested_sections:
            for section_spec in specification.requested_sections:
                sections.append(self._build_section(section_spec, memory_context, conflicts))
        else:
            sections.append(self._build_default_section(memory_context, conflicts))

        return sections

    def _build_default_section(
        self,
        memory_context: MemoryContext | None,
        conflicts: list[Any] | None,
    ) -> DocumentSection:
        content: list[SectionContent] = []

        if memory_context:
            content.extend(self._summarize_memory(memory_context))

        if conflicts:
            content.extend(self._summarize_conflicts(conflicts))

        if not content:
            content.append(SectionContent(text="No structured state available for projection."))

        return DocumentSection(
            section_type=SectionType.TEXT,
            title="Cognitive State Summary",
            content=tuple(content),
            provenance=ProvenanceRecord(
                source_type=SourceType.DETERMINISTIC_RULE,
                producer_id=self._projection_id,
                is_deterministic=True,
            ),
        )

    def _build_section(
        self,
        section_spec: SectionSpecification,
        memory_context: MemoryContext | None,
        conflicts: list[Any] | None,
    ) -> DocumentSection:
        content: list[SectionContent] = []

        if memory_context and self._section_matches_spec(section_spec, memory_context):
            content.extend(self._project_memory_into_section(section_spec, memory_context))

        if conflicts and section_spec.section_type == SectionType.CONFLICTS:
            content.extend(self._summarize_conflicts(conflicts))

        if not content:
            content.append(
                SectionContent(
                    content_type="text",
                    text=f"No content available for section '{section_spec.title}'.",
                    metadata={"section_type": section_spec.section_type.value},
                )
            )

        return DocumentSection(
            section_type=section_spec.section_type,
            title=section_spec.title,
            content=tuple(content),
            ordering=section_spec.ordering,
            filters=section_spec.filters,
            provenance=ProvenanceRecord(
                source_type=SourceType.DETERMINISTIC_RULE,
                producer_id=self._projection_id,
                is_deterministic=True,
            ),
            metadata={"section_spec": section_spec.metadata},
        )

    def _section_matches_spec(
        self,
        section_spec: SectionSpecification,
        memory_context: MemoryContext,
    ) -> bool:
        if not section_spec.artifact_types:
            return True
        available_types = {
            "experience": len(memory_context.experiences),
            "observation": len(memory_context.observations),
            "evidence": len(memory_context.evidence),
            "hypothesis": len(memory_context.hypotheses),
            "claim": len(memory_context.claims),
            "reasoning": len(memory_context.reasoning_traces),
            "decision": len(memory_context.decisions),
            "outcome": len(memory_context.outcomes),
        }
        return any(
            available_types.get(artifact_type, 0) > 0
            for artifact_type in section_spec.artifact_types
        )

    def _project_memory_into_section(
        self,
        section_spec: SectionSpecification,
        memory_context: MemoryContext,
    ) -> list[SectionContent]:
        content: list[SectionContent] = []

        section_type = section_spec.section_type
        artifact_types = section_spec.artifact_types or []

        def _matches(artifact_type: str) -> bool:
            return not artifact_types or artifact_type in artifact_types

        if section_type == SectionType.OBSERVATIONS and _matches("observation"):
            for observation in memory_context.observations:
                content.append(
                    SectionContent(
                        content_type="observation",
                        text=observation.payload.get("summary", ""),
                        reference=DocumentReference(
                            artifact_id=observation.id,
                            artifact_type="observation",
                        ),
                        metadata={"source_id": observation.source_id},
                    )
                )

        if section_type == SectionType.EVIDENCE and _matches("evidence"):
            for evidence in memory_context.evidence:
                content.append(
                    SectionContent(
                        content_type="evidence",
                        text=evidence.__class__.__name__,
                        reference=DocumentReference(
                            artifact_id=evidence.id,
                            artifact_type="evidence",
                        ),
                        metadata={"direction": evidence.direction.value},
                    )
                )

        if section_type == SectionType.HYPOTHESES and _matches("hypothesis"):
            for hypothesis in memory_context.hypotheses:
                content.append(
                    SectionContent(
                        content_type="hypothesis",
                        text=hypothesis.statement,
                        reference=DocumentReference(
                            artifact_id=hypothesis.id,
                            artifact_type="hypothesis",
                        ),
                        metadata={"status": hypothesis.initial_status.value},
                    )
                )

        if section_type == SectionType.CLAIMS and _matches("claim"):
            for claim in memory_context.claims:
                content.append(
                    SectionContent(
                        content_type="claim",
                        text=claim.statement,
                        reference=DocumentReference(
                            artifact_id=claim.id,
                            artifact_type="claim",
                        ),
                        metadata={"status": claim.status.value, "confidence": claim.confidence},
                    )
                )

        if section_type == SectionType.REASONING and _matches("reasoning"):
            for trace in memory_context.reasoning_traces:
                content.append(
                    SectionContent(
                        content_type="reasoning_trace",
                        text=trace.__class__.__name__,
                        reference=DocumentReference(
                            artifact_id=trace.id,
                            artifact_type="reasoning_trace",
                        ),
                        metadata={"mode": trace.mode.value if hasattr(trace, "mode") else "unknown"},
                    )
                )

        if section_type == SectionType.DECISIONS and _matches("decision"):
            for decision in memory_context.decisions:
                content.append(
                    SectionContent(
                        content_type="decision",
                        text=decision.proposal_type,
                        reference=DocumentReference(
                            artifact_id=decision.id,
                            artifact_type="decision",
                        ),
                        metadata={"confidence": decision.confidence},
                    )
                )

        if section_type == SectionType.DIRECTION and _matches("direction"):
            pass

        if section_type == SectionType.RESIDUALS and _matches("residual"):
            pass

        if section_type == SectionType.METRICS:
            data: list[tuple[str, Any]] = []
            data.append(("observations", len(memory_context.observations)))
            data.append(("evidence", len(memory_context.evidence)))
            data.append(("hypotheses", len(memory_context.hypotheses)))
            data.append(("claims", len(memory_context.claims)))
            data.append(("reasoning_traces", len(memory_context.reasoning_traces)))
            data.append(("decisions", len(memory_context.decisions)))
            data.append(("outcomes", len(memory_context.outcomes)))
            content.append(SectionContent(content_type="metrics", data=tuple(data)))

        return content

    def _summarize_memory(self, memory_context: MemoryContext) -> list[SectionContent]:
        content: list[SectionContent] = []

        if memory_context.observations:
            content.append(
                SectionContent(
                    content_type="summary",
                    text=f"Observations: {len(memory_context.observations)}",
                )
            )
        if memory_context.evidence:
            content.append(
                SectionContent(
                    content_type="summary",
                    text=f"Evidence: {len(memory_context.evidence)}",
                )
            )
        if memory_context.hypotheses:
            content.append(
                SectionContent(
                    content_type="summary",
                    text=f"Hypotheses: {len(memory_context.hypotheses)}",
                )
            )
        if memory_context.claims:
            content.append(
                SectionContent(
                    content_type="summary",
                    text=f"Claims: {len(memory_context.claims)}",
                )
            )
        if memory_context.reasoning_traces:
            content.append(
                SectionContent(
                    content_type="summary",
                    text=f"Reasoning traces: {len(memory_context.reasoning_traces)}",
                )
            )
        if memory_context.decisions:
            content.append(
                SectionContent(
                    content_type="summary",
                    text=f"Decisions: {len(memory_context.decisions)}",
                )
            )

        return content

    def _summarize_conflicts(self, conflicts: list[Any]) -> list[SectionContent]:
        content: list[SectionContent] = []

        for conflict in conflicts:
            content.append(
                SectionContent(
                    content_type="conflict",
                    text=f"Conflict: {conflict.description}",
                    reference=DocumentReference(
                        artifact_id=getattr(conflict, "id", ""),
                        artifact_type="cognitive_conflict",
                    ),
                    metadata={
                        "status": getattr(conflict, "status", "unknown").value
                        if hasattr(getattr(conflict, "status", ""), "value")
                        else str(getattr(conflict, "status", "unknown")),
                        "conflict_type": getattr(conflict, "conflict_type", "unknown").value
                        if hasattr(getattr(conflict, "conflict_type", ""), "value")
                        else str(getattr(conflict, "conflict_type", "unknown")),
                    },
                )
            )

        return content

    def _build_source_references(
        self,
        memory_context: MemoryContext | None,
        conflicts: list[Any] | None,
    ) -> list[DocumentReference]:
        references: list[DocumentReference] = []

        if memory_context:
            for observation in memory_context.observations:
                references.append(
                    DocumentReference(
                        artifact_id=observation.id,
                        artifact_type="observation",
                    )
                )
            for evidence in memory_context.evidence:
                references.append(
                    DocumentReference(
                        artifact_id=evidence.id,
                        artifact_type="evidence",
                    )
                )
            for hypothesis in memory_context.hypotheses:
                references.append(
                    DocumentReference(
                        artifact_id=hypothesis.id,
                        artifact_type="hypothesis",
                    )
                )
            for claim in memory_context.claims:
                references.append(
                    DocumentReference(
                        artifact_id=claim.id,
                        artifact_type="claim",
                    )
                )
            for trace in memory_context.reasoning_traces:
                references.append(
                    DocumentReference(
                        artifact_id=trace.id,
                        artifact_type="reasoning_trace",
                    )
                )
            for decision in memory_context.decisions:
                references.append(
                    DocumentReference(
                        artifact_id=decision.id,
                        artifact_type="decision",
                    )
                )

        return references

    def version_document(
        self,
        document: DynamicDocument,
        specification_hash: str = "",
        state_hash: str = "",
    ) -> DocumentVersion:
        """Create a versioned snapshot of a document."""
        return DocumentVersion(
            document_id=document.id,
            document_version=document.document_version,
            specification_hash=specification_hash,
            state_hash=state_hash,
            provenance=document.provenance,
        )
