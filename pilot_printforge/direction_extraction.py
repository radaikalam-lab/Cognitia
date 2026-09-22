"""PrintForge Direction Extraction.

This module translates PrintForge architectural intent into generic
DirectionalRule objects. It is explicitly PrintForge-specific and lives
outside the generic DP kernel.

The generic DP kernel (cognitia.project_spec) must remain domain-neutral.
This adapter is the boundary where PrintForge-specific knowledge is
translated into generic directional specifications.
"""

from __future__ import annotations

from typing import Any

from cognitia.project_spec.types import (
    ArchitectureCandidate,
    DirectionalRule,
    DirectionalRuleStatus,
    DirectionalSpec,
    InteractionContract,
    ProjectionResult,
    RelationshipType,
    ScaffoldSpec,
    Traceability,
)
from cognitia.project_spec.projection import InMemoryProjectionService
from cognitia.project_spec.provider import DeterministicProjectionProvider
from validator.project_spec_validator import DeterministicProjectSpecValidator
from validator.types import ValidationResult, ValidationStatus


class PrintForgeDirectionExtractor:
    """Extracts generic directional rules from PrintForge architectural intent.

    This class is explicitly PrintForge-specific. It translates PrintForge
    ADRs, contracts, and architecture into generic DP artifacts.

    The output of this class is generic DP objects. The translation logic
    is PrintForge-specific.
    """

    def extract_authority_rules(self) -> list[DirectionalRule]:
        """Extract authority model rules from PrintForge ADR-001."""
        return [
            DirectionalRule(
                rule_id="PF-AUTH-001",
                version="1.0.0",
                status=DirectionalRuleStatus.PROPOSED,
                current_state="no explicit authority boundaries",
                desired_state="explicit multi-scope authority boundaries",
                objectives=[
                    "establish four distinct authority scopes",
                    "ensure application state ownership is explicit",
                ],
                constraints=[
                    "observation != physical authority",
                    "proposal != approval",
                    "epistemic != production authority",
                ],
                allowed_authorities=["application", "provider_execution", "physical_printer", "epistemic_advisory"],
                prohibited_authorities=["epistemic_authority_for_execution"],
                authority_boundaries=[
                    "application_authority != provider_authority",
                    "provider_authority != physical_authority",
                    "epistemic_advisory != production_authority",
                ],
                observables=["authority_boundary_violations", "cross_scope_mutations"],
                acceptance_conditions=[
                    "each scope has clear non-overlapping responsibilities",
                    "epistemic cannot authorize execution",
                    "providers cannot mutate domain state",
                ],
                evidence_requirements=["authority_contract", "epistemic_boundary_contract"],
                provenance_requirements=["immutable_authority_log"],
                implementation_scope="authority boundary enforcement",
                governance_notes="requires governance acceptance before activation",
                conflict_policy="escalate_to_governance",
                scaffold_constraints=["authority_boundary_surfaces", "contract_surfaces"],
                technology_freedoms=["any_authority_enforcement_mechanism"],
                projection_requirements=["traceability_preserved", "authority_verification"],
            ),
            DirectionalRule(
                rule_id="PF-AUTH-002",
                version="1.0.0",
                status=DirectionalRuleStatus.PROPOSED,
                current_state="multiple components can propose state changes",
                desired_state="single writer of lifecycle state",
                objectives=[
                    "establish single-writer semantics for lifecycle state",
                    "isolate state proposal from state mutation",
                ],
                constraints=[
                    "only one component may mutate lifecycle state",
                    "all other components produce proposals only",
                ],
                allowed_authorities=["job_manager"],
                prohibited_authorities=["scheduler", "policy_engine", "provider", "observation_engine", "epistemic_subsystem"],
                authority_boundaries=["lifecycle_state_mutation_authority == job_manager"],
                observables=["lifecycle_state_changes", "proposed_transitions"],
                acceptance_conditions=[
                    "job_manager is sole lifecycle writer",
                    "all state transitions are auditable",
                ],
                evidence_requirements=["state_transition_log", "single_writer_proof"],
                provenance_requirements=["immutable_state_history"],
                implementation_scope="lifecycle state ownership",
                governance_notes="requires governance acceptance before activation",
                conflict_policy="escalate_to_governance",
                scaffold_constraints=["state_ownership_surface", "transition_contract"],
                technology_freedoms=["any_state_storage", "any_transition_mechanism"],
                projection_requirements=["traceability_preserved", "single_writer_verification"],
            ),
        ]

    def extract_boundary_rules(self) -> list[DirectionalRule]:
        """Extract boundary rules from PrintForge provider and epistemic ADRs."""
        return [
            DirectionalRule(
                rule_id="PF-BOUND-001",
                version="1.0.0",
                status=DirectionalRuleStatus.PROPOSED,
                current_state="providers may directly influence core state",
                desired_state="providers isolated behind well-defined interfaces",
                objectives=[
                    "establish provider boundary",
                    "ensure provider failures do not corrupt core state",
                ],
                constraints=[
                    "providers may not mutate domain state",
                    "providers may not bypass policy",
                    "provider failures must be isolated",
                ],
                allowed_authorities=["provider_execution"],
                prohibited_authorities=["provider_domain_mutation", "provider_policy_bypass"],
                authority_boundaries=[
                    "provider_boundary_enforced",
                    "core_never_trusts_provider_output_without_validation",
                ],
                observables=["provider_failures", "provider_outputs", "circuit_breaker_state"],
                acceptance_conditions=[
                    "provider interface is stable and versioned",
                    "provider failures are isolated",
                    "core continues operating with failed providers",
                ],
                evidence_requirements=["provider_contract", "isolation_test_evidence"],
                provenance_requirements=["provider_output_provenance"],
                implementation_scope="provider isolation mechanism",
                governance_notes="requires governance acceptance before activation",
                conflict_policy="escalate_to_governance",
                scaffold_constraints=["provider_interface_surface", "adapter_boundary"],
                technology_freedoms=["any_protocol", "any_isolation_mechanism"],
                projection_requirements=["traceability_preserved", "isolation_verification"],
                interaction_contracts=[
                    InteractionContract(
                        contract_id="PF-IC-001",
                        boundary="provider_adapter_boundary",
                        canonical_representation="canonical_internal_contract",
                        translation_required=True,
                        delivery_semantics="unspecified",
                        idempotency_required=False,
                        observables=["translation_boundary_crossings"],
                    )
                ],
            ),
            DirectionalRule(
                rule_id="PF-BOUND-002",
                version="1.0.0",
                status=DirectionalRuleStatus.PROPOSED,
                current_state="epistemic and execution paths are conflated",
                desired_state="epistemic advisory path never becomes execution path",
                objectives=[
                    "establish observation/epistemic boundary",
                    "prohibit epistemic-to-provider execution path",
                ],
                constraints=[
                    "epistemic cannot execute printer operations",
                    "epistemic cannot mutate production state",
                    "epistemic cannot bypass validation",
                ],
                allowed_authorities=["epistemic_advisory"],
                prohibited_authorities=["epistemic_execution", "epistemic_production_mutation"],
                authority_boundaries=[
                    "epistemic_advisory_only",
                    "observation_engine != epistemic_creator",
                ],
                observables=["epistemic_qualification", "observation_provenance", "reconciliation_state"],
                acceptance_conditions=[
                    "epistemic path is advisory only",
                    "observation and epistemic ownership are distinct",
                    "epistemic cannot cause physical execution",
                ],
                evidence_requirements=["epistemic_boundary_contract", "observation_evidence_contract"],
                provenance_requirements=["epistemic_provenance_chain"],
                implementation_scope="epistemic boundary enforcement",
                governance_notes="requires governance acceptance before activation",
                conflict_policy="escalate_to_governance",
                scaffold_constraints=["epistemic_advisory_surface", "observation_ingestion_surface"],
                technology_freedoms=["any_epistemic_mechanism", "any_qualification_algorithm"],
                projection_requirements=["traceability_preserved", "boundary_verification"],
            ),
        ]

    def extract_invariant_rules(self) -> list[DirectionalRule]:
        """Extract invariant rules from PrintForge deterministic core and reconciliation ADRs."""
        return [
            DirectionalRule(
                rule_id="PF-INV-001",
                version="1.0.0",
                status=DirectionalRuleStatus.PROPOSED,
                current_state="core contains side effects and non-determinism",
                desired_state="deterministic core with explicit side-effect boundary",
                objectives=[
                    "establish deterministic core",
                    "push side effects to explicit boundaries",
                ],
                constraints=[
                    "core business logic is pure and deterministic",
                    "time, randomness, and I/O are injected dependencies",
                    "deterministic mode is first-class",
                ],
                allowed_authorities=[],
                prohibited_authorities=[],
                authority_boundaries=["side_effect_boundary_explicit"],
                observables=["determinism_violations", "side_effect_boundary_crossings"],
                acceptance_conditions=[
                    "core functions are pure",
                    "identical inputs produce identical outputs",
                    "side effects are explicit and injectable",
                ],
                evidence_requirements=["determinism_contract", "property_based_test_evidence"],
                provenance_requirements=["deterministic_execution_provenance"],
                implementation_scope="deterministic core design",
                governance_notes="requires governance acceptance before activation",
                conflict_policy="escalate_to_governance",
                scaffold_constraints=["pure_core_surface", "side_effect_adapter_surface"],
                technology_freedoms=["any_test_framework", "any_determinism_mechanism"],
                projection_requirements=["traceability_preserved", "determinism_verification"],
            ),
            DirectionalRule(
                rule_id="PF-INV-002",
                version="1.0.0",
                status=DirectionalRuleStatus.PROPOSED,
                current_state="capability conflicts are silently resolved",
                desired_state="all contradictions are explicit and auditable",
                objectives=[
                    "establish multi-dimensional reconciliation",
                    "preserve all evidence explicitly",
                ],
                constraints=[
                    "declarations and observations are never silently overwritten",
                    "contradictions remain visible",
                    "stale observations remain identifiable",
                    "unknown must not silently become true or false",
                ],
                allowed_authorities=[],
                prohibited_authorities=[],
                authority_boundaries=["reconciliation_dimensions_independent"],
                observables=["reconciliation_outcomes", "contradictions", "stale_evidence"],
                acceptance_conditions=[
                    "all reconciliation dimensions are independent",
                    "contradictions are visible and auditable",
                    "both declaration and observation are preserved",
                ],
                evidence_requirements=["capability_contract", "observation_evidence_contract"],
                provenance_requirements=["reconciliation_provenance"],
                implementation_scope="reconciliation model",
                governance_notes="requires governance acceptance before activation",
                conflict_policy="escalate_to_governance",
                scaffold_constraints=["reconciliation_surface", "evidence_preservation_surface"],
                technology_freedoms=["any_reconciliation_algorithm", "any_evidence_store"],
                projection_requirements=["traceability_preserved", "reconciliation_verification"],
            ),
        ]

    def extract_provenance_rules(self) -> list[DirectionalRule]:
        """Extract provenance rules from PrintForge ADR-011."""
        return [
            DirectionalRule(
                rule_id="PF-PROV-001",
                version="1.0.0",
                status=DirectionalRuleStatus.PROPOSED,
                current_state="provenance is optional or best-effort",
                desired_state="every fact carries immutable provenance chain",
                objectives=[
                    "establish immutable provenance for all state changes and events",
                    "enable complete audit trails",
                ],
                constraints=[
                    "provenance is never discarded",
                    "normalized data and provenance remain separable",
                    "provenance chains are inspectable",
                ],
                allowed_authorities=[],
                prohibited_authorities=[],
                authority_boundaries=["provenance_immutable"],
                observables=["provenance_chains", "audit_trail_completeness"],
                acceptance_conditions=[
                    "every state change carries provenance",
                    "every event carries provenance",
                    "causal relationships are preserved",
                ],
                evidence_requirements=["provenance_contract", "epistemic_provenance_contract"],
                provenance_requirements=["full_causal_chain"],
                implementation_scope="provenance infrastructure",
                governance_notes="requires governance acceptance before activation",
                conflict_policy="escalate_to_governance",
                scaffold_constraints=["provenance_record_surface", "lineage_chain_surface"],
                technology_freedoms=["any_provenance_store", "any_serialization"],
                projection_requirements=["traceability_preserved", "provenance_verification"],
            ),
        ]

    def extract_execution_rules(self) -> list[DirectionalRule]:
        """Extract execution attempt and event delivery rules."""
        return [
            DirectionalRule(
                rule_id="PF-EXEC-001",
                version="1.0.0",
                status=DirectionalRuleStatus.PROPOSED,
                current_state="retries conflated with lifecycle transitions",
                desired_state="execution attempts separated from lifecycle state",
                objectives=[
                    "establish execution attempt as separate entity",
                    "preserve retry history explicitly",
                ],
                constraints=[
                    "execution attempts carry their own state",
                    "retry creates new execution attempt",
                    "printjob lifecycle remains clean",
                ],
                allowed_authorities=["provider_execution"],
                prohibited_authorities=["lifecycle_mutation_via_execution"],
                authority_boundaries=["execution_attempt_authority != lifecycle_authority"],
                observables=["execution_attempts", "retry_history", "attempt_provenance"],
                acceptance_conditions=[
                    "execution attempts are first-class entities",
                    "retry history is explicit and auditable",
                    "terminal states are unambiguous",
                ],
                evidence_requirements=["execution_contract", "attempt_history_log"],
                provenance_requirements=["attempt_provenance_chain"],
                implementation_scope="execution attempt model",
                governance_notes="requires governance acceptance before activation",
                conflict_policy="escalate_to_governance",
                scaffold_constraints=["execution_attempt_surface", "attempt_state_surface"],
                technology_freedoms=["any_attempt_storage", "any_retry_mechanism"],
                projection_requirements=["traceability_preserved", "execution_verification"],
            ),
            DirectionalRule(
                rule_id="PF-EXEC-002",
                version="1.0.0",
                status=DirectionalRuleStatus.PROPOSED,
                current_state="event delivery semantics are implicit",
                desired_state="at-least-once delivery with idempotent consumers",
                objectives=[
                    "establish explicit event delivery semantics",
                    "ensure event replay is supported",
                ],
                constraints=[
                    "at-least-once delivery",
                    "consumers must be idempotent",
                    "events may be replayed",
                    "undeliverable events move to dead-letter queue",
                ],
                allowed_authorities=[],
                prohibited_authorities=[],
                authority_boundaries=["event_delivery_semantic_boundary"],
                observables=["event_delivery_attempts", "duplicate_events", "dead_letter_queue"],
                acceptance_conditions=[
                    "delivery semantics are explicit",
                    "idempotency is enforced",
                    "replay is supported",
                ],
                evidence_requirements=["event_contract", "delivery_semantics_test"],
                provenance_requirements=["event_provenance_chain"],
                implementation_scope="event delivery infrastructure",
                governance_notes="requires governance acceptance before activation",
                conflict_policy="escalate_to_governance",
                scaffold_constraints=["event_bus_surface", "event_envelope_surface"],
                technology_freedoms=["any_event_broker", "any_delivery_mechanism"],
                projection_requirements=["traceability_preserved", "delivery_verification"],
                interaction_contracts=[
                    InteractionContract(
                        contract_id="PF-IC-002",
                        boundary="event_delivery_boundary",
                        canonical_representation="canonical_event_envelope",
                        translation_required=False,
                        delivery_semantics="at_least_once",
                        idempotency_required=True,
                        observables=["event_delivery_attempts", "duplicate_events", "dead_letter_queue"],
                    )
                ],
            ),
        ]

    def extract_storage_rules(self) -> list[DirectionalRule]:
        """Extract storage and persistence rules from PrintForge ADR-016 and ADR-017."""
        return [
            DirectionalRule(
                rule_id="PF-STOR-001",
                version="1.0.0",
                status=DirectionalRuleStatus.PROPOSED,
                current_state="storage technology is hardcoded",
                desired_state="pluggable storage backends with unified interface",
                objectives=[
                    "establish persistence abstraction layer",
                    "support multiple storage backends",
                ],
                constraints=[
                    "each data type uses optimal storage technology",
                    "core is decoupled from specific databases",
                    "atomicity within each backend",
                ],
                allowed_authorities=[],
                prohibited_authorities=[],
                authority_boundaries=["storage_abstraction_boundary"],
                observables=["storage_backend_usage", "backend_health"],
                acceptance_conditions=[
                    "storage backends are pluggable",
                    "core does not depend on specific databases",
                    "atomicity is enforced per backend",
                ],
                evidence_requirements=["spool_contract", "persistence_abstraction_evidence"],
                provenance_requirements=["storage_operation_provenance"],
                implementation_scope="persistence abstraction",
                governance_notes="requires governance acceptance before activation",
                conflict_policy="escalate_to_governance",
                scaffold_constraints=["storage_interface_surface", "backend_plugin_surface"],
                technology_freedoms=["any_storage_technology", "any_backend_implementation"],
                projection_requirements=["traceability_preserved", "storage_verification"],
            ),
        ]

    def extract_simulation_rules(self) -> list[DirectionalRule]:
        """Extract simulation-first rules from PrintForge ADR-020."""
        return [
            DirectionalRule(
                rule_id="PF-SIM-001",
                version="1.0.0",
                status=DirectionalRuleStatus.PROPOSED,
                current_state="testing requires physical hardware",
                desired_state="simulation-first development with deterministic mode",
                objectives=[
                    "enable development without physical hardware",
                    "establish deterministic simulation mode",
                ],
                constraints=[
                    "simulator implements same interfaces as real providers",
                    "deterministic mode is first-class",
                    "property-based testing is required for deterministic core",
                ],
                allowed_authorities=[],
                prohibited_authorities=[],
                authority_boundaries=["simulation_boundary"],
                observables=["simulation_fidelity", "deterministic_mode_usage"],
                acceptance_conditions=[
                    "simulator implements provider interface",
                    "deterministic mode is available",
                    "CI/CD uses simulator exclusively",
                ],
                evidence_requirements=["simulator_contract", "determinism_contract"],
                provenance_requirements=["simulation_provenance"],
                implementation_scope="simulation infrastructure",
                governance_notes="requires governance acceptance before activation",
                conflict_policy="escalate_to_governance",
                scaffold_constraints=["simulator_interface_surface", "deterministic_mode_surface"],
                technology_freedoms=["any_simulation_mechanism", "any_test_framework"],
                projection_requirements=["traceability_preserved", "simulation_verification"],
            ),
        ]

    def extract_all_rules(self) -> list[DirectionalRule]:
        """Extract all PrintForge directional rules."""
        rules = []
        rules.extend(self.extract_authority_rules())
        rules.extend(self.extract_boundary_rules())
        rules.extend(self.extract_invariant_rules())
        rules.extend(self.extract_provenance_rules())
        rules.extend(self.extract_execution_rules())
        rules.extend(self.extract_storage_rules())
        rules.extend(self.extract_simulation_rules())
        return rules

    def build_directional_spec(self) -> DirectionalSpec:
        """Build a complete PrintForge DirectionalSpec from extracted rules."""
        rules = self.extract_all_rules()
        return DirectionalSpec(
            rules=rules,
            metadata={
                "source": "PrintForge reference architecture",
                "reference_commit": "ad02b6d0c630d7d9f96a3702f60827dd759e847e",
                "extraction_version": "1.0.0",
                "description": "Directional specification derived from PrintForge ADRs and contracts",
            },
        )

    def build_projection_result(self) -> tuple[DirectionalSpec, ProjectionResult]:
        """Build a complete projection result from PrintForge directional spec."""
        spec = self.build_directional_spec()
        service = InMemoryProjectionService()
        result = service.project(spec)
        return spec, result

    def validate_projection_result(self, spec: DirectionalSpec, result: ProjectionResult) -> ValidationResult:
        """Validate the projection result using the independent validator."""
        if result.architecture_candidate is None or result.scaffold_spec is None:
            raise ValueError("Projection result must contain architecture candidate and scaffold spec")
        
        validator = DeterministicProjectSpecValidator()
        return validator.validate(
            specification=spec,
            candidate=result.architecture_candidate,
            scaffold=result.scaffold_spec,
            conflicts=list(result.conflicts),
            traceability=list(result.traceability),
        )
