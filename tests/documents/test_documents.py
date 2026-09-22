"""Cognitia Phase 9: Dynamic Cognitive Document Tests."""

from __future__ import annotations

import pytest

from cognitia.abi.types import Observation
from cognitia.capabilities.base import CapabilityType
from cognitia.documents.diff import ChangeEntry, ChangeType, DocumentChange
from cognitia.documents.intent import DocumentIntent, IntentType
from cognitia.documents.projection import DeterministicDocumentProjection
from cognitia.documents.provider import DeterministicMockDocumentProvider
from cognitia.documents.service import DocumentService, InMemoryDocumentService
from cognitia.documents.specification import DocumentSpecification, SectionSpecification
from cognitia.documents.types import (
    DocumentReference,
    DocumentSection,
    DocumentVersion,
    DynamicDocument,
    SectionContent,
    SectionType,
)
from cognitia.epistemic.types import Claim, EpistemicStatus, Evidence, Hypothesis
from cognitia.memory.store import InMemoryMemoryStore
from cognitia.memory.types import MemoryContext, MemoryQuery
from cognitia.persistence.store import InMemoryPersistenceStore
from cognitia.provenance.record import SourceType
from cognitia.reasoning.types import ReasoningTrace


def _make_observation(observation_id: str = "obs_1") -> Observation:
    return Observation(id=observation_id, source_id="source_1", payload={"summary": "test"})


def _make_hypothesis(hypothesis_id: str = "hyp_1") -> Hypothesis:
    return Hypothesis(id=hypothesis_id, statement="test hypothesis", initial_status="hypothesis")


def _make_claim(claim_id: str = "claim_1") -> Claim:
    return Claim(id=claim_id, statement="test claim", status="supported", confidence=0.9)


def _make_evidence(evidence_id: str = "ev_1") -> Evidence:
    return Evidence(id=evidence_id, target_id="target_1", direction="support", confidence=0.8)


class TestDynamicDocumentTypes:
    def test_document_creation_defaults(self) -> None:
        doc = DynamicDocument()
        assert doc.id != ""
        assert doc.document_version == "1.0.0"
        assert doc.title == ""
        assert doc.document_type == "cognitive"
        assert doc.source_references == ()
        assert doc.sections == ()

    def test_document_creation_custom_values(self) -> None:
        ref = DocumentReference(artifact_id="art_1", artifact_type="observation")
        section = DocumentSection(section_type=SectionType.TEXT, title="section")
        doc = DynamicDocument(
            document_version="2.0.0",
            title="Test Document",
            document_type="analysis",
            source_references=[ref],
            sections=[section],
        )
        assert doc.title == "Test Document"
        assert doc.document_version == "2.0.0"
        assert doc.document_type == "analysis"
        assert len(doc.source_references) == 1
        assert doc.source_references[0].artifact_id == "art_1"
        assert len(doc.sections) == 1
        assert doc.sections[0].title == "section"

    def test_document_has_provenance(self) -> None:
        doc = DynamicDocument()
        assert doc.provenance is not None
        assert doc.provenance.source_type == SourceType.DETERMINISTIC_RULE

    def test_document_immutable(self) -> None:
        doc = DynamicDocument()
        with pytest.raises(AttributeError):
            doc.title = "modified"  # type: ignore[misc]

    def test_document_deterministic_serialization(self) -> None:
        doc = DynamicDocument(title="deterministic_test")
        assert doc.serialize() == doc.serialize()

    def test_document_is_not_source_of_truth(self) -> None:
        doc = DynamicDocument()
        assert not hasattr(doc, "authoritative_state")
        assert not hasattr(doc, "source_of_truth")

    def test_document_is_not_authority(self) -> None:
        doc = DynamicDocument()
        assert not hasattr(doc, "validate_domain")
        assert not hasattr(doc, "execute")


