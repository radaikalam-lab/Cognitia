"""Independent Deterministic Validator Tests."""

from __future__ import annotations

import pathlib

import pytest

from cognitia.project_spec.types import (
    ArchitectureCandidate,
    Conflict,
    DeliverySemantics,
    DirectionalRule,
    DirectionalRuleStatus,
    DirectionalSpec,
    InteractionContract,
    ScaffoldSpec,
    Traceability,
    RelationshipType,
)
from validator.project_spec_validator import (
    DeterministicProjectSpecValidator,
    ProjectSpecValidator,
)
from validator.types import (
    ValidationFinding,
    ValidationResult,
    ValidationStatus,
)


def _make_rule(
    rule_id: str = "PROJECT-AUTH-001",
    version: str = "1.0.0",
    status: DirectionalRuleStatus = DirectionalRuleStatus.DRAFT,
    allowed_authorities: list[str] | None = None,
    prohibited_authorities: list[str] | None = None,
    authority_boundaries: list[str] | None = None,
    objectives: list[str] | None = None,
    constraints: list[str] | None = None,
    projection_requirements: list[str] | None = None,
    technology_freedoms: list[str] | None = None,
) -> DirectionalRule:
    return DirectionalRule(
        rule_id=rule_id,
        version=version,
        status=status,
        current_state="no project scaffold",
        desired_state="governed project scaffold",
        objectives=objectives or ["establish project boundaries"],
        constraints=constraints or ["must not prescribe implementation"],
        allowed_authorities=allowed_authorities or ["governance"],
        prohibited_authorities=prohibited_authorities or ["implementation_authority"],
        authority_boundaries=authority_boundaries or ["reasoning != approval"],
        observables=["boundary_contracts"],
        acceptance_conditions=["all boundaries explicit"],
        evidence_requirements=["traceability_chain"],
        provenance_requirements=["immutable_lineage"],
        implementation_scope="structural scaffold only",
        governance_notes="requires governance acceptance",
        conflict_policy="escalate_to_governance",
        scaffold_constraints=["required_boundaries"],
        technology_freedoms=technology_freedoms or ["any_persistence"],
        projection_requirements=projection_requirements or ["traceability_preserved"],
    )


def _make_spec(rules: list[DirectionalRule] | None = None) -> DirectionalSpec:
    return DirectionalSpec(rules=rules or [_make_rule()])


def _make_candidate(
    candidate_id: str = "arch-1",
    authorities: list[str] | None = None,
    boundaries: list[str] | None = None,
    required_capabilities: list[str] | None = None,
    traceability: list[str] | None = None,
    interaction_contracts: tuple[str, ...] = (),
) -> ArchitectureCandidate:
    return ArchitectureCandidate(
        candidate_id=candidate_id,
        boundaries=boundaries if boundaries is not None else ["reasoning != approval", "prohibited:implementation_authority"],
        authorities=authorities if authorities is not None else ["governance"],
        responsibilities=["establish project boundaries", "must not prescribe implementation"],
        dependencies=[],
        invariants=["must not prescribe implementation"],
        required_capabilities=required_capabilities if required_capabilities is not None else ["traceability_preserved"],
        prohibited_dependencies=["prohibited_authority:implementation_authority"],
        observables=["boundary_contracts"],
        validation_requirements=["all boundaries explicit", "traceability_chain"],
        traceability=traceability if traceability is not None else ["PROJECT-AUTH-001"],
        interaction_contracts=interaction_contracts,
    )


def _make_scaffold(
    spec_id: str = "scf-1",
    traceability: list[str] | None = None,
    interaction_contracts: tuple[str, ...] = (),
) -> ScaffoldSpec:
    return ScaffoldSpec(
        spec_id=spec_id,
        required_boundaries=["reasoning != approval"],
        required_surfaces=["governance"],
        required_interfaces=["traceability_preserved"],
        required_test_surfaces=["all boundaries explicit"],
        prohibited_structural_patterns=["prohibited_authority:implementation_authority"],
        implementation_freedoms=["any_persistence"],
        traceability=traceability or ["arch-1", "PROJECT-AUTH-001"],
        interaction_contracts=interaction_contracts,
    )


