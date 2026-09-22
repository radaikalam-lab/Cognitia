"""Cognitia Project Directional Programming Tests."""

from __future__ import annotations

import pathlib

import pytest

from cognitia.project_spec.projection import InMemoryProjectionService, ProjectionService
from cognitia.project_spec.provider import DeterministicProjectionProvider
from cognitia.project_spec.service import InMemoryProjectSpecService
from cognitia.project_spec.types import (
    ArchitectureCandidate,
    Conflict,
    ConflictResolutionPolicy,
    DeliverySemantics,
    DirectionalRule,
    DirectionalRuleStatus,
    DirectionalSpec,
    EvidenceRequest,
    InteractionContract,
    Projection,
    ProjectionResult,
    ProjectionType,
    RelationshipType,
    ScaffoldSpec,
    Traceability,
)


def _make_rule(
    rule_id: str = "PROJECT-AUTH-001",
    version: str = "1.0.0",
    status: DirectionalRuleStatus = DirectionalRuleStatus.DRAFT,
) -> DirectionalRule:
    return DirectionalRule(
        rule_id=rule_id,
        version=version,
        status=status,
        current_state="no project scaffold",
        desired_state="governed project scaffold",
        objectives=["establish project boundaries", "define authority model"],
        constraints=["must not prescribe implementation", "must remain domain-neutral"],
        allowed_authorities=["governance"],
        prohibited_authorities=["implementation_authority"],
        authority_boundaries=["reasoning != approval", "proposal != execution"],
        observables=["boundary_contracts", "test_surfaces"],
        acceptance_conditions=["all boundaries explicit", "no domain leakage"],
        evidence_requirements=["traceability_chain", "validator_evidence"],
        provenance_requirements=["immutable_lineage"],
        implementation_scope="structural scaffold only",
        governance_notes="requires governance acceptance before activation",
        conflict_policy=ConflictResolutionPolicy.ESCALATE_TO_GOVERNANCE.value,
        scaffold_constraints=["required_boundaries", "required_surfaces"],
        technology_freedoms=["any_persistence", "any_test_framework"],
        projection_requirements=["traceability_preserved"],
    )


def _make_spec(rules: list[DirectionalRule] | None = None) -> DirectionalSpec:
    return DirectionalSpec(rules=rules or [_make_rule()])


class TestDirectionalRuleStatus:
    def test_all_statuses_defined(self) -> None:
        expected = {
            "draft",
            "proposed",
            "validated",
            "accepted",
            "rejected",
            "superseded",
            "unresolved",
        }
        actual = {s.value for s in DirectionalRuleStatus}
        assert actual == expected

    def test_status_values(self) -> None:
        assert DirectionalRuleStatus.DRAFT.value == "draft"
        assert DirectionalRuleStatus.ACCEPTED.value == "accepted"
        assert DirectionalRuleStatus.SUPERSEDED.value == "superseded"


class TestDirectionalRule:
    def test_default_values(self) -> None:
        rule = DirectionalRule()
        assert rule.id != ""
        assert rule.rule_id == ""
        assert rule.version == "1.0.0"
        assert rule.status == DirectionalRuleStatus.DRAFT

    def test_custom_values(self) -> None:
        rule = _make_rule()
        assert rule.rule_id == "PROJECT-AUTH-001"
        assert rule.desired_state == "governed project scaffold"
        assert "governance" in rule.allowed_authorities
        assert "implementation_authority" in rule.prohibited_authorities
        assert rule.conflict_policy == ConflictResolutionPolicy.ESCALATE_TO_GOVERNANCE.value

    def test_immutable(self) -> None:
        rule = _make_rule()
        with pytest.raises(AttributeError):
            rule.rule_id = "OTHER"  # type: ignore[misc]

    def test_supersession_fields(self) -> None:
        rule = DirectionalRule(
            rule_id="RULE-OLD",
            supersedes="",
            superseded_by="RULE-NEW",
        )
        assert rule.superseded_by == "RULE-NEW"

    def test_status_string_accepted(self) -> None:
        rule = DirectionalRule(status="accepted")
        assert rule.status == DirectionalRuleStatus.ACCEPTED

    def test_invalid_status_raises(self) -> None:
        with pytest.raises(ValueError):
            DirectionalRule(status="not_a_status")

    def test_provenance_present(self) -> None:
        rule = _make_rule()
        assert rule.provenance is not None
        assert rule.provenance.source_type.value == "deterministic_rule"

    def test_technology_freedoms_preserved(self) -> None:
        rule = _make_rule()
        assert "any_persistence" in rule.technology_freedoms
        assert "any_test_framework" in rule.technology_freedoms

    def test_implementation_scope_not_implementation(self) -> None:
        rule = _make_rule()
        assert "structural scaffold only" in rule.implementation_scope
        assert "class" not in rule.implementation_scope.lower()
        assert "algorithm" not in rule.implementation_scope.lower()