class TestDocumentReference:
    def test_default_values(self) -> None:
        ref = DocumentReference()
        assert ref.reference_id != ""
        assert ref.artifact_id == ""
        assert ref.artifact_type == ""
        assert ref.schema_version == "1.0.0"
        assert ref.source_node_id is None
        assert ref.origin_node_id is None
        assert ref.metadata == {}

    def test_custom_values(self) -> None:
        ref = DocumentReference(
            artifact_id="art_1",
            artifact_type="observation",
            source_node_id="node_a",
            origin_node_id="node_b",
            metadata={"key": "value"},
        )
        assert ref.artifact_id == "art_1"
        assert ref.artifact_type == "observation"
        assert ref.source_node_id == "node_a"
        assert ref.origin_node_id == "node_b"
        assert ref.metadata["key"] == "value"

    def test_immutable(self) -> None:
        ref = DocumentReference(artifact_id="art_1")
        with pytest.raises(AttributeError):
            ref.artifact_id = "art_2"  # type: ignore[misc]


class TestSectionContent:
    def test_default_values(self) -> None:
        content = SectionContent()
        assert content.content_id != ""
        assert content.content_type == "text"
        assert content.reference is None
        assert content.text is None
        assert content.data == ()
        assert content.metadata == {}

    def test_custom_values(self) -> None:
        ref = DocumentReference(artifact_id="art_1", artifact_type="observation")
        content = SectionContent(
            content_type="observation",
            reference=ref,
            text="test text",
            data=[("key", "value")],
            metadata={"m": 1},
        )
        assert content.content_type == "observation"
        assert content.reference is not None
        assert content.reference.artifact_id == "art_1"
        assert content.text == "test text"
        assert content.data == (("key", "value"),)
        assert content.metadata["m"] == 1


class TestDocumentSection:
    def test_default_values(self) -> None:
        section = DocumentSection()
        assert section.section_id != ""
        assert section.section_type == SectionType.TEXT
        assert section.title == ""
        assert section.content == ()
        assert section.ordering is None
        assert section.filters is None

    def test_custom_values(self) -> None:
        content = SectionContent(content_type="text", text="hello")
        section = DocumentSection(
            section_type=SectionType.OBSERVATIONS,
            title="Observations",
            content=[content],
            ordering=["field1"],
            filters={"type": "sensor"},
        )
        assert section.section_type == SectionType.OBSERVATIONS
        assert section.title == "Observations"
        assert len(section.content) == 1
        assert section.content[0].text == "hello"
        assert section.ordering == ("field1",)
        assert section.filters == {"type": "sensor"}

    def test_string_section_type_conversion(self) -> None:
        section = DocumentSection(section_type="evidence")
        assert section.section_type == SectionType.EVIDENCE

    def test_immutable(self) -> None:
        section = DocumentSection()
        with pytest.raises(AttributeError):
            section.title = "modified"  # type: ignore[misc]

    def test_has_provenance(self) -> None:
        section = DocumentSection()
        assert section.provenance is not None
        assert section.provenance.source_type == SourceType.DETERMINISTIC_RULE


class TestDocumentVersion:
    def test_default_values(self) -> None:
        version = DocumentVersion()
        assert version.version_id != ""
        assert version.document_id == ""
        assert version.document_version == "1.0.0"
        assert version.specification_hash == ""
        assert version.state_hash == ""
        assert version.created_at != ""

    def test_custom_values(self) -> None:
        version = DocumentVersion(
            document_id="doc_1",
            document_version="1.0.0",
            specification_hash="sha256:abc",
            state_hash="sha256:def",
        )
        assert version.document_id == "doc_1"
        assert version.specification_hash == "sha256:abc"
        assert version.state_hash == "sha256:def"


class TestDocumentSpecification:
    def test_default_values(self) -> None:
        spec = DocumentSpecification()
        assert spec.specification_id != ""
        assert spec.document_type == "cognitive"
        assert spec.title == ""
        assert spec.requested_artifacts == ()
        assert spec.requested_sections == ()
        assert spec.filters is None
        assert spec.ordering is None
        assert spec.provenance_visibility is True
        assert spec.epistemic_visibility is True
        assert spec.conflict_visibility is True
        assert spec.residual_visibility is True

    def test_custom_values(self) -> None:
        section_spec = SectionSpecification(
            section_type=SectionType.OBSERVATIONS,
            title="Observations",
            artifact_types=["observation"],
        )
        ref = DocumentReference(artifact_id="art_1", artifact_type="observation")
        spec = DocumentSpecification(
            document_type="analysis",
            title="Test Spec",
            requested_artifacts=[ref],
            requested_sections=[section_spec],
            filters={"status": "active"},
            ordering=["created_at"],
            context_scope={"agent_id": "agent_1"},
            attention_scope={"limit": 10},
        )
        assert spec.document_type == "analysis"
        assert spec.title == "Test Spec"
        assert len(spec.requested_artifacts) == 1
        assert len(spec.requested_sections) == 1
        assert spec.requested_sections[0].section_type == SectionType.OBSERVATIONS
        assert spec.filters == {"status": "active"}
        assert spec.ordering == ("created_at",)
        assert spec.context_scope == {"agent_id": "agent_1"}
        assert spec.attention_scope == {"limit": 10}

    def test_immutable(self) -> None:
        spec = DocumentSpecification()
        with pytest.raises(AttributeError):
            spec.title = "modified"  # type: ignore[misc]

    def test_has_provenance(self) -> None:
        spec = DocumentSpecification()
        assert spec.provenance is not None