class TestValidationStatus:
    def test_all_statuses_defined(self) -> None:
        expected = {"pass", "fail", "inconclusive", "not_applicable"}
        actual = {s.value for s in ValidationStatus}
        assert actual == expected

    def test_no_governance_statuses(self) -> None:
        forbidden = {"approved", "accepted", "authorized", "executed", "activated"}
        actual = {s.value for s in ValidationStatus}
        assert forbidden.isdisjoint(actual)


class TestDeterministicProjectSpecValidator:
    def test_validator_attributes(self) -> None:
        validator = DeterministicProjectSpecValidator(
            validator_id="custom",
            validator_version="2.0.0",
        )
        assert validator.validator_id == "custom"
        assert validator.validator_version == "2.0.0"

    def test_validate_returns_result(self) -> None:
        validator = DeterministicProjectSpecValidator()
        result = validator.validate(
            specification=_make_spec(),
            candidate=_make_candidate(),
        )
        assert isinstance(result, ValidationResult)

    def test_validate_pass(self) -> None:
        validator = DeterministicProjectSpecValidator()
        result = validator.validate(
            specification=_make_spec(),
            candidate=_make_candidate(),
        )
        assert result.status == ValidationStatus.PASS.value

    def test_validate_inconclusive_with_open_conflict(self) -> None:
        validator = DeterministicProjectSpecValidator()
        conflict = Conflict(
            conflict_id="CONF-1",
            rules_in_conflict=["RULE-1", "RULE-2"],
            description="overlap",
            severity="high",
            resolution_status="open",
            governance_required=True,
        )
        result = validator.validate(
            specification=_make_spec(),
            candidate=_make_candidate(),
            conflicts=[conflict],
        )
        assert result.status == ValidationStatus.INCONCLUSIVE.value

    def test_validate_pass_with_resolved_conflict(self) -> None:
        validator = DeterministicProjectSpecValidator()
        conflict = Conflict(
            conflict_id="CONF-1",
            rules_in_conflict=["RULE-1", "RULE-2"],
            description="overlap",
            severity="high",
            resolution_status="resolved",
            governance_required=True,
        )
        result = validator.validate(
            specification=_make_spec(),
            candidate=_make_candidate(),
            conflicts=[conflict],
        )
        assert result.status == ValidationStatus.PASS.value

    def test_validate_fail_missing_authority(self) -> None:
        validator = DeterministicProjectSpecValidator()
        candidate = _make_candidate(authorities=["wrong_authority"])
        result = validator.validate(
            specification=_make_spec(),
            candidate=candidate,
        )
        assert result.status == ValidationStatus.FAIL.value
        assert any(
            f.check == "allowed_authorities_represented" and f.status == ValidationStatus.FAIL.value
            for f in result.findings
        )

    def test_validate_fail_prohibited_dependency_present(self) -> None:
        validator = DeterministicProjectSpecValidator()
        candidate = _make_candidate(authorities=["governance", "implementation_authority"])
        result = validator.validate(
            specification=_make_spec(),
            candidate=candidate,
        )
        assert result.status == ValidationStatus.FAIL.value
        assert any(
            f.check == "prohibited_authority_absent" and f.status == ValidationStatus.FAIL.value
            for f in result.findings
        )

    def test_validate_fail_missing_boundary(self) -> None:
        validator = DeterministicProjectSpecValidator()
        candidate = _make_candidate(boundaries=["other_boundary"])
        result = validator.validate(
            specification=_make_spec(),
            candidate=candidate,
        )
        assert result.status == ValidationStatus.FAIL.value
        assert any(
            f.check == "authority_boundaries_represented" and f.status == ValidationStatus.FAIL.value
            for f in result.findings
        )

    def test_validate_fail_missing_required_capability(self) -> None:
        validator = DeterministicProjectSpecValidator()
        candidate = _make_candidate(required_capabilities=[])
        result = validator.validate(
            specification=_make_spec(),
            candidate=candidate,
        )
        assert result.status == ValidationStatus.FAIL.value
        assert any(
            f.check == "required_capabilities_represented" and f.status == ValidationStatus.FAIL.value
            for f in result.findings
        )

    def test_validate_fail_missing_objectives_and_constraints(self) -> None:
        validator = DeterministicProjectSpecValidator()
        rule = DirectionalRule(
            rule_id="RULE-EMPTY",
            objectives=[],
            constraints=[],
        )
        spec = DirectionalSpec(rules=[rule])
        candidate = _make_candidate()
        result = validator.validate(
            specification=spec,
            candidate=candidate,
        )
        assert result.status == ValidationStatus.FAIL.value
        assert any(
            f.check == "required_directional_elements" and f.status == ValidationStatus.FAIL.value
            for f in result.findings
        )

    def test_validate_implementation_freedom_finding(self) -> None:
        validator = DeterministicProjectSpecValidator()
        result = validator.validate(
            specification=_make_spec(),
            candidate=_make_candidate(),
        )
        assert any(
            f.check == "implementation_freedom_preserved"
            and f.status == ValidationStatus.PASS.value
            for f in result.findings
        )

    def test_validate_scaffold_traceability_pass(self) -> None:
        validator = DeterministicProjectSpecValidator()
        candidate = _make_candidate(candidate_id="arch-1")
        scaffold = _make_scaffold(traceability=["arch-1", "PROJECT-AUTH-001"])
        result = validator.validate(
            specification=_make_spec(),
            candidate=candidate,
            scaffold=scaffold,
        )
        assert result.status == ValidationStatus.PASS.value

    def test_validate_scaffold_traceability_fail(self) -> None:
        validator = DeterministicProjectSpecValidator()
        candidate = _make_candidate(candidate_id="arch-1")
        scaffold = _make_scaffold(traceability=["other-arch"])
        result = validator.validate(
            specification=_make_spec(),
            candidate=candidate,
            scaffold=scaffold,
        )
        assert result.status == ValidationStatus.FAIL.value
        assert any(
            f.check == "scaffold_traceability_to_architecture"
            and f.status == ValidationStatus.FAIL.value
            for f in result.findings
        )

    def test_validate_without_scaffold(self) -> None:
        validator = DeterministicProjectSpecValidator()
        result = validator.validate(
            specification=_make_spec(),
            candidate=_make_candidate(),
            scaffold=None,
        )
        assert result.status == ValidationStatus.PASS.value
        assert all(
            f.check != "scaffold_traceability_to_architecture" for f in result.findings
        )

    def test_deterministic_output(self) -> None:
        validator = DeterministicProjectSpecValidator()
        spec = _make_spec()
        candidate = _make_candidate()
        r1 = validator.validate(specification=spec, candidate=candidate)
        r2 = validator.validate(specification=spec, candidate=candidate)
        assert r1.status == r2.status
        assert len(r1.findings) == len(r2.findings)
        for f1, f2 in zip(r1.findings, r2.findings):
            assert f1.rule_id == f2.rule_id
            assert f1.check == f2.check
            assert f1.status == f2.status
            assert f1.expected == f2.expected
            assert f1.observed == f2.observed
        assert r1.checked_constraints == r2.checked_constraints
        assert r1.traceability == r2.traceability

    def test_validation_result_provenance(self) -> None:
        validator = DeterministicProjectSpecValidator()
        result = validator.validate(
            specification=_make_spec(),
            candidate=_make_candidate(),
        )
        assert result.provenance is not None
        assert result.provenance.source_type.value == "deterministic_rule"

    def test_finding_has_rule_id_and_subject(self) -> None:
        validator = DeterministicProjectSpecValidator()
        result = validator.validate(
            specification=_make_spec(),
            candidate=_make_candidate(),
        )
        for finding in result.findings:
            assert finding.rule_id != ""
            assert finding.subject_id != ""
            assert finding.check != ""
            assert finding.status in {s.value for s in ValidationStatus}

    def test_checked_constraints_lists_all_rules(self) -> None:
        validator = DeterministicProjectSpecValidator()
        rule1 = _make_rule("RULE-1")
        rule2 = _make_rule("RULE-2")
        spec = DirectionalSpec(rules=[rule1, rule2])
        result = validator.validate(
            specification=spec,
            candidate=_make_candidate(),
        )
        assert "RULE-1" in result.checked_constraints
        assert "RULE-2" in result.checked_constraints

    def test_validator_never_returns_approved(self) -> None:
        forbidden = {"approved", "accepted", "authorized", "executed", "activated"}
        validator = DeterministicProjectSpecValidator()
        for _ in range(5):
            result = validator.validate(
                specification=_make_spec(),
                candidate=_make_candidate(),
            )
            assert result.status not in forbidden