class TestDirectionalSpec:
    def test_default_values(self) -> None:
        spec = DirectionalSpec()
        assert spec.id != ""
        assert spec.rules == ()

    def test_with_rules(self) -> None:
        rule = _make_rule()
        spec = _make_spec([rule])
        assert len(spec.rules) == 1
        assert spec.rules[0].rule_id == "PROJECT-AUTH-001"

    def test_immutable(self) -> None:
        spec = _make_spec()
        with pytest.raises(AttributeError):
            spec.rules = ()  # type: ignore[misc]

    def test_provenance_present(self) -> None:
        spec = _make_spec()
        assert spec.provenance is not None
        assert spec.provenance.source_type.value == "deterministic_rule"


class TestArchitectureCandidate:
    def test_default_values(self) -> None:
        candidate = ArchitectureCandidate()
        assert candidate.id != ""
        assert candidate.candidate_id == ""
        assert candidate.boundaries == ()

    def test_custom_values(self) -> None:
        candidate = ArchitectureCandidate(
            candidate_id="arch-001",
            boundaries=["boundary_a", "boundary_b"],
            authorities=["governance"],
            responsibilities=["resp1"],
            dependencies=["dep1"],
            invariants=["inv1"],
            required_capabilities=["cap1"],
            prohibited_dependencies=["forbidden_dep"],
            observables=["obs1"],
            validation_requirements=["val1"],
            traceability=["PROJECT-AUTH-001"],
        )
        assert candidate.candidate_id == "arch-001"
        assert "boundary_a" in candidate.boundaries
        assert "governance" in candidate.authorities
        assert "PROJECT-AUTH-001" in candidate.traceability

    def test_immutable(self) -> None:
        candidate = ArchitectureCandidate()
        with pytest.raises(AttributeError):
            candidate.boundaries = ()  # type: ignore[misc]

    def test_no_domain_entities(self) -> None:
        candidate = ArchitectureCandidate(
            responsibilities=["PrintJob", "Speaker", "Invoice"],
        )
        assert "PrintJob" in candidate.responsibilities


class TestScaffoldSpec:
    def test_default_values(self) -> None:
        scaffold = ScaffoldSpec()
        assert scaffold.id != ""
        assert scaffold.spec_id == ""
        assert scaffold.required_boundaries == ()

    def test_custom_values(self) -> None:
        scaffold = ScaffoldSpec(
            spec_id="scf-001",
            required_boundaries=["b1"],
            required_surfaces=["s1"],
            required_interfaces=["i1"],
            required_contract_surfaces=["c1"],
            required_test_surfaces=["t1"],
            prohibited_structural_patterns=["monolith"],
            implementation_freedoms=["any_persistence"],
            traceability=["arch-001"],
        )
        assert scaffold.spec_id == "scf-001"
        assert "monolith" in scaffold.prohibited_structural_patterns
        assert "any_persistence" in scaffold.implementation_freedoms

    def test_immutable(self) -> None:
        scaffold = ScaffoldSpec()
        with pytest.raises(AttributeError):
            scaffold.required_boundaries = ()  # type: ignore[misc]


class TestProjection:
    def test_default_values(self) -> None:
        proj = Projection()
        assert proj.id != ""
        assert proj.source_id == ""
        assert proj.target_id == ""

    def test_custom_values(self) -> None:
        proj = Projection(
            source_id="rule-1",
            target_id="arch-1",
            projection_type=ProjectionType.RULE_TO_ARCHITECTURE.value,
            source_references=["rule-1"],
            result_references=["arch-1"],
        )
        assert proj.projection_type == ProjectionType.RULE_TO_ARCHITECTURE.value
        assert "rule-1" in proj.source_references

    def test_immutable(self) -> None:
        proj = Projection()
        with pytest.raises(AttributeError):
            proj.source_id = "other"  # type: ignore[misc]


class TestEvidenceRequest:
    def test_default_values(self) -> None:
        req = EvidenceRequest()
        assert req.id != ""
        assert req.request_id == ""
        assert req.evidence_type == ""

    def test_custom_values(self) -> None:
        req = EvidenceRequest(
            request_id="EVID-001",
            rule_id="RULE-1",
            projection_id="PROJ-1",
            evidence_type="boundary_contract",
            acceptance_condition="contract must be present",
        )
        assert req.request_id == "EVID-001"
        assert req.evidence_type == "boundary_contract"


class TestConflict:
    def test_default_values(self) -> None:
        conflict = Conflict()
        assert conflict.id != ""
        assert conflict.conflict_id == ""
        assert conflict.resolution_status == "open"
        assert conflict.governance_required is True

    def test_custom_values(self) -> None:
        conflict = Conflict(
            conflict_id="CONF-001",
            rules_in_conflict=["RULE-1", "RULE-2"],
            description="contradictory authorities",
            affected_projection="PROJ-1",
            severity="high",
            resolution_status="open",
            governance_required=True,
        )
        assert conflict.conflict_id == "CONF-001"
        assert conflict.severity == "high"
        assert conflict.governance_required is True

    def test_immutable(self) -> None:
        conflict = Conflict()
        with pytest.raises(AttributeError):
            conflict.resolution_status = "resolved"  # type: ignore[misc]