class TestSectionSpecification:
    def test_default_values(self) -> None:
        spec = SectionSpecification()
        assert spec.section_type == SectionType.TEXT
        assert spec.title == ""
        assert spec.artifact_types == ()
        assert spec.filters is None
        assert spec.ordering is None

    def test_string_section_type_conversion(self) -> None:
        spec = SectionSpecification(section_type="metrics")
        assert spec.section_type == SectionType.METRICS

    def test_immutable(self) -> None:
        spec = SectionSpecification()
        with pytest.raises(AttributeError):
            spec.title = "modified"  # type: ignore[misc]


class TestDeterministicDocumentProjection:
    def test_project_empty_specification(self) -> None:
        projection = DeterministicDocumentProjection()
        spec = DocumentSpecification()
        doc = projection.project(spec)
        assert doc.id != ""
        assert doc.document_version == "1.0.0"
        assert doc.title == "Dynamic Cognitive Document"
        assert len(doc.sections) >= 1

    def test_project_with_title(self) -> None:
        projection = DeterministicDocumentProjection()
        spec = DocumentSpecification(title="My Document")
        doc = projection.project(spec)
        assert doc.title == "My Document"

    def test_project_with_section_specification(self) -> None:
        projection = DeterministicDocumentProjection()
        section_spec = SectionSpecification(
            section_type=SectionType.METRICS,
            title="Metrics",
        )
        spec = DocumentSpecification(title="Metrics Doc", requested_sections=[section_spec])
        doc = projection.project(spec)
        assert len(doc.sections) == 1
        assert doc.sections[0].section_type == SectionType.METRICS

    def test_project_deterministic(self) -> None:
        projection = DeterministicDocumentProjection()
        spec = DocumentSpecification(title="Deterministic Test")
        doc1 = projection.project(spec)
        doc2 = projection.project(spec)
        assert doc1.title == doc2.title
        assert doc1.document_version == doc2.document_version
        assert doc1.document_type == doc2.document_type
        assert len(doc1.sections) == len(doc2.sections)
        assert len(doc1.source_references) == len(doc2.source_references)

    def test_project_with_memory_context(self) -> None:
        store = InMemoryPersistenceStore()
        memory_store = InMemoryMemoryStore(persistence_store=store)
        query = MemoryQuery(object_types=["observation"])
        context = memory_store.get_context(query)

        projection = DeterministicDocumentProjection()
        section_spec = SectionSpecification(
            section_type=SectionType.OBSERVATIONS,
            title="Observations",
            artifact_types=["observation"],
        )
        spec = DocumentSpecification(
            title="Memory Doc",
            requested_sections=[section_spec],
        )
        doc = projection.project(spec, memory_context=context)
        assert doc is not None
        assert len(doc.sections) == 1

    def test_project_with_conflicts(self) -> None:
        from cognitia.distributed.types import CognitiveConflict, ConflictStatus, ConflictType
        conflicts = [
            CognitiveConflict(
                subject_id="hyp_1",
                conflict_type=ConflictType.EPISTEMIC_CONFLICT,
                description="conflicting evidence",
                status=ConflictStatus.OPEN,
            )
        ]
        projection = DeterministicDocumentProjection()
        section_spec = SectionSpecification(
            section_type=SectionType.CONFLICTS,
            title="Conflicts",
        )
        spec = DocumentSpecification(
            title="Conflict Doc",
            requested_sections=[section_spec],
        )
        doc = projection.project(spec, conflicts=conflicts)
        assert doc is not None
        conflict_section = doc.sections[0]
        assert conflict_section.section_type == SectionType.CONFLICTS
        assert len(conflict_section.content) == 1

    def test_project_preserves_source_references(self) -> None:
        store = InMemoryPersistenceStore()
        obs = _make_observation("obs_ref")
        store.save_object(obs)

        memory_store = InMemoryMemoryStore(persistence_store=store)
        query = MemoryQuery(object_types=["observation"])
        context = memory_store.get_context(query)

        projection = DeterministicDocumentProjection()
        spec = DocumentSpecification()
        doc = projection.project(spec, memory_context=context)
        assert len(doc.source_references) == 1
        assert doc.source_references[0].artifact_id == "obs_ref"

    def test_version_document(self) -> None:
        projection = DeterministicDocumentProjection()
        doc = DynamicDocument(title="Versioned Doc")
        version = projection.version_document(
            document=doc,
            specification_hash="sha256:spec",
            state_hash="sha256:state",
        )
        assert version.document_id == doc.id
        assert version.specification_hash == "sha256:spec"
        assert version.state_hash == "sha256:state"

    def test_projection_is_read_only_with_respect_to_source(self) -> None:
        projection = DeterministicDocumentProjection()
        spec = DocumentSpecification()
        doc = projection.project(spec)
        assert not hasattr(doc, "mutate_source")
        assert not hasattr(doc, "write_to_source")