class TestAuthorityBoundaryTests:
    """Explicit authority boundary tests from DP-P0.2 section 12."""

    def test_validator_cannot_mutate_specification(self) -> None:
        validator = DeterministicProjectSpecValidator()
        spec = _make_spec()
        original_rule_count = len(spec.rules)
        candidate = _make_candidate()
        validator.validate(specification=spec, candidate=candidate)
        assert len(spec.rules) == original_rule_count

    def test_validator_cannot_mutate_candidate(self) -> None:
        validator = DeterministicProjectSpecValidator()
        candidate = _make_candidate()
        original_boundaries = candidate.boundaries
        spec = _make_spec()
        validator.validate(specification=spec, candidate=candidate)
        assert candidate.boundaries == original_boundaries

    def test_validation_cannot_change_validated_to_accepted(self) -> None:
        forbidden = {"accepted", "approved", "authorized"}
        validator = DeterministicProjectSpecValidator()
        result = validator.validate(
            specification=_make_spec(),
            candidate=_make_candidate(),
        )
        assert result.status not in forbidden

    def test_validator_has_no_execute_method(self) -> None:
        validator = DeterministicProjectSpecValidator()
        assert not hasattr(validator, "execute_action")
        assert not hasattr(validator, "actuate")
        assert not hasattr(validator, "approve")
        assert not hasattr(validator, "authorize")
        assert not hasattr(validator, "deploy")
        assert not hasattr(validator, "erect")

    def test_validator_does_not_import_adapters(self) -> None:
        import validator.project_spec_validator as val_mod
        import pathlib
        source = pathlib.Path(val_mod.__file__).read_text(encoding="utf-8")
        forbidden = [
            "adapters.fjh",
            "adapters.frappe",
            "PrintForge",
            "AcoustiForge",
            "FJH",
            "Frappe",
            "ERPNext",
            "printer",
            "speaker",
            "reactor",
            "farm",
            "actuator",
        ]
        for term in forbidden:
            assert term not in source, f"Validator imports domain term: {term}"

    def test_validator_does_not_depend_on_llm(self) -> None:
        import validator.project_spec_validator as val_mod
        import pathlib
        source = pathlib.Path(val_mod.__file__).read_text(encoding="utf-8")
        forbidden = ["openai", "anthropic", "llm", "model_inference", "torch", "tensorflow"]
        for term in forbidden:
            assert term not in source.lower(), f"Validator has LLM/ML dependency: {term}"

    def test_validation_output_is_not_governance(self) -> None:
        validator = DeterministicProjectSpecValidator()
        result = validator.validate(
            specification=_make_spec(),
            candidate=_make_candidate(),
        )
        assert not hasattr(result, "approve")
        assert not hasattr(result, "authorize")
        assert not hasattr(result, "execute")
        assert not hasattr(result, "deploy")