class TestTraceability:
    def test_default_values(self) -> None:
        link = Traceability()
        assert link.id != ""
        assert link.source_id == ""
        assert link.target_id == ""
        assert link.relationship == ""

    def test_custom_values(self) -> None:
        link = Traceability(
            source_id="RULE-1",
            target_id="ARCH-1",
            relationship=RelationshipType.DERIVES.value,
        )
        assert link.source_id == "RULE-1"
        assert link.target_id == "ARCH-1"
        assert link.relationship == RelationshipType.DERIVES.value

    def test_immutable(self) -> None:
        link = Traceability()
        with pytest.raises(AttributeError):
            link.relationship = "other"  # type: ignore[misc]


class TestInMemoryProjectSpecService:
    def test_create_specification(self) -> None:
        service = InMemoryProjectSpecService()
        rule = _make_rule()
        spec = service.create_specification(rules=[rule])
        assert spec.id != ""
        assert len(spec.rules) == 1

    def test_get_specification(self) -> None:
        service = InMemoryProjectSpecService()
        spec = service.create_specification(rules=[_make_rule()])
        retrieved = service.get_specification(spec.id)
        assert retrieved is not None
        assert retrieved.id == spec.id

    def test_list_specifications(self) -> None:
        service = InMemoryProjectSpecService()
        service.create_specification(rules=[_make_rule("R1")])
        service.create_specification(rules=[_make_rule("R2")])
        assert len(service.list_specifications()) == 2

    def test_add_rule(self) -> None:
        service = InMemoryProjectSpecService()
        spec = service.create_specification(rules=[_make_rule("R1")])
        updated = service.add_rule(spec.id, _make_rule("R2"))
        assert len(updated.rules) == 2

    def test_add_rule_missing_spec_raises(self) -> None:
        service = InMemoryProjectSpecService()
        with pytest.raises(KeyError):
            service.add_rule("missing", _make_rule("R1"))

    def test_create_architecture_candidate(self) -> None:
        service = InMemoryProjectSpecService()
        spec = service.create_specification(rules=[_make_rule()])
        candidate = ArchitectureCandidate(candidate_id="arch-1")
        result = service.create_architecture_candidate(spec.id, candidate)
        assert result.candidate_id == "arch-1"

    def test_get_architecture_candidate(self) -> None:
        service = InMemoryProjectSpecService()
        spec = service.create_specification(rules=[_make_rule()])
        candidate = ArchitectureCandidate(candidate_id="arch-1")
        service.create_architecture_candidate(spec.id, candidate)
        retrieved = service.get_architecture_candidate("arch-1")
        assert retrieved is not None
        assert retrieved.candidate_id == "arch-1"

    def test_create_scaffold_spec(self) -> None:
        service = InMemoryProjectSpecService()
        spec = service.create_specification(rules=[_make_rule()])
        candidate = ArchitectureCandidate(candidate_id="arch-1")
        service.create_architecture_candidate(spec.id, candidate)
        scaffold = ScaffoldSpec(spec_id="scf-1")
        result = service.create_scaffold_spec("arch-1", scaffold)
        assert result.spec_id == "scf-1"

    def test_get_scaffold_spec(self) -> None:
        service = InMemoryProjectSpecService()
        spec = service.create_specification(rules=[_make_rule()])
        candidate = ArchitectureCandidate(candidate_id="arch-1")
        service.create_architecture_candidate(spec.id, candidate)
        scaffold = ScaffoldSpec(spec_id="scf-1")
        service.create_scaffold_spec("arch-1", scaffold)
        retrieved = service.get_scaffold_spec("scf-1")
        assert retrieved is not None
        assert retrieved.spec_id == "scf-1"

    def test_create_projection(self) -> None:
        service = InMemoryProjectSpecService()
        proj = service.create_projection(
            source_id="rule-1",
            target_id="arch-1",
            projection_type=ProjectionType.RULE_TO_ARCHITECTURE.value,
        )
        assert proj.source_id == "rule-1"
        assert proj.target_id == "arch-1"

    def test_get_projection(self) -> None:
        service = InMemoryProjectSpecService()
        proj = service.create_projection("r1", "a1", ProjectionType.RULE_TO_ARCHITECTURE.value)
        retrieved = service.get_projection(proj.id)
        assert retrieved is not None
        assert retrieved.source_id == "r1"

    def test_create_evidence_request(self) -> None:
        service = InMemoryProjectSpecService()
        req = service.create_evidence_request(
            rule_id="RULE-1",
            projection_id="PROJ-1",
            evidence_type="boundary_contract",
            acceptance_condition="contract present",
        )
        assert req.rule_id == "RULE-1"
        assert req.evidence_type == "boundary_contract"

    def test_create_conflict(self) -> None:
        service = InMemoryProjectSpecService()
        conflict = service.create_conflict(
            rules_in_conflict=["RULE-1", "RULE-2"],
            description="overlap",
            affected_projection="PROJ-1",
            severity="high",
        )
        assert conflict.id != ""
        assert conflict.rules_in_conflict == ("RULE-1", "RULE-2")
        assert conflict.governance_required is True

    def test_add_traceability(self) -> None:
        service = InMemoryProjectSpecService()
        link = service.add_traceability(
            source_id="RULE-1",
            target_id="ARCH-1",
            relationship=RelationshipType.DERIVES.value,
        )
        assert link.source_id == "RULE-1"
        assert link.target_id == "ARCH-1"

    def test_get_traceability(self) -> None:
        service = InMemoryProjectSpecService()
        service.add_traceability("RULE-1", "ARCH-1", RelationshipType.DERIVES.value)
        service.add_traceability("RULE-1", "SCF-1", RelationshipType.IMPLEMENTS.value)
        links = service.get_traceability("RULE-1")
        assert len(links) == 2

    def test_get_reverse_traceability(self) -> None:
        service = InMemoryProjectSpecService()
        service.add_traceability("RULE-1", "ARCH-1", RelationshipType.DERIVES.value)
        links = service.get_reverse_traceability("ARCH-1")
        assert len(links) == 1
        assert links[0].source_id == "RULE-1"


