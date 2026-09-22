"""PrintForge Cross-Domain Controlled Pilot Tests.

Tests the ability of the generic DP framework to express PrintForge
architectural intent without embedding PrintForge-specific semantics
into the generic kernel.
"""

from __future__ import annotations

import pathlib

import pytest

from cognitia.project_spec.types import (
    ArchitectureCandidate,
    DeliverySemantics,
    DirectionalRule,
    DirectionalRuleStatus,
    DirectionalSpec,
    InteractionContract,
    RelationshipType,
    ScaffoldSpec,
    Traceability,
)
from pilot_printforge.direction_extraction import PrintForgeDirectionExtractor
from validator.types import ValidationResult, ValidationStatus


class TestPrintForgeDirectionExtraction:
    """Test that PrintForge architectural concepts are extracted into generic rules."""

    @pytest.fixture
    def extractor(self) -> PrintForgeDirectionExtractor:
        return PrintForgeDirectionExtractor()

    @pytest.fixture
    def extracted_spec(self, extractor: PrintForgeDirectionExtractor) -> DirectionalSpec:
        return extractor.build_directional_spec()

    @pytest.fixture
    def extracted_rules(self, extracted_spec: DirectionalSpec) -> list[DirectionalRule]:
        return list(extracted_spec.rules)

    def test_extracts_authority_rules(self, extracted_rules: list[DirectionalRule]) -> None:
        authority_rules = [r for r in extracted_rules if r.rule_id.startswith("PF-AUTH-")]
        assert len(authority_rules) >= 2
        assert any(r.rule_id == "PF-AUTH-001" for r in extracted_rules)
        assert any(r.rule_id == "PF-AUTH-002" for r in extracted_rules)

    def test_extracts_boundary_rules(self, extracted_rules: list[DirectionalRule]) -> None:
        boundary_rules = [r for r in extracted_rules if r.rule_id.startswith("PF-BOUND-")]
        assert len(boundary_rules) >= 2
        assert any(r.rule_id == "PF-BOUND-001" for r in extracted_rules)
        assert any(r.rule_id == "PF-BOUND-002" for r in extracted_rules)

    def test_extracts_invariant_rules(self, extracted_rules: list[DirectionalRule]) -> None:
        invariant_rules = [r for r in extracted_rules if r.rule_id.startswith("PF-INV-")]
        assert len(invariant_rules) >= 2
        assert any(r.rule_id == "PF-INV-001" for r in extracted_rules)
        assert any(r.rule_id == "PF-INV-002" for r in extracted_rules)

    def test_extracts_provenance_rules(self, extracted_rules: list[DirectionalRule]) -> None:
        provenance_rules = [r for r in extracted_rules if r.rule_id.startswith("PF-PROV-")]
        assert len(provenance_rules) >= 1
        assert any(r.rule_id == "PF-PROV-001" for r in extracted_rules)

    def test_extracts_execution_rules(self, extracted_rules: list[DirectionalRule]) -> None:
        execution_rules = [r for r in extracted_rules if r.rule_id.startswith("PF-EXEC-")]
        assert len(execution_rules) >= 2
        assert any(r.rule_id == "PF-EXEC-001" for r in extracted_rules)
        assert any(r.rule_id == "PF-EXEC-002" for r in extracted_rules)

    def test_extracts_storage_rules(self, extracted_rules: list[DirectionalRule]) -> None:
        storage_rules = [r for r in extracted_rules if r.rule_id.startswith("PF-STOR-")]
        assert len(storage_rules) >= 1
        assert any(r.rule_id == "PF-STOR-001" for r in extracted_rules)

    def test_extracts_simulation_rules(self, extracted_rules: list[DirectionalRule]) -> None:
        simulation_rules = [r for r in extracted_rules if r.rule_id.startswith("PF-SIM-")]
        assert len(simulation_rules) >= 1
        assert any(r.rule_id == "PF-SIM-001" for r in extracted_rules)

    def test_single_writer_rule_preserves_authority(self, extracted_rules: list[DirectionalRule]) -> None:
        single_writer_rule = next((r for r in extracted_rules if r.rule_id == "PF-AUTH-002"), None)
        assert single_writer_rule is not None
        assert "job_manager" in single_writer_rule.allowed_authorities
        assert "scheduler" in single_writer_rule.prohibited_authorities
        assert "policy_engine" in single_writer_rule.prohibited_authorities
        assert "provider" in single_writer_rule.prohibited_authorities
        assert "lifecycle_state_mutation_authority == job_manager" in single_writer_rule.authority_boundaries

    def test_epistemic_boundary_rule_prohibits_execution(self, extracted_rules: list[DirectionalRule]) -> None:
        epistemic_rule = next((r for r in extracted_rules if r.rule_id == "PF-BOUND-002"), None)
        assert epistemic_rule is not None
        assert "epistemic_execution" in epistemic_rule.prohibited_authorities
        assert "epistemic_production_mutation" in epistemic_rule.prohibited_authorities
        assert "epistemic_advisory_only" in epistemic_rule.authority_boundaries

    def test_deterministic_core_rule_preserves_purity(self, extracted_rules: list[DirectionalRule]) -> None:
        deterministic_rule = next((r for r in extracted_rules if r.rule_id == "PF-INV-001"), None)
        assert deterministic_rule is not None
        assert any("core business logic is pure" in c for c in deterministic_rule.constraints)
        assert any("deterministic" in c.lower() for c in deterministic_rule.constraints)

    def test_execution_attempt_rule_separates_attempts_from_lifecycle(
        self, extracted_rules: list[DirectionalRule]
    ) -> None:
        execution_rule = next((r for r in extracted_rules if r.rule_id == "PF-EXEC-001"), None)
        assert execution_rule is not None
        assert "execution attempts carry their own state" in execution_rule.constraints
        assert "retry creates new execution attempt" in execution_rule.constraints