class TestDirectionVsImplementation:
    """Direction vs Implementation test from DP-P0.2 section 13."""

    def test_two_structurally_different_candidates_both_pass(self) -> None:
        validator = DeterministicProjectSpecValidator()
        rule = _make_rule(
            rule_id="RULE-FREE",
            technology_freedoms=["any_persistence", "any_test_framework", "any_interface"],
        )
        spec = _make_spec([rule])

        candidate_a = ArchitectureCandidate(
            candidate_id="candidate-a",
            boundaries=rule.authority_boundaries,
            authorities=rule.allowed_authorities,
            responsibilities=rule.objectives + rule.constraints,
            required_capabilities=rule.projection_requirements,
            prohibited_dependencies=[
                f"prohibited_authority:{a}" for a in rule.prohibited_authorities
            ],
            traceability=[rule.rule_id],
        )

        candidate_b = ArchitectureCandidate(
            candidate_id="candidate-b",
            boundaries=list(rule.authority_boundaries) + ["extra_boundary"],
            authorities=list(rule.allowed_authorities) + ["extra_authority"],
            responsibilities=list(rule.objectives + rule.constraints) + ["extra_resp"],
            required_capabilities=list(rule.projection_requirements) + ["extra_cap"],
            prohibited_dependencies=[
                f"prohibited_authority:{a}" for a in rule.prohibited_authorities
            ] + ["extra_prohibited"],
            traceability=[rule.rule_id, "extra_trace"],
        )

        result_a = validator.validate(
            specification=spec,
            candidate=candidate_a,
        )
        result_b = validator.validate(
            specification=spec,
            candidate=candidate_b,
        )

        assert result_a.status == ValidationStatus.PASS.value
        assert result_b.status == ValidationStatus.PASS.value

    def test_validator_does_not_impose_implementation_technology(self) -> None:
        validator = DeterministicProjectSpecValidator()
        rule = _make_rule(
            rule_id="RULE-TECH-FREE",
            technology_freedoms=["any_persistence", "any_framework"],
        )
        spec = _make_spec([rule])
        candidate = _make_candidate()
        result = validator.validate(
            specification=spec,
            candidate=candidate,
        )
        assert result.status == ValidationStatus.PASS.value
        for finding in result.findings:
            assert "python" not in finding.expected.lower()
            assert "fastapi" not in finding.expected.lower()
            assert "postgresql" not in finding.expected.lower()