class TestDocumentService:
    def test_project_creates_document(self) -> None:
        service = DocumentService()
        spec = DocumentSpecification(title="Service Test")
        doc = service.project(spec)
        assert doc.id != ""
        assert doc.title == "Service Test"

    def test_refresh_creates_new_projection(self) -> None:
        service = DocumentService()
        spec = DocumentSpecification(title="Original")
        doc = service.project(spec)
        new_doc = service.refresh(spec, doc)
        assert new_doc.id != ""
        assert new_doc.title == "Original"

    def test_diff_unchanged_documents(self) -> None:
        service = DocumentService()
        spec = DocumentSpecification(title="Same")
        doc1 = service.project(spec)
        doc2 = service.project(spec)
        change = service.diff(doc1, doc2)
        assert change.document_id == doc1.id
        assert len(change.changes) > 0

    def test_diff_changed_title(self) -> None:
        service = DocumentService()
        spec1 = DocumentSpecification(title="Title A")
        doc1 = service.project(spec1)
        spec2 = DocumentSpecification(title="Title B")
        doc2 = service.project(spec2)
        change = service.diff(doc1, doc2)
        title_changes = [c for c in change.changes if c.path == "title"]
        assert len(title_changes) == 1
        assert title_changes[0].change_type == ChangeType.CHANGED
        assert title_changes[0].old_value == "Title A"
        assert title_changes[0].new_value == "Title B"

    def test_version_document(self) -> None:
        service = DocumentService()
        spec = DocumentSpecification(title="Versioned")
        doc = service.project(spec)
        version = service.version(doc, specification_hash="sha256:s", state_hash="sha256:st")
        assert version.document_id == doc.id
        assert version.specification_hash == "sha256:s"
        assert version.state_hash == "sha256:st"

    def test_get_document(self) -> None:
        service = DocumentService()
        spec = DocumentSpecification(title="Get Test")
        doc = service.project(spec)
        retrieved = service.get_document(doc.id)
        assert retrieved is not None
        assert retrieved.id == doc.id

    def test_get_document_missing(self) -> None:
        service = DocumentService()
        assert service.get_document("nonexistent") is None

    def test_get_versions_empty(self) -> None:
        service = DocumentService()
        assert service.get_versions("doc_1") == []

    def test_in_memory_document_service(self) -> None:
        service = InMemoryDocumentService()
        spec = DocumentSpecification(title="InMemory Test")
        doc = service.project(spec)
        assert doc is not None
        assert doc.title == "InMemory Test"

    def test_service_does_not_introduce_authority(self) -> None:
        service = DocumentService()
        assert not hasattr(service, "validate_domain")
        assert not hasattr(service, "execute_action")
        assert not hasattr(service, "actuate")