class TestPrintForgeProjection:
    """Test that generic projection machinery works with PrintForge directional spec."""

    @pytest.fixture
    def extractor(self) -> PrintForgeDirectionExtractor:
        return PrintForgeDirectionExtractor()

    @pytest.fixture
    def projection_result(self, extractor: PrintForgeDirectionExtractor) -> tuple[DirectionalSpec, ProjectionResult]:
        return extractor.build_projection_result()

    def test_projection_returns_architecture_candidate(
        self, projection_result: tuple[DirectionalSpec, ProjectionResult]
    ) -> None:
        spec, result = projection_result
        assert result.architecture_candidate is not None
        assert isinstance(result.architecture_candidate, ArchitectureCandidate)

    def test_projection_returns_scaffold_spec(
        self, projection_result: tuple[DirectionalSpec, ProjectionResult]
    ) -> None:
        spec, result = projection_result
        assert result.scaffold_spec is not None
        assert isinstance(result.scaffold_spec, ScaffoldSpec)

    def test_projection_produces_traceability(
        self, projection_result: tuple[DirectionalSpec, ProjectionResult]
    ) -> None:
        spec, result = projection_result
        assert len(result.traceability) > 0
        assert all(isinstance(t, Traceability) for t in result.traceability)

    def test_projection_produces_projections(
        self, projection_result: tuple[DirectionalSpec, ProjectionResult]
    ) -> None:
        spec, result = projection_result
        assert len(result.projections) > 0

    def test_architecture_candidate_has_boundaries(
        self, projection_result: tuple[DirectionalSpec, ProjectionResult]
    ) -> None:
        spec, result = projection_result
        assert len(result.architecture_candidate.boundaries) > 0

    def test_architecture_candidate_has_authorities(
        self, projection_result: tuple[DirectionalSpec, ProjectionResult]
    ) -> None:
        spec, result = projection_result
        assert len(result.architecture_candidate.authorities) > 0

    def test_scaffold_preserves_implementation_freedoms(
        self, projection_result: tuple[DirectionalSpec, ProjectionResult]
    ) -> None:
        spec, result = projection_result
        assert len(result.scaffold_spec.implementation_freedoms) > 0

    def test_projection_deterministic(self, extractor: PrintForgeDirectionExtractor) -> None:
        spec1, result1 = extractor.build_projection_result()
        spec2, result2 = extractor.build_projection_result()
        assert result1.architecture_candidate is not None
        assert result2.architecture_candidate is not None
        assert result1.architecture_candidate.boundaries == result2.architecture_candidate.boundaries
        assert result1.architecture_candidate.authorities == result2.architecture_candidate.authorities
        assert result1.scaffold_spec is not None
        assert result2.scaffold_spec is not None
        assert result1.scaffold_spec.required_boundaries == result2.scaffold_spec.required_boundaries
        assert len(result1.projections) == len(result2.projections)
        assert len(result1.traceability) == len(result2.traceability)
        assert set(t.source_id for t in result1.traceability) == set(t.source_id for t in result2.traceability)
        assert set(t.source_id for t in result1.traceability) == set(t.source_id for t in result2.traceability)
        assert set(t.source_id for t in result1.traceability) == set(t.source_id for t in result2.traceability)
        assert set(t.source_id for t in result1.traceability) == set(t.source_id for t in result2.traceability)