class TestNegativeValidationCases:
    """Deterministic negative tests from DP-P0.2 section 14."""

    def test_missing_required_boundary(self) -> None:
        validator = DeterministicProjectSpecValidator()
        candidate = _make_candidate(boundaries=["wrong_boundary"])
        result = validator.validate(
            specification=_make_spec(),
            candidate=candidate,
        )
        assert result.status == ValidationStatus.FAIL.value
        assert any(
            "authority_boundaries_represented" in f.check
            and f.status == ValidationStatus.FAIL.value
            for f in result.findings
        )

    def test_missing_required_authority(self) -> None:
        validator = DeterministicProjectSpecValidator()
        candidate = _make_candidate(authorities=[])
        result = validator.validate(
            specification=_make_spec(),
            candidate=candidate,
        )
        assert result.status == ValidationStatus.FAIL.value
        assert any(
            "allowed_authorities_represented" in f.check
            and f.status == ValidationStatus.FAIL.value
            for f in result.findings
        )

    def test_violated_constraint(self) -> None:
        validator = DeterministicProjectSpecValidator()
        candidate = _make_candidate(authorities=["governance", "implementation_authority"])
        result = validator.validate(
            specification=_make_spec(),
            candidate=candidate,
        )
        assert result.status == ValidationStatus.FAIL.value
        assert any(
            "prohibited_authority_absent" in f.check
            and f.status == ValidationStatus.FAIL.value
            for f in result.findings
        )

    def test_prohibited_dependency_present(self) -> None:
        validator = DeterministicProjectSpecValidator()
        candidate = _make_candidate(
            authorities=["governance", "implementation_authority"]
        )
        result = validator.validate(
            specification=_make_spec(),
            candidate=candidate,
        )
        assert result.status == ValidationStatus.FAIL.value
        assert any(
            "prohibited_authority_absent" in f.check
            and f.status == ValidationStatus.FAIL.value
            for f in result.findings
        )

    def test_missing_required_capability(self) -> None:
        validator = DeterministicProjectSpecValidator()
        candidate = _make_candidate(required_capabilities=[])
        result = validator.validate(
            specification=_make_spec(),
            candidate=candidate,
        )
        assert result.status == ValidationStatus.FAIL.value
        assert any(
            "required_capabilities_represented" in f.check
            and f.status == ValidationStatus.FAIL.value
            for f in result.findings
        )

    def test_missing_traceability(self) -> None:
        validator = DeterministicProjectSpecValidator()
        candidate = _make_candidate(candidate_id="arch-1", traceability=[])
        scaffold = _make_scaffold(traceability=["other"])
        result = validator.validate(
            specification=_make_spec(),
            candidate=candidate,
            scaffold=scaffold,
        )
        assert result.status == ValidationStatus.FAIL.value
        assert any(
            "scaffold_traceability_to_architecture" in f.check
            and f.status == ValidationStatus.FAIL.value
            for f in result.findings
        )

    def test_unresolved_conflict(self) -> None:
        validator = DeterministicProjectSpecValidator()
        conflict = Conflict(
            conflict_id="CONF-1",
            rules_in_conflict=["RULE-1"],
            description="unresolved",
            resolution_status="open",
            governance_required=True,
        )
        result = validator.validate(
            specification=_make_spec(),
            candidate=_make_candidate(),
            conflicts=[conflict],
        )
        assert result.status == ValidationStatus.INCONCLUSIVE.value

    def test_malformed_specification_reference(self) -> None:
        validator = DeterministicProjectSpecValidator()
        rule = DirectionalRule(rule_id="")
        spec = DirectionalSpec(rules=[rule])
        candidate = _make_candidate()
        result = validator.validate(
            specification=spec,
            candidate=candidate,
        )
        assert any(
            f.check == "rule_identity"
            and f.subject_id == rule.id
            for f in result.findings
        )