class TestDocumentIntent:
    def test_default_values(self) -> None:
        intent = DocumentIntent()
        assert intent.intent_id != ""
        assert intent.document_id == ""
        assert intent.intent_type == IntentType.ANNOTATE
        assert intent.parameters == ()
        assert intent.rationale is None

    def test_custom_values(self) -> None:
        intent = DocumentIntent(
            document_id="doc_1",
            intent_type=IntentType.REQUEST_REFRESH,
            parameters=[("spec_id", "spec_1")],
            rationale="Need updated view",
        )
        assert intent.document_id == "doc_1"
        assert intent.intent_type == IntentType.REQUEST_REFRESH
        assert intent.parameters_dict == {"spec_id": "spec_1"}
        assert intent.rationale == "Need updated view"

    def test_string_intent_type_conversion(self) -> None:
        intent = DocumentIntent(intent_type="request_projection")
        assert intent.intent_type == IntentType.REQUEST_PROJECTION

    def test_immutable(self) -> None:
        intent = DocumentIntent()
        with pytest.raises(AttributeError):
            intent.rationale = "modified"  # type: ignore[misc]

    def test_has_human_provenance(self) -> None:
        intent = DocumentIntent()
        assert intent.provenance is not None
        assert intent.provenance.source_type == SourceType.HUMAN

    def test_all_intent_types_defined(self) -> None:
        expected = {
            "add_reference",
            "remove_reference",
            "change_section",
            "change_filter",
            "change_order",
            "update_direction",
            "annotate",
            "request_refresh",
            "request_projection",
        }
        actual = {t.value for t in IntentType}
        assert actual == expected


class TestDocumentChange:
    def test_default_values(self) -> None:
        change = DocumentChange()
        assert change.change_id != ""
        assert change.document_id == ""
        assert change.from_version == ""
        assert change.to_version == ""
        assert change.changes == ()

    def test_custom_values(self) -> None:
        entries = (
            ChangeEntry(
                change_type=ChangeType.CHANGED,
                path="title",
                old_value="A",
                new_value="B",
            ),
        )
        change = DocumentChange(
            document_id="doc_1",
            from_version="1.0.0",
            to_version="2.0.0",
            changes=entries,
        )
        assert change.document_id == "doc_1"
        assert change.from_version == "1.0.0"
        assert change.to_version == "2.0.0"
        assert len(change.changes) == 1
        assert change.changes[0].change_type == ChangeType.CHANGED

    def test_string_change_type_conversion(self) -> None:
        entry = ChangeEntry(change_type="added", path="new_field")
        assert entry.change_type == ChangeType.ADDED

    def test_immutable(self) -> None:
        change = DocumentChange()
        with pytest.raises(AttributeError):
            change.from_version = "modified"  # type: ignore[misc]

    def test_has_provenance(self) -> None:
        change = DocumentChange()
        assert change.provenance is not None
        assert change.provenance.source_type == SourceType.DETERMINISTIC_RULE


class TestChangeEntry:
    def test_default_values(self) -> None:
        entry = ChangeEntry()
        assert entry.change_type == ChangeType.UNCHANGED
        assert entry.path == ""
        assert entry.old_value is None
        assert entry.new_value is None
        assert entry.metadata == {}

    def test_custom_values(self) -> None:
        entry = ChangeEntry(
            change_type=ChangeType.REMOVED,
            path="sections.metrics",
            old_value="old_metrics",
            new_value=None,
            metadata={"author": "system"},
        )
        assert entry.change_type == ChangeType.REMOVED
        assert entry.path == "sections.metrics"
        assert entry.old_value == "old_metrics"
        assert entry.new_value is None
        assert entry.metadata["author"] == "system"

    def test_string_change_type_conversion(self) -> None:
        entry = ChangeEntry(change_type="added")
        assert entry.change_type == ChangeType.ADDED


class TestSectionType:
    def test_all_section_types_defined(self) -> None:
        expected = {
            "text",
            "table",
            "timeline",
            "graph",
            "metrics",
            "observations",
            "evidence",
            "hypotheses",
            "claims",
            "reasoning",
            "decisions",
            "direction",
            "conflicts",
            "provenance",
            "residuals",
        }
        actual = {t.value for t in SectionType}
        assert actual == expected

    def test_section_type_values(self) -> None:
        assert SectionType.TEXT.value == "text"
        assert SectionType.METRICS.value == "metrics"
        assert SectionType.CONFLICTS.value == "conflicts"