class TestPrintForgeValidation:
    """Test that independent validator works with PrintForge projection result."""

    @pytest.fixture
    def extractor(self) -> PrintForgeDirectionExtractor:
        return PrintForgeDirectionExtractor()

    @pytest.fixture
    def spec_and_result(self, extractor: PrintForgeDirectionExtractor) -> tuple[DirectionalSpec, ProjectionResult]:
        return extractor.build_projection_result()

    @pytest.fixture
    def validation_result(
        self, spec_and_result: tuple[DirectionalSpec, ProjectionResult], extractor: PrintForgeDirectionExtractor
    ) -> ValidationResult:
        spec, result = spec_and_result
        return extractor.validate_projection_result(spec, result)

    def test_validation_returns_result(self, validation_result: ValidationResult) -> None:
        assert isinstance(validation_result, ValidationResult)

    def test_validation_status_is_valid(self, validation_result: ValidationResult) -> None:
        assert validation_result.status in {"pass", "fail", "inconclusive", "not_applicable"}

    def test_validation_never_returns_accepted(self, validation_result: ValidationResult) -> None:
        forbidden = {"approved", "accepted", "authorized", "executed", "activated"}
        assert validation_result.status not in forbidden

    def test_validation_has_findings(self, validation_result: ValidationResult) -> None:
        assert len(validation_result.findings) > 0

    def test_validation_findings_have_rule_ids(self, validation_result: ValidationResult) -> None:
        for finding in validation_result.findings:
            assert finding.rule_id != ""

    def test_validation_findings_have_checks(self, validation_result: ValidationResult) -> None:
        for finding in validation_result.findings:
            assert finding.check != ""
            assert finding.status in {"pass", "fail", "inconclusive", "not_applicable"}


class TestPrintForgeAuthority:
    """Test that PrintForge authority boundaries are preserved in DP representation."""

    @pytest.fixture
    def extractor(self) -> PrintForgeDirectionExtractor:
        return PrintForgeDirectionExtractor()

    @pytest.fixture
    def spec(self, extractor: PrintForgeDirectionExtractor) -> DirectionalSpec:
        return extractor.build_directional_spec()

    def test_single_writer_rule_exists(self, spec: DirectionalSpec) -> None:
        single_writer_rule = next((r for r in spec.rules if r.rule_id == "PF-AUTH-002"), None)
        assert single_writer_rule is not None
        assert "job_manager" in single_writer_rule.allowed_authorities

    def test_provider_isolation_rule_exists(self, spec: DirectionalSpec) -> None:
        provider_rule = next((r for r in spec.rules if r.rule_id == "PF-BOUND-001"), None)
        assert provider_rule is not None
        assert "provider_domain_mutation" in provider_rule.prohibited_authorities
        assert "provider_policy_bypass" in provider_rule.prohibited_authorities

    def test_epistemic_advisory_rule_exists(self, spec: DirectionalSpec) -> None:
        epistemic_rule = next((r for r in spec.rules if r.rule_id == "PF-BOUND-002"), None)
        assert epistemic_rule is not None
        assert "epistemic_execution" in epistemic_rule.prohibited_authorities
        assert "epistemic_production_mutation" in epistemic_rule.prohibited_authorities
        assert "epistemic_advisory_only" in epistemic_rule.authority_boundaries

    def test_execution_attempt_separation_rule_exists(self, spec: DirectionalSpec) -> None:
        execution_rule = next((r for r in spec.rules if r.rule_id == "PF-EXEC-001"), None)
        assert execution_rule is not None
        assert "execution_attempt_authority != lifecycle_authority" in execution_rule.authority_boundaries

    def test_deterministic_core_rule_exists(self, spec: DirectionalSpec) -> None:
        deterministic_rule = next((r for r in spec.rules if r.rule_id == "PF-INV-001"), None)
        assert deterministic_rule is not None
        assert any("core business logic is pure" in c for c in deterministic_rule.constraints)

    def test_reconciliation_explicitness_rule_exists(self, spec: DirectionalSpec) -> None:
        reconciliation_rule = next((r for r in spec.rules if r.rule_id == "PF-INV-002"), None)
        assert reconciliation_rule is not None
        assert "declarations and observations are never silently overwritten" in reconciliation_rule.constraints