class TestDeterministicProjectionProvider:
    def test_provider_attributes(self) -> None:
        provider = DeterministicProjectionProvider(
            provider_id="custom_provider",
            provider_version="2.0.0",
        )
        assert provider.provider_id == "custom_provider"
        assert provider.provider_version == "2.0.0"

    def test_project_rule_to_architecture(self) -> None:
        provider = DeterministicProjectionProvider()
        rule = _make_rule()
        candidate = provider.project_rule_to_architecture(rule)
        assert isinstance(candidate, ArchitectureCandidate)
        assert "governance" in candidate.authorities
        assert "prohibited_authority:implementation_authority" in candidate.prohibited_dependencies

    def test_project_architecture_to_scaffold(self) -> None:
        provider = DeterministicProjectionProvider()
        candidate = ArchitectureCandidate(
            candidate_id="arch-1",
            boundaries=["b1"],
            authorities=["gov"],
            required_capabilities=["cap1"],
            validation_requirements=["val1"],
            prohibited_dependencies=["forbidden"],
        )
        scaffold = provider.project_architecture_to_scaffold(candidate)
        assert isinstance(scaffold, ScaffoldSpec)
        assert "b1" in scaffold.required_boundaries
        assert "cap1" in scaffold.required_interfaces
        assert "forbidden" in scaffold.prohibited_structural_patterns

    def test_detect_conflicts_overlapping_authorities(self) -> None:
        provider = DeterministicProjectionProvider()
        rule_a = DirectionalRule(
            rule_id="RULE-A",
            allowed_authorities=["governance"],
            prohibited_authorities=["implementation"],
        )
        rule_b = DirectionalRule(
            rule_id="RULE-B",
            allowed_authorities=["implementation"],
            prohibited_authorities=[],
        )
        conflicts = provider.detect_conflicts([rule_a, rule_b])
        assert len(conflicts) == 1
        assert conflicts[0].governance_required is True

    def test_detect_no_conflicts(self) -> None:
        provider = DeterministicProjectionProvider()
        rule_a = DirectionalRule(
            rule_id="RULE-A",
            allowed_authorities=["governance"],
            prohibited_authorities=["implementation"],
        )
        rule_b = DirectionalRule(
            rule_id="RULE-B",
            allowed_authorities=["governance"],
            prohibited_authorities=[],
        )
        conflicts = provider.detect_conflicts([rule_a, rule_b])
        assert len(conflicts) == 0

    def test_build_traceability(self) -> None:
        provider = DeterministicProjectionProvider()
        link = provider.build_traceability(
            source_id="RULE-1",
            target_id="ARCH-1",
            relationship=RelationshipType.DERIVES.value,
        )
        assert isinstance(link, Traceability)
        assert link.source_id == "RULE-1"
        assert link.target_id == "ARCH-1"

    def test_deterministic_output(self) -> None:
        provider = DeterministicProjectionProvider()
        rule = _make_rule()
        c1 = provider.project_rule_to_architecture(rule)
        c2 = provider.project_rule_to_architecture(rule)
        assert c1.boundaries == c2.boundaries
        assert c1.authorities == c2.authorities
        assert c1.traceability == c2.traceability


class TestProjectSpecDeterminism:
    def test_rule_deterministic(self) -> None:
        r1 = DirectionalRule(rule_id="R1", version="1.0.0", status=DirectionalRuleStatus.DRAFT)
        r2 = DirectionalRule(rule_id="R1", version="1.0.0", status=DirectionalRuleStatus.DRAFT)
        assert r1.rule_id == r2.rule_id
        assert r1.status == r2.status

    def test_spec_deterministic(self) -> None:
        rule = _make_rule("R1")
        s1 = DirectionalSpec(rules=[rule])
        s2 = DirectionalSpec(rules=[rule])
        assert s1.rules == s2.rules

    def test_candidate_deterministic(self) -> None:
        c1 = ArchitectureCandidate(candidate_id="a1", boundaries=["b1"])
        c2 = ArchitectureCandidate(candidate_id="a1", boundaries=["b1"])
        assert c1.boundaries == c2.boundaries
        assert c1.candidate_id == c2.candidate_id

    def test_scaffold_deterministic(self) -> None:
        s1 = ScaffoldSpec(spec_id="s1", required_boundaries=["b1"])
        s2 = ScaffoldSpec(spec_id="s1", required_boundaries=["b1"])
        assert s1.required_boundaries == s2.required_boundaries

    def test_serialization_deterministic(self) -> None:
        rule = _make_rule()
        first = rule.serialize()
        second = rule.serialize()
        assert first == second


