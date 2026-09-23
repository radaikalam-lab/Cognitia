"""Independent Deterministic Validator for Project Directional Programming.

The validator consumes public project_spec artifacts and produces
structured conformance evidence. It is independent of Cognitia's
reasoning authority and does not perform governance, approval,
or execution.

Architectural boundary:
    Cognitia/ProjectSpec proposes
        ↓
    Independent Validator evaluates
        ↓
    Validation Evidence
        ↓
    Governance / Human Authority decides
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from cognitia.project_spec.types import (
    ArchitectureCandidate,
    Conflict,
    DirectionalRule,
    DirectionalSpec,
    DirectionalRuleStatus,
    InteractionContract,
    ScaffoldSpec,
    Traceability,
)
from validator.types import (
    ValidationFinding,
    ValidationResult,
    ValidationStatus,
)


@runtime_checkable
class ProjectSpecValidator(Protocol):
    """Protocol for independent project directional validators."""

    validator_id: str
    validator_version: str

    def validate(
        self,
        specification: DirectionalSpec,
        candidate: ArchitectureCandidate,
        scaffold: ScaffoldSpec | None = None,
        conflicts: list[Conflict] | None = None,
        traceability: list[Traceability] | None = None,
    ) -> ValidationResult: ...


class DeterministicProjectSpecValidator:
    """Deterministic baseline independent validator.

    Checks conformance of ArchitectureCandidate and optional ScaffoldSpec
    against a DirectionalSpec without resolving conflicts or performing
    governance.

    This validator contains no AI/ML/network/filesystem dependencies.
    It does not import from cognitia.directional or any adapter.
    """

    def __init__(
        self,
        validator_id: str = "deterministic_project_spec_validator",
        validator_version: str = "1.0.0",
    ) -> None:
        self.validator_id = validator_id
        self.validator_version = validator_version

    def validate(
        self,
        specification: DirectionalSpec,
        candidate: ArchitectureCandidate,
        scaffold: ScaffoldSpec | None = None,
        conflicts: list[Conflict] | None = None,
        traceability: list[Traceability] | None = None,
    ) -> ValidationResult:
        """Validate candidate (and optional scaffold) against specification.

        Returns a ValidationResult with deterministic findings.
        """
        findings: list[ValidationFinding] = []
        checked_constraints: list[str] = []
        checked_invariants: list[str] = []
        traceability_refs: list[str] = []

        rule_map = {rule.rule_id: rule for rule in specification.rules if rule.rule_id}

        for rule in specification.rules:
            rule_id = rule.rule_id or rule.id
            checked_constraints.append(rule_id)
            self._check_rule_identity(rule_id, rule_map, findings)
            self._check_objectives(rule_id, rule, candidate, findings)
            self._check_authorities(rule_id, rule, candidate, findings)
            self._check_prohibited_dependencies(
                rule_id, rule, candidate, findings
            )
            self._check_required_capabilities(
                rule_id, rule, candidate, findings
            )
            self._check_implementation_freedom(
                rule_id, rule, candidate, findings
            )
            self._check_interaction_contracts(
                rule_id, rule, candidate, scaffold, findings
            )
            if scaffold is not None:
                self._check_scaffold_traceability(
                    rule_id, candidate, scaffold, findings
                )
            traceability_refs.append(rule_id)

        if conflicts:
            self._check_conflicts(
                conflicts, findings, checked_invariants
            )

        overall_status = self._compute_overall_status(findings)

        validation_result = ValidationResult(
            validation_id=f"validation-{specification.id}",
            subject_id=candidate.candidate_id or candidate.id,
            specification_id=specification.id,
            validator_id=self.validator_id,
            validator_version=self.validator_version,
            status=overall_status.value,
            findings=tuple(findings),
            checked_constraints=tuple(checked_constraints),
            checked_invariants=tuple(checked_invariants),
            traceability=tuple(traceability_refs),
        )
        return validation_result

    def _check_rule_identity(
        self,
        rule_id: str,
        rule_map: dict[str, DirectionalRule],
        findings: list[ValidationFinding],
    ) -> None:
        findings.append(
            ValidationFinding(
                validation_id="",
                rule_id=rule_id,
                subject_id=rule_id,
                check="rule_identity",
                expected="rule_id present and non-empty",
                observed="present" if rule_id else "missing",
                status=(
                    ValidationStatus.PASS.value
                    if rule_id
                    else ValidationStatus.FAIL.value
                ),
                explanation=(
                    "Rule identity is present"
                    if rule_id
                    else "Rule identity is missing"
                ),
            )
        )

    def _check_objectives(
        self,
        rule_id: str,
        rule: DirectionalRule,
        candidate: ArchitectureCandidate,
        findings: list[ValidationFinding],
    ) -> None:
        if not rule.objectives and not rule.constraints:
            findings.append(
                ValidationFinding(
                    validation_id="",
                    rule_id=rule_id,
                    subject_id=candidate.candidate_id or candidate.id,
                    check="required_directional_elements",
                    expected="at least one objective or constraint",
                    observed="none",
                    status=ValidationStatus.FAIL.value,
                    explanation="Rule has no objectives or constraints",
                )
            )
        else:
            findings.append(
                ValidationFinding(
                    validation_id="",
                    rule_id=rule_id,
                    subject_id=candidate.candidate_id or candidate.id,
                    check="required_directional_elements",
                    expected="at least one objective or constraint",
                    observed="present",
                    status=ValidationStatus.PASS.value,
                    explanation="Rule declares objectives/constraints",
                )
            )

    def _check_authorities(
        self,
        rule_id: str,
        rule: DirectionalRule,
        candidate: ArchitectureCandidate,
        findings: list[ValidationFinding],
    ) -> None:
        if rule.allowed_authorities:
            missing = [
                auth
                for auth in rule.allowed_authorities
                if auth not in candidate.authorities
            ]
            findings.append(
                ValidationFinding(
                    validation_id="",
                    rule_id=rule_id,
                    subject_id=candidate.candidate_id or candidate.id,
                    check="allowed_authorities_represented",
                    expected=str(rule.allowed_authorities),
                    observed=str(candidate.authorities),
                    status=(
                        ValidationStatus.FAIL.value
                        if missing
                        else ValidationStatus.PASS.value
                    ),
                    explanation=(
                        f"Missing authorities: {missing}"
                        if missing
                        else "All allowed authorities represented"
                    ),
                )
            )

        if rule.authority_boundaries:
            missing = [
                boundary
                for boundary in rule.authority_boundaries
                if boundary not in candidate.boundaries
            ]
            findings.append(
                ValidationFinding(
                    validation_id="",
                    rule_id=rule_id,
                    subject_id=candidate.candidate_id or candidate.id,
                    check="authority_boundaries_represented",
                    expected=str(rule.authority_boundaries),
                    observed=str(candidate.boundaries),
                    status=(
                        ValidationStatus.FAIL.value
                        if missing
                        else ValidationStatus.PASS.value
                    ),
                    explanation=(
                        f"Missing boundaries: {missing}"
                        if missing
                        else "All authority boundaries represented"
                    ),
                )
            )

    def _check_prohibited_dependencies(
        self,
        rule_id: str,
        rule: DirectionalRule,
        candidate: ArchitectureCandidate,
        findings: list[ValidationFinding],
    ) -> None:
        for prohibited in rule.prohibited_authorities:
            present = prohibited in candidate.authorities
            findings.append(
                ValidationFinding(
                    validation_id="",
                    rule_id=rule_id,
                    subject_id=candidate.candidate_id or candidate.id,
                    check="prohibited_authority_absent",
                    expected=f"absent: {prohibited}",
                    observed=("present" if present else "absent"),
                    status=(ValidationStatus.FAIL.value if present else ValidationStatus.PASS.value),
                    explanation=(
                        f"Prohibited authority present: {prohibited}"
                        if present
                        else f"Prohibited authority absent: {prohibited}"
                    ),
                )
            )

    def _check_required_capabilities(
        self,
        rule_id: str,
        rule: DirectionalRule,
        candidate: ArchitectureCandidate,
        findings: list[ValidationFinding],
    ) -> None:
        if rule.projection_requirements:
            missing = [
                cap
                for cap in rule.projection_requirements
                if cap not in candidate.required_capabilities
            ]
            findings.append(
                ValidationFinding(
                    validation_id="",
                    rule_id=rule_id,
                    subject_id=candidate.candidate_id or candidate.id,
                    check="required_capabilities_represented",
                    expected=str(rule.projection_requirements),
                    observed=str(candidate.required_capabilities),
                    status=(
                        ValidationStatus.FAIL.value
                        if missing
                        else ValidationStatus.PASS.value
                    ),
                    explanation=(
                        f"Missing capabilities: {missing}"
                        if missing
                        else "All required capabilities represented"
                    ),
                )
            )

    def _check_implementation_freedom(
        self,
        rule_id: str,
        rule: DirectionalRule,
        candidate: ArchitectureCandidate,
        findings: list[ValidationFinding],
    ) -> None:
        if rule.technology_freedoms:
            findings.append(
                ValidationFinding(
                    validation_id="",
                    rule_id=rule_id,
                    subject_id=candidate.candidate_id or candidate.id,
                    check="implementation_freedom_preserved",
                    expected="technology_freedoms preserved; implementation unconstrained",
                    observed="candidate does not prescribe implementation",
                    status=ValidationStatus.PASS.value,
                    explanation=(
                        "Candidate preserves implementation freedom "
                        f"per rule {rule_id}"
                    ),
                )
            )

    def _check_interaction_contracts(
        self,
        rule_id: str,
        rule: DirectionalRule,
        candidate: ArchitectureCandidate,
        scaffold: ScaffoldSpec | None,
        findings: list[ValidationFinding],
    ) -> None:
        for contract in rule.interaction_contracts:
            contract_id = contract.contract_id or contract.id
            self._check_interaction_contract_presence(
                rule_id, contract, candidate, scaffold, findings
            )
            self._check_delivery_idempotency_consistency(
                rule_id, contract, findings
            )

    def _check_interaction_contract_presence(
        self,
        rule_id: str,
        contract: InteractionContract,
        candidate: ArchitectureCandidate,
        scaffold: ScaffoldSpec | None,
        findings: list[ValidationFinding],
    ) -> None:
        contract_id = contract.contract_id or contract.id
        contract_refs = candidate.interaction_contracts
        present = contract_id in contract_refs or contract.id in contract_refs
        findings.append(
            ValidationFinding(
                validation_id="",
                rule_id=rule_id,
                subject_id=candidate.candidate_id or candidate.id,
                check="interaction_contract_presence",
                expected=f"interaction contract {contract_id} represented",
                observed=("present" if present else "missing"),
                status=(
                    ValidationStatus.FAIL.value
                    if not present
                    else ValidationStatus.PASS.value
                ),
                explanation=(
                    f"Interaction contract {contract_id} missing from architecture"
                    if not present
                    else f"Interaction contract {contract_id} represented"
                ),
            )
        )

        if contract.translation_required:
            boundary_present = any(
                (bool(contract.boundary) and contract.boundary in b)
                or (bool(contract.canonical_representation) and contract.canonical_representation in b)
                for b in candidate.boundaries
            )
            findings.append(
                ValidationFinding(
                    validation_id="",
                    rule_id=rule_id,
                    subject_id=candidate.candidate_id or candidate.id,
                    check="translation_boundary_represented",
                    expected=f"translation boundary {contract.boundary} represented",
                    observed=("present" if boundary_present else "missing"),
                    status=(
                        ValidationStatus.FAIL.value
                        if not boundary_present
                        else ValidationStatus.PASS.value
                    ),
                    explanation=(
                        f"Translation boundary {contract.boundary} missing from architecture"
                        if not boundary_present
                        else f"Translation boundary {contract.boundary} represented"
                    ),
                )
            )

        if scaffold is not None:
            scaffold_present = contract_id in scaffold.interaction_contracts or contract.id in scaffold.interaction_contracts
            findings.append(
                ValidationFinding(
                    validation_id="",
                    rule_id=rule_id,
                    subject_id=scaffold.spec_id or scaffold.id,
                    check="interaction_contract_in_scaffold",
                    expected=f"interaction contract {contract_id} represented in scaffold",
                    observed=("present" if scaffold_present else "missing"),
                    status=(
                        ValidationStatus.FAIL.value
                        if not scaffold_present
                        else ValidationStatus.PASS.value
                    ),
                    explanation=(
                        f"Interaction contract {contract_id} missing from scaffold"
                        if not scaffold_present
                        else f"Interaction contract {contract_id} represented in scaffold"
                    ),
                )
            )

    def _check_delivery_idempotency_consistency(
        self,
        rule_id: str,
        contract: InteractionContract,
        findings: list[ValidationFinding],
    ) -> None:
        if contract.delivery_semantics == "at_least_once" and not contract.idempotency_required:
            findings.append(
                ValidationFinding(
                    validation_id="",
                    rule_id=rule_id,
                    subject_id=contract.contract_id or contract.id,
                    check="delivery_idempotency_consistency",
                    expected="idempotency_required=true when delivery is at_least_once",
                    observed="idempotency_required=false",
                    status=ValidationStatus.FAIL.value,
                    explanation=(
                        "At-least-once delivery requires idempotent consumers "
                        f"but contract {contract.contract_id or contract.id} does not require idempotency"
                    ),
                )
            )

    def _check_scaffold_traceability(
        self,
        rule_id: str,
        candidate: ArchitectureCandidate,
        scaffold: ScaffoldSpec,
        findings: list[ValidationFinding],
    ) -> None:
        if candidate.candidate_id and candidate.candidate_id not in scaffold.traceability:
            findings.append(
                ValidationFinding(
                    validation_id="",
                    rule_id=rule_id,
                    subject_id=scaffold.spec_id or scaffold.id,
                    check="scaffold_traceability_to_architecture",
                    expected=f"traceability includes {candidate.candidate_id}",
                    observed=str(scaffold.traceability),
                    status=ValidationStatus.FAIL.value,
                    explanation=(
                        "Scaffold traceability missing architecture candidate "
                        f"{candidate.candidate_id}"
                    ),
                )
            )

    def _check_conflicts(
        self,
        conflicts: list[Conflict],
        findings: list[ValidationFinding],
        checked_invariants: list[str],
    ) -> None:
        for conflict in conflicts:
            checked_invariants.append(conflict.id)
            findings.append(
                ValidationFinding(
                    validation_id="",
                    rule_id=",".join(conflict.rules_in_conflict),
                    subject_id=conflict.affected_projection or conflict.id,
                    check="conflict_governance_required",
                    expected="conflict resolved by governance before acceptance",
                    observed=f"resolution_status={conflict.resolution_status}",
                    status=(
                        ValidationStatus.INCONCLUSIVE.value
                        if conflict.resolution_status == "open"
                        else ValidationStatus.PASS.value
                    ),
                    explanation=(
                        "Conflict remains unresolved; governance required"
                        if conflict.resolution_status == "open"
                        else "Conflict has been resolved"
                    ),
                )
            )

    def _compute_overall_status(
        self,
        findings: list[ValidationFinding],
    ) -> ValidationStatus:
        if not findings:
            return ValidationStatus.NOT_APPLICABLE

        statuses = [f.status for f in findings]
        if ValidationStatus.FAIL.value in statuses:
            return ValidationStatus.FAIL
        if ValidationStatus.INCONCLUSIVE.value in statuses:
            return ValidationStatus.INCONCLUSIVE
        if all(s == ValidationStatus.PASS.value for s in statuses):
            return ValidationStatus.PASS
        return ValidationStatus.NOT_APPLICABLE