class TestValidatorDomainNeutrality:
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
    def validator_source_files(self) -> list[pathlib.Path]:
        src_dir = pathlib.Path(__file__).resolve().parents[2] / "validator"
        return list(src_dir.rglob("*.py"))

    def test_no_forbidden_domain_terms(self, validator_source_files: list[pathlib.Path]) -> None:
        violations = []
        for file_path in validator_source_files:
            text = file_path.read_text(encoding="utf-8")
            for term in self.FORBIDDEN_TERMS:
                if term in text:
                    violations.append((file_path, term))
        assert violations == [], f"Forbidden domain terms found: {violations}"


class TestValidatorDeterminism:
    def test_deterministic_validation(self) -> None:
        validator = DeterministicProjectSpecValidator()
        spec = _make_spec()
        candidate = _make_candidate()
        r1 = validator.validate(specification=spec, candidate=candidate)
        r2 = validator.validate(specification=spec, candidate=candidate)
        assert r1.status == r2.status
        assert len(r1.findings) == len(r2.findings)
        for f1, f2 in zip(r1.findings, r2.findings):
            assert f1.rule_id == f2.rule_id
            assert f1.check == f2.check
            assert f1.status == f2.status
            assert f1.expected == f2.expected
            assert f1.observed == f2.observed
        assert r1.checked_constraints == r2.checked_constraints
        assert r1.traceability == r2.traceability

    def test_serialization_deterministic(self) -> None:
        validator = DeterministicProjectSpecValidator()
        result = validator.validate(
            specification=_make_spec(),
            candidate=_make_candidate(),
        )
        first = result.serialize()
        second = result.serialize()
        assert first == second