class TestProjectSpecDomainNeutrality:
    FORBIDDEN_TERMS = [
        "PrintForge",
        "AcoustiForge",
        "FJH",
        "Frappe",
        "ERPNext",
        "speaker",
        "printer",
        "reactor",
        "farm",
        "Oracle",
        "FastAPI",
        "PostgreSQL",
        "Django",
        "REST",
        "HTTP",
        "SalesOrder",
        "PurchaseOrder",
        "Invoice",
        "Customer",
        "DocType",
        "chamber",
        "experiment",
        "actuator",
    ]

    @pytest.fixture
    def project_spec_source_files(self) -> list[pathlib.Path]:
        src_dir = pathlib.Path(__file__).resolve().parents[1] / "src" / "cognitia" / "project_spec"
        return list(src_dir.rglob("*.py"))

    def test_no_forbidden_domain_terms(self, project_spec_source_files: list[pathlib.Path]) -> None:
        violations = []
        for file_path in project_spec_source_files:
            text = file_path.read_text(encoding="utf-8")
            for term in self.FORBIDDEN_TERMS:
                if term in text:
                    violations.append((file_path, term))
        assert violations == [], f"Forbidden domain terms found: {violations}"


class TestProjectionResult:
    def test_default_values(self) -> None:
        result = ProjectionResult()
        assert result.id != ""
        assert result.specification_id == ""
        assert result.architecture_candidate is None
        assert result.scaffold_spec is None
        assert result.projections == ()
        assert result.traceability == ()
        assert result.conflicts == ()

    def test_custom_values(self) -> None:
        candidate = ArchitectureCandidate(candidate_id="arch-1")
        scaffold = ScaffoldSpec(spec_id="scf-1")
        proj = Projection(
            source_id="rule-1",
            target_id="arch-1",
            projection_type=ProjectionType.RULE_TO_ARCHITECTURE.value,
        )
        link = Traceability(
            source_id="rule-1",
            target_id="arch-1",
            relationship=RelationshipType.DERIVES.value,
        )
        result = ProjectionResult(
            specification_id="spec-1",
            architecture_candidate=candidate,
            scaffold_spec=scaffold,
            projections=[proj],
            traceability=[link],
        )
        assert result.specification_id == "spec-1"
        assert result.architecture_candidate is not None
        assert result.scaffold_spec is not None
        assert len(result.projections) == 1
        assert len(result.traceability) == 1

    def test_immutable(self) -> None:
        result = ProjectionResult()
        with pytest.raises(AttributeError):
            result.specification_id = "other"  # type: ignore[misc]

    def test_provenance_present(self) -> None:
        result = ProjectionResult()
        assert result.provenance is not None
        assert result.provenance.source_type.value == "reasoning_engine"