class TestDocumentCapabilityIntegration:
    def test_provider_implements_capability(self) -> None:
        provider = DeterministicMockDocumentProvider()
        assert isinstance(provider, DeterministicMockDocumentProvider)

    def test_provider_descriptor(self) -> None:
        provider = DeterministicMockDocumentProvider(
            capability_id="custom_doc_provider",
            provider_name="custom",
            version="2.0.0",
        )
        assert provider.descriptor.capability_id == "custom_doc_provider"
        assert provider.descriptor.provider_name == "custom"
        assert provider.descriptor.capability_type == CapabilityType.DYNAMIC_DOCUMENT
        assert provider.descriptor.is_deterministic is True

    def test_provider_projects_document(self) -> None:
        provider = DeterministicMockDocumentProvider()
        spec = DocumentSpecification(title="Provider Test")
        doc = provider.project(spec)
        assert doc is not None
        assert doc.title == "Provider Test"

    def test_provider_projection_deterministic(self) -> None:
        provider = DeterministicMockDocumentProvider()
        spec = DocumentSpecification(title="Det Test")
        doc1 = provider.project(spec)
        doc2 = provider.project(spec)
        assert doc1.title == doc2.title
        assert doc1.document_version == doc2.document_version
        assert doc1.document_type == doc2.document_type
        assert len(doc1.sections) == len(doc2.sections)

    def test_capability_type_registered(self) -> None:
        assert CapabilityType.DYNAMIC_DOCUMENT.value == "dynamic_document"


class TestDocumentContractInvariants:
    def test_document_is_not_memory(self) -> None:
        doc = DynamicDocument()
        assert not hasattr(doc, "recall")
        assert not hasattr(doc, "memory_retrieve")

    def test_document_is_not_persistence(self) -> None:
        doc = DynamicDocument()
        assert not hasattr(doc, "save")
        assert not hasattr(doc, "persist")

    def test_document_is_not_epistemic_authority(self) -> None:
        doc = DynamicDocument()
        assert not hasattr(doc, "validate_epistemic")
        assert not hasattr(doc, "transition_status")

    def test_document_is_not_execution(self) -> None:
        doc = DynamicDocument()
        assert not hasattr(doc, "execute")
        assert not hasattr(doc, "actuate")

    def test_document_intent_is_not_command(self) -> None:
        intent = DocumentIntent(intent_type=IntentType.REQUEST_PROJECTION)
        assert not hasattr(intent, "execute")
        assert not hasattr(intent, "actuate")

    def test_document_preserves_contradictions(self) -> None:
        from cognitia.distributed.types import CognitiveConflict, ConflictStatus, ConflictType
        projection = DeterministicDocumentProjection()
        conflicts = [
            CognitiveConflict(
                subject_id="hyp_1",
                conflict_type=ConflictType.EPISTEMIC_CONFLICT,
                description="conflict A",
                status=ConflictStatus.OPEN,
            ),
            CognitiveConflict(
                subject_id="hyp_1",
                conflict_type=ConflictType.EPISTEMIC_CONFLICT,
                description="conflict B",
                status=ConflictStatus.OPEN,
            ),
        ]
        section_spec = SectionSpecification(
            section_type=SectionType.CONFLICTS,
            title="Conflicts",
        )
        spec = DocumentSpecification(requested_sections=[section_spec])
        doc = projection.project(spec, conflicts=conflicts)
        conflict_section = doc.sections[0]
        assert len(conflict_section.content) == 2

    def test_document_does_not_silently_select_conflict(self) -> None:
        from cognitia.distributed.types import CognitiveConflict, ConflictStatus, ConflictType
        projection = DeterministicDocumentProjection()
        conflicts = [
            CognitiveConflict(
                subject_id="hyp_1",
                conflict_type=ConflictType.EPISTEMIC_CONFLICT,
                description="conflict A",
                status=ConflictStatus.OPEN,
            ),
        ]
        section_spec = SectionSpecification(
            section_type=SectionType.CONFLICTS,
            title="Conflicts",
        )
        spec = DocumentSpecification(requested_sections=[section_spec])
        doc = projection.project(spec, conflicts=conflicts)
        assert doc is not None
        assert len(doc.sections[0].content) == 1

    def test_document_identity_distinct_from_artifact_identity(self) -> None:
        doc = DynamicDocument(title="Identity Test")
        ref = DocumentReference(
            artifact_id="art_1",
            artifact_type="observation",
        )
        assert doc.id != ref.artifact_id
        assert doc.id != ref.reference_id

    def test_projection_does_not_mutate_specification(self) -> None:
        spec = DocumentSpecification(title="Original")
        original_title = spec.title
        projection = DeterministicDocumentProjection()
        projection.project(spec)
        assert spec.title == original_title

    def test_projection_preserves_epistemic_status(self) -> None:
        from cognitia.memory.types import MemoryContext
        projection = DeterministicDocumentProjection()
        hypothesis = Hypothesis(
            statement="Test hypothesis",
            initial_status=EpistemicStatus.HYPOTHESIS,
        )
        memory_context = MemoryContext(hypotheses=[hypothesis])
        section_spec = SectionSpecification(
            section_type=SectionType.HYPOTHESES,
            title="Hypotheses",
        )
        spec = DocumentSpecification(requested_sections=[section_spec])
        doc = projection.project(spec, memory_context=memory_context)
        content = doc.sections[0].content[0]
        assert content.metadata["status"] == "hypothesis"

    def test_document_provenance_regenerated(self) -> None:
        spec = DocumentSpecification(title="Provenance")
        projection = DeterministicDocumentProjection()
        doc1 = projection.project(spec)
        doc2 = projection.project(spec)
        assert doc1.provenance.parent_ids == doc2.provenance.parent_ids
        assert doc1.provenance.is_deterministic is True
        assert doc1.provenance.producer_id == projection._projection_id

    def test_distinct_origin_and_processing_nodes(self) -> None:
        ref = DocumentReference(
            artifact_id="art_1",
            artifact_type="observation",
            origin_node_id="node_origin",
            source_node_id="node_source",
        )
        assert ref.origin_node_id == "node_origin"
        assert ref.source_node_id == "node_source"
        assert ref.origin_node_id != ref.source_node_id

    def test_document_version_distinct_from_artifact_versioning(self) -> None:
        projection = DeterministicDocumentProjection()
        doc = DynamicDocument(title="Version Test")
        v1 = projection.version_document(document=doc, specification_hash="spec_hash", state_hash="state_hash")
        v2 = projection.version_document(document=doc, specification_hash="spec_hash", state_hash="state_hash")
        assert v1.document_version == v2.document_version
        assert v1.document_id == doc.id
        assert v1.document_id != "art_1"