class TestPrintForgeGenericity:
    """Test that PrintForge pilot does not contaminate generic DP packages."""

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
        "actuator",
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
    ]

    @pytest.fixture
    def generic_project_spec_files(self) -> list[pathlib.Path]:
        src_dir = pathlib.Path(__file__).resolve().parents[2] / "src" / "cognitia" / "project_spec"
        return list(src_dir.rglob("*.py"))

    @pytest.fixture
    def validator_files(self) -> list[pathlib.Path]:
        src_dir = pathlib.Path(__file__).resolve().parents[2] / "validator"
        return list(src_dir.rglob("*.py"))

    @pytest.fixture
    def erector_files(self) -> list[pathlib.Path]:
        src_dir = pathlib.Path(__file__).resolve().parents[2] / "erector"
        return list(src_dir.rglob("*.py"))

    def test_project_spec_no_forbidden_terms(self, generic_project_spec_files: list[pathlib.Path]) -> None:
        violations = []
        for file_path in generic_project_spec_files:
            text = file_path.read_text(encoding="utf-8")
            for term in self.FORBIDDEN_TERMS:
                if term in text:
                    violations.append((file_path, term))
        assert violations == [], f"Forbidden domain terms in project_spec: {violations}"

    def test_validator_no_forbidden_terms(self, validator_files: list[pathlib.Path]) -> None:
        violations = []
        for file_path in validator_files:
            text = file_path.read_text(encoding="utf-8")
            for term in self.FORBIDDEN_TERMS:
                if term in text:
                    violations.append((file_path, term))
        assert violations == [], f"Forbidden domain terms in validator: {violations}"

    def test_erector_no_forbidden_terms(self, erector_files: list[pathlib.Path]) -> None:
        violations = []
        for file_path in erector_files:
            text = file_path.read_text(encoding="utf-8")
            for term in self.FORBIDDEN_TERMS:
                if term in text:
                    violations.append((file_path, term))
        assert violations == [], f"Forbidden domain terms in erector: {violations}"


class TestPrintForgeReferenceIntegrity:
    """Test that PrintForge reference repository remains untouched."""

    def test_printforge_working_tree_clean(self) -> None:
        import subprocess
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd="E:\\PrintForge",
            capture_output=True,
            text=True,
        )
        assert result.stdout.strip() == "", f"PrintForge working tree is not clean: {result.stdout}"

    def test_printforge_commit_unchanged(self) -> None:
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd="E:\\PrintForge",
            capture_output=True,
            text=True,
        )
        assert result.stdout.strip() == "ad02b6d0c630d7d9f96a3702f60827dd759e847e"


class TestPrintForgeTraceability:
    """Test complete traceability chain for PrintForge concepts."""

    @pytest.fixture
    def extractor(self) -> PrintForgeDirectionExtractor:
        return PrintForgeDirectionExtractor()

    @pytest.fixture
    def projection_result(self, extractor: PrintForgeDirectionExtractor) -> tuple[DirectionalSpec, ProjectionResult]:
        return extractor.build_projection_result()

    def test_rule_to_architecture_traceability(
        self, projection_result: tuple[DirectionalSpec, ProjectionResult]
    ) -> None:
        spec, result = projection_result
        rule_ids = {r.rule_id for r in spec.rules}
        traceability_targets = {t.target_id for t in result.traceability}
        for rule_id in rule_ids:
            assert rule_id in traceability_targets or any(
                rule_id in t.source_id or rule_id in t.target_id for t in result.traceability
            ), f"Rule {rule_id} not found in traceability"

    def test_architecture_to_scaffold_traceability(
        self, projection_result: tuple[DirectionalSpec, ProjectionResult]
    ) -> None:
        spec, result = projection_result
        if result.architecture_candidate is not None:
            arch_id = result.architecture_candidate.candidate_id or result.architecture_candidate.id
            arch_to_scaffold = [
                t for t in result.traceability
                if t.source_id == arch_id and t.relationship == RelationshipType.IMPLEMENTS.value
            ]
            assert len(arch_to_scaffold) >= 1

    def test_complete_chain_exists(self, projection_result: tuple[DirectionalSpec, ProjectionResult]) -> None:
        spec, result = projection_result
        rule_ids = {r.rule_id for r in spec.rules}
        for rule_id in rule_ids:
            rule_trace = [t for t in result.traceability if t.source_id == rule_id]
            assert len(rule_trace) >= 1, f"Rule {rule_id} has no traceability links"