class TestInMemoryProjectionService:
    def test_project_returns_projection_result(self) -> None:
        service = InMemoryProjectionService()
        spec = _make_spec()
        result = service.project(spec)
        assert isinstance(result, ProjectionResult)

    def test_project_produces_architecture_candidate(self) -> None:
        service = InMemoryProjectionService()
        spec = _make_spec()
        result = service.project(spec)
        assert result.architecture_candidate is not None
        assert isinstance(result.architecture_candidate, ArchitectureCandidate)

    def test_project_produces_scaffold_spec(self) -> None:
        service = InMemoryProjectionService()
        spec = _make_spec()
        result = service.project(spec)
        assert result.scaffold_spec is not None
        assert isinstance(result.scaffold_spec, ScaffoldSpec)

    def test_project_produces_projections(self) -> None:
        service = InMemoryProjectionService()
        spec = _make_spec()
        result = service.project(spec)
        assert len(result.projections) > 0
        assert all(isinstance(p, Projection) for p in result.projections)

    def test_project_produces_traceability(self) -> None:
        service = InMemoryProjectionService()
        spec = _make_spec()
        result = service.project(spec)
        assert len(result.traceability) > 0
        assert all(isinstance(t, Traceability) for t in result.traceability)

    def test_project_specification_id_set(self) -> None:
        service = InMemoryProjectionService()
        spec = _make_spec()
        result = service.project(spec)
        assert result.specification_id == spec.id

    def test_project_rule_to_architecture_projection(self) -> None:
        service = InMemoryProjectionService()
        rule = _make_rule()
        spec = DirectionalSpec(rules=[rule])
        result = service.project(spec)
        rule_proj = [p for p in result.projections if p.projection_type == ProjectionType.RULE_TO_ARCHITECTURE.value]
        assert len(rule_proj) == 1
        assert rule_proj[0].source_id == rule.rule_id

    def test_project_architecture_to_scaffold_projection(self) -> None:
        service = InMemoryProjectionService()
        spec = _make_spec()
        result = service.project(spec)
        arch_to_scaffold = [p for p in result.projections if p.projection_type == ProjectionType.ARCHITECTURE_TO_SCAFFOLD.value]
        assert len(arch_to_scaffold) == 1

    def test_project_detects_conflicts(self) -> None:
        service = InMemoryProjectionService()
        rule_a = DirectionalRule(
            rule_id="RULE-A",
            allowed_authorities=["governance"],
            prohibited_authorities=["implementation"],
        )
        rule_b = DirectionalRule(
            rule_id="RULE-B",
            allowed_authorities=["implementation"],
            prohibited_authorities=[],
        )
        spec = DirectionalSpec(rules=[rule_a, rule_b])
        result = service.project(spec)
        assert len(result.conflicts) > 0
        assert all(isinstance(c, Conflict) for c in result.conflicts)

    def test_project_no_conflicts_when_none(self) -> None:
        service = InMemoryProjectionService()
        spec = _make_spec()
        result = service.project(spec)
        assert len(result.conflicts) == 0

    def test_project_traceability_chain_rule_to_architecture(self) -> None:
        service = InMemoryProjectionService()
        rule = _make_rule()
        spec = DirectionalSpec(rules=[rule])
        result = service.project(spec)
        rule_links = [t for t in result.traceability if t.source_id == rule.rule_id]
        assert len(rule_links) >= 1
        assert any(t.relationship == RelationshipType.DERIVES.value for t in rule_links)

    def test_project_traceability_chain_architecture_to_scaffold(self) -> None:
        service = InMemoryProjectionService()
        spec = _make_spec()
        result = service.project(spec)
        arch = result.architecture_candidate
        assert arch is not None
        arch_id = arch.candidate_id or arch.id
        arch_to_scaffold = [
            t for t in result.traceability
            if t.source_id == arch_id
            and t.relationship == RelationshipType.IMPLEMENTS.value
        ]
        assert len(arch_to_scaffold) == 1

    def test_project_implementation_freedoms_preserved(self) -> None:
        service = InMemoryProjectionService()
        rule = _make_rule()
        spec = DirectionalSpec(rules=[rule])
        result = service.project(spec)
        assert result.scaffold_spec is not None
        assert "any_persistence" in result.scaffold_spec.implementation_freedoms
        assert "any_test_framework" in result.scaffold_spec.implementation_freedoms

    def test_project_does_not_generate_code(self) -> None:
        service = InMemoryProjectionService()
        spec = _make_spec()
        result = service.project(spec)
        assert not hasattr(result, "source_files")
        assert not hasattr(result, "repository_url")
        assert not hasattr(result, "package_name")
        assert not hasattr(result, "deployment_manifest")

    def test_project_candidate_not_accepted(self) -> None:
        service = InMemoryProjectionService()
        spec = _make_spec()
        result = service.project(spec)
        assert result.architecture_candidate is not None
        assert not hasattr(result.architecture_candidate, "accepted_at")
        assert not hasattr(result.architecture_candidate, "approved_by")

    def test_project_scaffold_not_code(self) -> None:
        service = InMemoryProjectionService()
        spec = _make_spec()
        result = service.project(spec)
        assert result.scaffold_spec is not None
        assert not hasattr(result.scaffold_spec, "class_names")
        assert not hasattr(result.scaffold_spec, "file_tree")
        assert not hasattr(result.scaffold_spec, "dependency_versions")

    def test_project_deterministic_output(self) -> None:
        service = InMemoryProjectionService()
        rule = _make_rule()
        spec = DirectionalSpec(rules=[rule])
        r1 = service.project(spec)
        r2 = service.project(spec)
        assert r1.specification_id == r2.specification_id
        assert r1.architecture_candidate is not None
        assert r2.architecture_candidate is not None
        assert r1.architecture_candidate.boundaries == r2.architecture_candidate.boundaries
        assert r1.architecture_candidate.authorities == r2.architecture_candidate.authorities
        assert r1.scaffold_spec is not None
        assert r2.scaffold_spec is not None
        assert r1.scaffold_spec.required_boundaries == r2.scaffold_spec.required_boundaries
        assert len(r1.projections) == len(r2.projections)
        assert len(r1.traceability) == len(r2.traceability)

    def test_project_with_multiple_rules(self) -> None:
        service = InMemoryProjectionService()
        rule1 = _make_rule("RULE-1")
        rule2 = _make_rule("RULE-2")
        spec = DirectionalSpec(rules=[rule1, rule2])
        result = service.project(spec)
        assert result.architecture_candidate is not None
        assert "RULE-1" in result.architecture_candidate.traceability
        assert "RULE-2" in result.architecture_candidate.traceability
        assert result.scaffold_spec is not None
        assert len(result.projections) >= 2

    def test_project_merge_candidates_preserves_all_boundaries(self) -> None:
        service = InMemoryProjectionService()
        rule1 = DirectionalRule(
            rule_id="RULE-1",
            authority_boundaries=["boundary_a"],
            allowed_authorities=["auth_a"],
        )
        rule2 = DirectionalRule(
            rule_id="RULE-2",
            authority_boundaries=["boundary_b"],
            allowed_authorities=["auth_b"],
        )
        spec = DirectionalSpec(rules=[rule1, rule2])
        result = service.project(spec)
        assert result.architecture_candidate is not None
        assert "boundary_a" in result.architecture_candidate.boundaries
        assert "boundary_b" in result.architecture_candidate.boundaries
        assert "auth_a" in result.architecture_candidate.authorities
        assert "auth_b" in result.architecture_candidate.authorities

    def test_project_result_does_not_perform_validation(self) -> None:
        service = InMemoryProjectionService()
        spec = _make_spec()
        result = service.project(spec)
        assert not hasattr(result, "validate")
        assert not hasattr(result, "approve")
        assert not hasattr(result, "accept")

    def test_project_result_does_not_generate_files(self) -> None:
        service = InMemoryProjectionService()
        spec = _make_spec()
        result = service.project(spec)
        assert not hasattr(result, "write_file")
        assert not hasattr(result, "create_repository")
        assert not hasattr(result, "install_dependencies")