class TestDocumentDeterminism:
    def test_same_spec_same_document(self) -> None:
        projection = DeterministicDocumentProjection()
        spec = DocumentSpecification(title="Det", document_type="test")
        doc1 = projection.project(spec)
        doc2 = projection.project(spec)
        assert doc1.title == doc2.title
        assert doc1.document_version == doc2.document_version
        assert doc1.document_type == doc2.document_type
        assert len(doc1.sections) == len(doc2.sections)

    def test_different_specs_different_documents(self) -> None:
        projection = DeterministicDocumentProjection()
        spec1 = DocumentSpecification(title="A")
        spec2 = DocumentSpecification(title="B")
        doc1 = projection.project(spec1)
        doc2 = projection.project(spec2)
        assert doc1.serialize() != doc2.serialize()

    def test_document_versioning_deterministic(self) -> None:
        projection = DeterministicDocumentProjection()
        doc = DynamicDocument(title="Versioned")
        v1 = projection.version_document(document=doc, specification_hash="hash1", state_hash="hash1")
        v2 = projection.version_document(document=doc, specification_hash="hash1", state_hash="hash1")
        assert v1.document_id == v2.document_id
        assert v1.document_version == v2.document_version
        assert v1.specification_hash == v2.specification_hash
        assert v1.state_hash == v2.state_hash

    def test_service_deterministic_projections(self) -> None:
        service = DocumentService()
        spec = DocumentSpecification(title="Det Service")
        doc1 = service.project(spec)
        doc2 = service.project(spec)
        assert doc1.title == doc2.title
        assert doc1.document_version == doc2.document_version
        assert doc1.document_type == doc2.document_type
        assert len(doc1.sections) == len(doc2.sections)