class TestPrintForgeDeterminism:
    """Test that PrintForge extraction and projection are deterministic."""

    @pytest.fixture
    def extractor(self) -> PrintForgeDirectionExtractor:
        return PrintForgeDirectionExtractor()

    def test_extraction_deterministic(self, extractor: PrintForgeDirectionExtractor) -> None:
        spec1 = extractor.build_directional_spec()
        spec2 = extractor.build_directional_spec()
        assert len(spec1.rules) == len(spec2.rules)
        for r1, r2 in zip(spec1.rules, spec2.rules):
            assert r1.rule_id == r2.rule_id
            assert r1.version == r2.version
            assert r1.status == r2.status
            assert r1.objectives == r2.objectives
            assert r1.constraints == r2.constraints
            assert r1.allowed_authorities == r2.allowed_authorities
            assert r1.prohibited_authorities == r2.prohibited_authorities

    def test_projection_deterministic(self, extractor: PrintForgeDirectionExtractor) -> None:
        spec1, result1 = extractor.build_projection_result()
        spec2, result2 = extractor.build_projection_result()
        # IDs differ per build; compare semantic content instead
        assert result1.architecture_candidate is not None
        assert result2.architecture_candidate is not None
        assert result1.architecture_candidate.boundaries == result2.architecture_candidate.boundaries
        assert result1.architecture_candidate.authorities == result2.architecture_candidate.authorities
        assert result1.scaffold_spec is not None
        assert result2.scaffold_spec is not None
        assert result1.scaffold_spec.required_boundaries == result2.scaffold_spec.required_boundaries
        assert len(result1.projections) == len(result2.projections)
        assert len(result1.traceability) == len(result2.traceability)
        assert set(t.source_id for t in result1.traceability) == set(t.source_id for t in result2.traceability)


class TestPrintForgeInteractionContracts:
    """Test that PrintForge interaction semantics are expressed via generic InteractionContract."""

    @pytest.fixture
    def extractor(self) -> PrintForgeDirectionExtractor:
        return PrintForgeDirectionExtractor()

    @pytest.fixture
    def spec(self, extractor: PrintForgeDirectionExtractor) -> DirectionalSpec:
        return extractor.build_directional_spec()

    def test_provider_boundary_has_interaction_contract(self, spec: DirectionalSpec) -> None:
        provider_rule = next((r for r in spec.rules if r.rule_id == "PF-BOUND-001"), None)
        assert provider_rule is not None
        assert len(provider_rule.interaction_contracts) >= 1
        contract = provider_rule.interaction_contracts[0]
        assert contract.boundary == "provider_adapter_boundary"
        assert contract.canonical_representation == "canonical_internal_contract"
        assert contract.translation_required is True

    def test_event_delivery_has_interaction_contract(self, spec: DirectionalSpec) -> None:
        execution_rule = next((r for r in spec.rules if r.rule_id == "PF-EXEC-002"), None)
        assert execution_rule is not None
        assert len(execution_rule.interaction_contracts) >= 1
        contract = execution_rule.interaction_contracts[0]
        assert contract.delivery_semantics == DeliverySemantics.AT_LEAST_ONCE.value
        assert contract.idempotency_required is True

    def test_projection_carries_interaction_contracts(self, extractor: PrintForgeDirectionExtractor) -> None:
        spec, result = extractor.build_projection_result()
        assert result.architecture_candidate is not None
        assert "PF-IC-001" in result.architecture_candidate.interaction_contracts
        assert "PF-IC-002" in result.architecture_candidate.interaction_contracts
        assert result.scaffold_spec is not None
        assert "PF-IC-001" in result.scaffold_spec.interaction_contracts
        assert "PF-IC-002" in result.scaffold_spec.interaction_contracts

    def test_interaction_contracts_do_not_contain_domain_terms(self, spec: DirectionalSpec) -> None:
        for rule in spec.rules:
            for contract in rule.interaction_contracts:
                assert "ipp" not in contract.boundary.lower()
                assert "kafka" not in contract.boundary.lower()
                assert "cups" not in contract.boundary.lower()
                assert "printer" not in contract.canonical_representation.lower()