class TestProjectionDirectionVsImplementation:
    def test_two_different_interpretations_both_pass_validation(self) -> None:
        from cognitia.project_spec.types import ArchitectureCandidate, ScaffoldSpec
        from validator.project_spec_validator import DeterministicProjectSpecValidator

        validator = DeterministicProjectSpecValidator()

        rule = DirectionalRule(
            rule_id="RULE-FREE",
            technology_freedoms=["any_persistence", "any_test_framework", "any_interface"],
            allowed_authorities=["governance"],
            authority_boundaries=["reasoning != approval"],
            objectives=["establish boundaries"],
            constraints=["must not prescribe implementation"],
            projection_requirements=["traceability_preserved"],
        )
        spec = DirectionalSpec(rules=[rule])

        candidate_a = ArchitectureCandidate(
            candidate_id="candidate-a",
            boundaries=["reasoning != approval"],
            authorities=["governance"],
            responsibilities=["establish boundaries", "must not prescribe implementation"],
            required_capabilities=["traceability_preserved"],
            prohibited_dependencies=[],
            traceability=["RULE-FREE"],
        )
        scaffold_a = ScaffoldSpec(
            spec_id="scf-a",
            required_boundaries=["reasoning != approval"],
            required_surfaces=["governance"],
            required_interfaces=["traceability_preserved"],
            implementation_freedoms=["any_persistence", "any_test_framework"],
            traceability=["candidate-a"],
        )

        candidate_b = ArchitectureCandidate(
            candidate_id="candidate-b",
            boundaries=["reasoning != approval", "extra_boundary"],
            authorities=["governance", "extra_authority"],
            responsibilities=["establish boundaries", "must not prescribe implementation", "extra_resp"],
            required_capabilities=["traceability_preserved", "extra_cap"],
            prohibited_dependencies=[],
            traceability=["RULE-FREE", "extra_trace"],
        )
        scaffold_b = ScaffoldSpec(
            spec_id="scf-b",
            required_boundaries=["reasoning != approval", "extra_boundary"],
            required_surfaces=["governance", "extra_authority"],
            required_interfaces=["traceability_preserved", "extra_cap"],
            implementation_freedoms=["any_persistence", "any_test_framework", "any_interface"],
            traceability=["candidate-b"],
        )

        result_a = validator.validate(
            specification=spec,
            candidate=candidate_a,
            scaffold=scaffold_a,
        )
        result_b = validator.validate(
            specification=spec,
            candidate=candidate_b,
            scaffold=scaffold_b,
        )

        assert result_a.status == "pass"
        assert result_b.status == "pass"

    def test_projection_does_not_prescribe_implementation_technology(self) -> None:
        service = InMemoryProjectionService()
        rule = DirectionalRule(
            rule_id="RULE-TECH-FREE",
            technology_freedoms=["any_persistence", "any_framework"],
            allowed_authorities=["governance"],
            authority_boundaries=["reasoning != approval"],
            objectives=["establish boundaries"],
            constraints=["must not prescribe implementation"],
            projection_requirements=["traceability_preserved"],
        )
        spec = DirectionalSpec(rules=[rule])
        result = service.project(spec)
        assert result.scaffold_spec is not None
        forbidden_tech_terms = ["python", "fastapi", "postgresql", "docker", "kubernetes", "rest", "graphql"]
        scaffold_text = str(result.scaffold_spec.serialize()).lower()
        for term in forbidden_tech_terms:
            assert term not in scaffold_text, f"Scaffold prescribes forbidden technology: {term}"


class TestProjectionGenericity:
    def test_generic_domain_neutral_specification(self) -> None:
        service = InMemoryProjectionService()
        rule = DirectionalRule(
            rule_id="PROJECT-AUTH-001",
            objectives=["establish authority boundary", "define provider boundary"],
            constraints=["must not prescribe implementation", "must remain domain-neutral"],
            allowed_authorities=["governance"],
            prohibited_authorities=["implementation_authority"],
            authority_boundaries=["reasoning != approval", "proposal != execution"],
            observables=["boundary_contracts", "test_surfaces"],
            acceptance_conditions=["all boundaries explicit"],
            evidence_requirements=["traceability_chain"],
            provenance_requirements=["immutable_lineage"],
            implementation_scope="structural scaffold only",
            governance_notes="requires governance acceptance",
            conflict_policy="escalate_to_governance",
            scaffold_constraints=["required_boundaries", "required_surfaces"],
            technology_freedoms=["any_persistence", "any_test_framework"],
            projection_requirements=["traceability_preserved"],
        )
        spec = DirectionalSpec(rules=[rule])
        result = service.project(spec)
        assert result.architecture_candidate is not None
        assert result.scaffold_spec is not None
        forbidden_terms = ["PrintForge", "AcoustiForge", "FJH", "Frappe", "printer", "speaker", "reactor"]
        spec_text = str(spec.serialize()).lower()
        result_text = str(result.architecture_candidate.serialize()).lower() + str(result.scaffold_spec.serialize()).lower()
        for term in forbidden_terms:
            assert term.lower() not in spec_text
            assert term.lower() not in result_text