class TestValidatorInteractionContracts:
    def test_validate_interaction_contract_present(self) -> None:
        validator = DeterministicProjectSpecValidator()
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
        candidate = _make_candidate(interaction_contracts=("IC-001",))
        result = validator.validate(
            specification=spec,
            candidate=candidate,
        )
        assert any(
            f.check == "interaction_contract_presence"
            and f.status == ValidationStatus.PASS.value
            for f in result.findings
        )

    def test_validate_interaction_contract_missing(self) -> None:
        validator = DeterministicProjectSpecValidator()
        contract = InteractionContract(
            contract_id="IC-001",
            boundary="provider_boundary",
        )
        rule = DirectionalRule(
            rule_id="RULE-1",
            interaction_contracts=[contract],
        )
        spec = DirectionalSpec(rules=[rule])
        candidate = _make_candidate()
        result = validator.validate(
            specification=spec,
            candidate=candidate,
        )
        assert any(
            f.check == "interaction_contract_presence"
            and f.status == ValidationStatus.FAIL.value
            for f in result.findings
        )

    def test_validate_translation_boundary_present(self) -> None:
        validator = DeterministicProjectSpecValidator()
        contract = InteractionContract(
            contract_id="IC-001",
            boundary="provider_boundary",
            canonical_representation="canonical_contract",
            translation_required=True,
        )
        rule = DirectionalRule(
            rule_id="RULE-1",
            interaction_contracts=[contract],
        )
        spec = DirectionalSpec(rules=[rule])
        candidate = _make_candidate(
            boundaries=["reasoning != approval", "prohibited:implementation_authority", "provider_boundary", "canonical_contract"],
            interaction_contracts=("IC-001",),
        )
        result = validator.validate(
            specification=spec,
            candidate=candidate,
        )
        assert any(
            f.check == "translation_boundary_represented"
            and f.status == ValidationStatus.PASS.value
            for f in result.findings
        )

    def test_validate_translation_boundary_missing(self) -> None:
        validator = DeterministicProjectSpecValidator()
        contract = InteractionContract(
            contract_id="IC-001",
            boundary="provider_boundary",
            canonical_representation="canonical_contract",
            translation_required=True,
        )
        rule = DirectionalRule(
            rule_id="RULE-1",
            interaction_contracts=[contract],
        )
        spec = DirectionalSpec(rules=[rule])
        candidate = _make_candidate(interaction_contracts=("IC-001",))
        result = validator.validate(
            specification=spec,
            candidate=candidate,
        )
        assert any(
            f.check == "translation_boundary_represented"
            and f.status == ValidationStatus.FAIL.value
            for f in result.findings
        )

    def test_validate_at_least_once_without_idempotency_fails(self) -> None:
        validator = DeterministicProjectSpecValidator()
        contract = InteractionContract(
            contract_id="IC-001",
            boundary="event_boundary",
            delivery_semantics=DeliverySemantics.AT_LEAST_ONCE.value,
            idempotency_required=False,
        )
        rule = DirectionalRule(
            rule_id="RULE-1",
            interaction_contracts=[contract],
        )
        spec = DirectionalSpec(rules=[rule])
        candidate = _make_candidate(interaction_contracts=("IC-001",))
        result = validator.validate(
            specification=spec,
            candidate=candidate,
        )
        assert any(
            f.check == "delivery_idempotency_consistency"
            and f.status == ValidationStatus.FAIL.value
            for f in result.findings
        )

    def test_validate_at_least_once_with_idempotency_passes(self) -> None:
        validator = DeterministicProjectSpecValidator()
        contract = InteractionContract(
            contract_id="IC-001",
            boundary="event_boundary",
            delivery_semantics=DeliverySemantics.AT_LEAST_ONCE.value,
            idempotency_required=True,
        )
        rule = DirectionalRule(
            rule_id="RULE-1",
            interaction_contracts=[contract],
        )
        spec = DirectionalSpec(rules=[rule])
        candidate = _make_candidate(interaction_contracts=("IC-001",))
        result = validator.validate(
            specification=spec,
            candidate=candidate,
        )
        assert not any(
            f.check == "delivery_idempotency_consistency"
            and f.status == ValidationStatus.FAIL.value
            for f in result.findings
        )

    def test_validate_interaction_contract_in_scaffold(self) -> None:
        validator = DeterministicProjectSpecValidator()
        contract = InteractionContract(
            contract_id="IC-001",
            boundary="event_boundary",
            delivery_semantics=DeliverySemantics.AT_LEAST_ONCE.value,
            idempotency_required=True,
        )
        rule = DirectionalRule(
            rule_id="RULE-1",
            interaction_contracts=[contract],
        )
        spec = DirectionalSpec(rules=[rule])
        candidate = _make_candidate(interaction_contracts=("IC-001",))
        scaffold = _make_scaffold(interaction_contracts=("IC-001",))
        result = validator.validate(
            specification=spec,
            candidate=candidate,
            scaffold=scaffold,
        )
        assert any(
            f.check == "interaction_contract_in_scaffold"
            and f.status == ValidationStatus.PASS.value
            for f in result.findings
        )

    def test_validate_interaction_contract_missing_from_scaffold(self) -> None:
        validator = DeterministicProjectSpecValidator()
        contract = InteractionContract(
            contract_id="IC-001",
            boundary="event_boundary",
            delivery_semantics=DeliverySemantics.AT_LEAST_ONCE.value,
            idempotency_required=True,
        )
        rule = DirectionalRule(
            rule_id="RULE-1",
            interaction_contracts=[contract],
        )
        spec = DirectionalSpec(rules=[rule])
        candidate = _make_candidate(interaction_contracts=("IC-001",))
        scaffold = _make_scaffold()
        result = validator.validate(
            specification=spec,
            candidate=candidate,
            scaffold=scaffold,
        )
        assert any(
            f.check == "interaction_contract_in_scaffold"
            and f.status == ValidationStatus.FAIL.value
            for f in result.findings
        )