class TestDeliverySemantics:
    def test_all_statuses_defined(self) -> None:
        expected = {"at_most_once", "at_least_once", "exactly_once", "unspecified"}
        actual = {s.value for s in DeliverySemantics}
        assert actual == expected

    def test_default_is_unspecified(self) -> None:
        assert DeliverySemantics.UNSPECIFIED.value == "unspecified"


class TestInteractionContract:
    def test_default_values(self) -> None:
        contract = InteractionContract()
        assert contract.id != ""
        assert contract.contract_id == ""
        assert contract.boundary == ""
        assert contract.canonical_representation == ""
        assert contract.translation_required is False
        assert contract.delivery_semantics == DeliverySemantics.UNSPECIFIED.value
        assert contract.idempotency_required is False
        assert contract.observables == ()

    def test_custom_values(self) -> None:
        contract = InteractionContract(
            contract_id="IC-001",
            boundary="provider_boundary",
            canonical_representation="canonical_contract",
            translation_required=True,
            delivery_semantics=DeliverySemantics.AT_LEAST_ONCE.value,
            idempotency_required=True,
            observables=["duplicate_events"],
        )
        assert contract.contract_id == "IC-001"
        assert contract.boundary == "provider_boundary"
        assert contract.translation_required is True
        assert contract.delivery_semantics == DeliverySemantics.AT_LEAST_ONCE.value
        assert contract.idempotency_required is True
        assert "duplicate_events" in contract.observables

    def test_immutable(self) -> None:
        contract = InteractionContract()
        with pytest.raises(AttributeError):
            contract.boundary = "other"  # type: ignore[misc]

    def test_provenance_present(self) -> None:
        contract = InteractionContract()
        assert contract.provenance is not None
        assert contract.provenance.source_type.value == "deterministic_rule"


class TestDirectionalRuleInteractionContracts:
    def test_default_empty(self) -> None:
        rule = DirectionalRule()
        assert rule.interaction_contracts == ()

    def test_with_interaction_contracts(self) -> None:
        contract = InteractionContract(
            contract_id="IC-001",
            boundary="provider_boundary",
            delivery_semantics=DeliverySemantics.AT_LEAST_ONCE.value,
            idempotency_required=True,
        )
        rule = DirectionalRule(
            rule_id="RULE-1",
            interaction_contracts=[contract],
        )
        assert len(rule.interaction_contracts) == 1
        assert rule.interaction_contracts[0].contract_id == "IC-001"


class TestArchitectureCandidateInteractionContracts:
    def test_default_empty(self) -> None:
        candidate = ArchitectureCandidate()
        assert candidate.interaction_contracts == ()

    def test_with_interaction_contracts(self) -> None:
        candidate = ArchitectureCandidate(
            candidate_id="arch-1",
            interaction_contracts=["IC-001", "IC-002"],
        )
        assert "IC-001" in candidate.interaction_contracts
        assert "IC-002" in candidate.interaction_contracts


class TestScaffoldSpecInteractionContracts:
    def test_default_empty(self) -> None:
        scaffold = ScaffoldSpec()
        assert scaffold.interaction_contracts == ()

    def test_with_interaction_contracts(self) -> None:
        scaffold = ScaffoldSpec(
            spec_id="scf-1",
            interaction_contracts=["IC-001"],
        )
        assert "IC-001" in scaffold.interaction_contracts


class TestProjectionInteractionContracts:
    def test_projection_carries_interaction_contracts(self) -> None:
        service = InMemoryProjectionService()
        contract = InteractionContract(
            contract_id="IC-001",
            boundary="provider_boundary",
            delivery_semantics=DeliverySemantics.AT_LEAST_ONCE.value,
            idempotency_required=True,
        )
        rule = DirectionalRule(
            rule_id="RULE-1",
            interaction_contracts=[contract],
        )
        spec = DirectionalSpec(rules=[rule])
        result = service.project(spec)
        assert result.architecture_candidate is not None
        assert "IC-001" in result.architecture_candidate.interaction_contracts
        assert result.scaffold_spec is not None
        assert "IC-001" in result.scaffold_spec.interaction_contracts

    def test_projection_without_interaction_contracts(self) -> None:
        service = InMemoryProjectionService()
        rule = DirectionalRule(rule_id="RULE-1")
        spec = DirectionalSpec(rules=[rule])
        result = service.project(spec)
        assert result.architecture_candidate is not None
        assert result.architecture_candidate.interaction_contracts == ()
        assert result.scaffold_spec is not None
        assert result.scaffold_spec.interaction_contracts == ()
