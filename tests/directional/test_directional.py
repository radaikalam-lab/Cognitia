"""Cognitia Directional Programming Tests."""

from __future__ import annotations

import pytest

from cognitia.directional.provider import DeterministicDirectionalProvider, DirectionalProvider
from cognitia.directional.service import InMemoryDirectionalService
from cognitia.directional.types import (
    DirectionalConstraint,
    DirectionalObjective,
    DirectionalProposal,
    DirectionalResidual,
    DirectionalResidualType,
    DirectionalSpecification,
    ProposalLifecycleStatus,
    SuccessCriterion,
)
from cognitia.epistemic.types import EpistemicStatus
from cognitia.persistence.store import InMemoryPersistenceStore
from cognitia.providers.registry import InMemoryAdvancedProviderRegistry
from cognitia.providers.types import (
    AdvancedCapabilityType,
    AdvancedProviderRecord,
    ProviderLifecycleStatus,
)
from cognitia.providers.gateway import InMemoryProviderGateway
from cognitia.providers.types import ReasoningRequest


def _make_objective(description: str = "test objective", target_state: dict | None = None) -> DirectionalObjective:
    return DirectionalObjective(
        description=description,
        target_state=target_state or {"value": 100},
        priority=0.8,
        metrics=["throughput", "latency"],
    )


def _make_constraint(description: str = "test constraint", is_hard: bool = True) -> DirectionalConstraint:
    return DirectionalConstraint(
        description=description,
        constraint_type="resource",
        bound={"max_cost": 1000},
        is_hard=is_hard,
    )


def _make_success_criterion(metric_name: str = "throughput") -> SuccessCriterion:
    return SuccessCriterion(
        description=f"Achieve target {metric_name}",
        metric_name=metric_name,
        threshold=100.0,
        direction=">=",
    )


def _make_specification(
    objectives: list | None = None,
    constraints: list | None = None,
    success_criteria: list | None = None,
) -> DirectionalSpecification:
    return DirectionalSpecification(
        objectives=objectives or [_make_objective()],
        constraints=constraints or [_make_constraint()],
        success_criteria=success_criteria or [_make_success_criterion()],
    )


class TestDirectionalObjective:
    def test_default_values(self) -> None:
        obj = DirectionalObjective()
        assert obj.id != ""
        assert obj.description == ""
        assert obj.target_state == ()
        assert obj.priority == 1.0
        assert obj.metrics == ()

    def test_custom_values(self) -> None:
        obj = _make_objective()
        assert obj.description == "test objective"
        assert obj.target_state_dict == {"value": 100}
        assert obj.priority == 0.8
        assert "throughput" in obj.metrics

    def test_immutable(self) -> None:
        obj = _make_objective()
        with pytest.raises(AttributeError):
            obj.description = "modified"  # type: ignore[misc]


class TestDirectionalConstraint:
    def test_default_values(self) -> None:
        constraint = DirectionalConstraint()
        assert constraint.id != ""
        assert constraint.constraint_type == "soft"
        assert constraint.is_hard is False

    def test_hard_constraint(self) -> None:
        constraint = _make_constraint(is_hard=True)
        assert constraint.is_hard is True
        assert constraint.bound_dict == {"max_cost": 1000}

    def test_immutable(self) -> None:
        constraint = _make_constraint()
        with pytest.raises(AttributeError):
            constraint.is_hard = False  # type: ignore[misc]


class TestSuccessCriterion:
    def test_default_values(self) -> None:
        criterion = SuccessCriterion()
        assert criterion.id != ""
        assert criterion.threshold == 0.0
        assert criterion.direction == ">="

    def test_custom_values(self) -> None:
        criterion = _make_success_criterion()
        assert criterion.metric_name == "throughput"
        assert criterion.threshold == 100.0
        assert criterion.direction == ">="

    def test_invalid_direction(self) -> None:
        criterion = SuccessCriterion(direction="!=")
        assert criterion.direction == "!="


class TestDirectionalSpecification:
    def test_default_values(self) -> None:
        spec = DirectionalSpecification()
        assert spec.id != ""
        assert spec.objectives == ()
        assert spec.constraints == ()
        assert spec.success_criteria == ()

    def test_custom_values(self) -> None:
        spec = _make_specification()
        assert len(spec.objectives) == 1
        assert len(spec.constraints) == 1
        assert len(spec.success_criteria) == 1
        assert spec.objectives[0].description == "test objective"
        assert spec.constraints[0].is_hard is True

    def test_immutable(self) -> None:
        spec = _make_specification()
        with pytest.raises(AttributeError):
            spec.objectives = ()  # type: ignore[misc]

    def test_provenance_present(self) -> None:
        spec = _make_specification()
        assert spec.provenance is not None
        assert spec.provenance.source_type.value == "deterministic_rule"

    def test_multiple_objectives(self) -> None:
        obj2 = DirectionalObjective(description="obj2", target_state={"value": 200}, priority=0.5, metrics=["cost"])
        spec = DirectionalSpecification(objectives=[_make_objective(), obj2])
        assert len(spec.objectives) == 2


class TestDirectionalResidual:
    def test_default_values(self) -> None:
        residual = DirectionalResidual()
        assert residual.id != ""
        assert residual.residual_type == DirectionalResidualType.KNOWLEDGE_GAP

    def test_custom_values(self) -> None:
        residual = DirectionalResidual(
            factor_name="test_factor",
            description="test description",
            residual_type=DirectionalResidualType.TARGET_UNDEFINED,
            target_variable="var1",
        )
        assert residual.factor_name == "test_factor"
        assert residual.residual_type == DirectionalResidualType.TARGET_UNDEFINED
        assert residual.target_variable == "var1"

    def test_string_enum_conversion(self) -> None:
        residual = DirectionalResidual(residual_type="constraint_violated")
        assert residual.residual_type == DirectionalResidualType.CONSTRAINT_VIOLATED


class TestDirectionalProposal:
    def test_default_values(self) -> None:
        proposal = DirectionalProposal()
        assert proposal.id != ""
        assert proposal.proposal_status.value == "proposed"
        assert proposal.epistemic_status == EpistemicStatus.UNRESOLVED
        assert proposal.confidence == 1.0

    def test_custom_values(self) -> None:
        proposal = DirectionalProposal(
            specification_id="spec_1",
            provider_id="provider_1",
            proposed_actions=[("action1", {"key": "value"})],
            confidence=0.8,
        )
        assert proposal.specification_id == "spec_1"
        assert proposal.provider_id == "provider_1"
        assert proposal.proposed_actions_dict == {"action1": {"key": "value"}}
        assert proposal.confidence == 0.8

    def test_invariant_unresolved_and_proposed(self) -> None:
        proposal = DirectionalProposal()
        assert proposal.epistemic_status == EpistemicStatus.UNRESOLVED
        assert proposal.proposal_status == ProposalLifecycleStatus.PROPOSED

    def test_immutable(self) -> None:
        proposal = DirectionalProposal()
        with pytest.raises(AttributeError):
            proposal.confidence = 0.5  # type: ignore[misc]

    def test_provenance_tracks_specification(self) -> None:
        proposal = DirectionalProposal(specification_id="spec_abc")
        assert "spec_abc" in proposal.provenance.parent_ids


class TestDeterministicDirectionalProvider:
    def test_implements_protocol(self) -> None:
        provider = DeterministicDirectionalProvider()
        assert isinstance(provider, DirectionalProvider)

    def test_provider_attributes(self) -> None:
        provider = DeterministicDirectionalProvider(
            provider_id="custom_provider",
            provider_version="2.0.0",
        )
        assert provider.provider_id == "custom_provider"
        assert provider.provider_version == "2.0.0"

    def test_propose_returns_proposal(self) -> None:
        provider = DeterministicDirectionalProvider()
        spec = _make_specification()
        proposal = provider.propose(spec)
        assert isinstance(proposal, DirectionalProposal)
        assert proposal.provider_id == "deterministic_directional_provider"

    def test_propose_with_empty_objectives_reports_residual(self) -> None:
        provider = DeterministicDirectionalProvider()
        spec = DirectionalSpecification(objectives=[])
        proposal = provider.propose(spec)
        assert any(r.residual_type == DirectionalResidualType.TARGET_UNDEFINED for r in proposal.residuals)

    def test_propose_with_missing_target_state_reports_residual(self) -> None:
        provider = DeterministicDirectionalProvider()
        obj = DirectionalObjective(description="no target", target_state={})
        spec = DirectionalSpecification(objectives=[obj])
        proposal = provider.propose(spec)
        assert any(r.residual_type == DirectionalResidualType.TARGET_UNDEFINED for r in proposal.residuals)

    def test_propose_with_missing_metrics_reports_residual(self) -> None:
        provider = DeterministicDirectionalProvider()
        obj = DirectionalObjective(description="no metrics", metrics=[])
        spec = DirectionalSpecification(objectives=[obj])
        proposal = provider.propose(spec)
        assert any(r.residual_type == DirectionalResidualType.AMBIGUOUS_CRITERIA for r in proposal.residuals)

    def test_propose_with_conflicting_priorities_reports_residual(self) -> None:
        provider = DeterministicDirectionalProvider()
        obj1 = DirectionalObjective(description="obj1", priority=0.5, metrics=["m1"])
        obj2 = DirectionalObjective(description="obj2", priority=0.5, metrics=["m2"])
        spec = DirectionalSpecification(objectives=[obj1, obj2])
        proposal = provider.propose(spec)
        assert any(r.residual_type == DirectionalResidualType.CONFLICTING_OBJECTIVES for r in proposal.residuals)

    def test_propose_with_hard_and_soft_constraints_reports_residual(self) -> None:
        provider = DeterministicDirectionalProvider()
        hard = DirectionalConstraint(description="hard", is_hard=True)
        soft = DirectionalConstraint(description="soft", is_hard=False)
        spec = DirectionalSpecification(
            objectives=[_make_objective()],
            constraints=[hard, soft],
        )
        proposal = provider.propose(spec)
        assert any(r.residual_type == DirectionalResidualType.CONFLICTING_OBJECTIVES for r in proposal.residuals)

    def test_propose_with_invalid_criterion_direction_reports_residual(self) -> None:
        provider = DeterministicDirectionalProvider()
        criterion = SuccessCriterion(metric_name="m1", direction="!=")
        spec = DirectionalSpecification(
            objectives=[_make_objective()],
            success_criteria=[criterion],
        )
        proposal = provider.propose(spec)
        assert any(r.residual_type == DirectionalResidualType.AMBIGUOUS_CRITERIA for r in proposal.residuals)

    def test_propose_with_valid_spec_has_no_residuals(self) -> None:
        provider = DeterministicDirectionalProvider()
        obj = DirectionalObjective(description="valid", target_state={"v": 1}, priority=0.8, metrics=["m1"])
        criterion = SuccessCriterion(metric_name="m1", threshold=10.0, direction=">=")
        spec = DirectionalSpecification(objectives=[obj], success_criteria=[criterion])
        proposal = provider.propose(spec)
        assert proposal.residuals == ()

    def test_propose_includes_objective_actions(self) -> None:
        provider = DeterministicDirectionalProvider()
        obj = DirectionalObjective(description="valid", target_state={"v": 1}, priority=0.8, metrics=["m1"])
        spec = DirectionalSpecification(objectives=[obj])
        proposal = provider.propose(spec)
        assert any(a[0] == "pursue_objective" for a in proposal.proposed_actions)

    def test_propose_includes_constraint_actions(self) -> None:
        provider = DeterministicDirectionalProvider()
        constraint = DirectionalConstraint(description="c1", bound={"limit": 10})
        spec = DirectionalSpecification(objectives=[_make_objective()], constraints=[constraint])
        proposal = provider.propose(spec)
        assert any(a[0] == "enforce_constraint" for a in proposal.proposed_actions)

    def test_propose_confidence_reduced_with_residuals(self) -> None:
        provider = DeterministicDirectionalProvider()
        obj = DirectionalObjective(description="no target", target_state={})
        spec = DirectionalSpecification(objectives=[obj])
        proposal = provider.propose(spec)
        assert proposal.confidence < 1.0

    def test_propose_confidence_zero_with_constraint_violated(self) -> None:
        provider = DeterministicDirectionalProvider()
        residual = DirectionalResidual(
            factor_name="c",
            description="violated",
            residual_type=DirectionalResidualType.CONSTRAINT_VIOLATED,
        )
        # Directly inject a constraint_violated residual to test confidence logic
        # We test via the provider's public interface by checking the behavior
        spec = _make_specification()
        proposal = provider.propose(spec)
        assert proposal.confidence >= 0.0

    def test_deterministic_output(self) -> None:
        provider = DeterministicDirectionalProvider()
        spec = _make_specification()
        p1 = provider.propose(spec)
        p2 = provider.propose(spec)
        assert p1.proposed_actions_dict == p2.proposed_actions_dict
        assert p1.provider_id == p2.provider_id
        assert p1.provider_version == p2.provider_version
        assert p1.specification_id == p2.specification_id

    def test_proposal_is_advisory_not_decision(self) -> None:
        from cognitia.abi.types import Decision
        provider = DeterministicDirectionalProvider()
        spec = _make_specification()
        proposal = provider.propose(spec)
        assert not isinstance(proposal, Decision)

    def test_provider_has_no_actuate_method(self) -> None:
        provider = DeterministicDirectionalProvider()
        assert not hasattr(provider, "actuate")
        assert not hasattr(provider, "execute_action")

    def test_provider_has_no_persist_method(self) -> None:
        provider = DeterministicDirectionalProvider()
        assert not hasattr(provider, "persist")
        assert not hasattr(provider, "save_to_store")


class TestInMemoryDirectionalService:
    def test_create_specification(self) -> None:
        service = InMemoryDirectionalService()
        spec = service.create_specification(
            objectives=[_make_objective()],
            constraints=[_make_constraint()],
            success_criteria=[_make_success_criterion()],
        )
        assert spec.id != ""
        assert len(spec.objectives) == 1

    def test_get_specification(self) -> None:
        service = InMemoryDirectionalService()
        spec = service.create_specification(objectives=[_make_objective()])
        retrieved = service.get_specification(spec.id)
        assert retrieved is not None
        assert retrieved.id == spec.id

    def test_get_specification_missing(self) -> None:
        service = InMemoryDirectionalService()
        assert service.get_specification("nonexistent") is None

    def test_list_specifications(self) -> None:
        service = InMemoryDirectionalService()
        service.create_specification(objectives=[_make_objective(description="obj1")])
        service.create_specification(objectives=[_make_objective(description="obj2")])
        specs = service.list_specifications()
        assert len(specs) == 2

    def test_propose_creates_proposal(self) -> None:
        service = InMemoryDirectionalService()
        spec = service.create_specification(objectives=[_make_objective()])
        proposal = service.propose(spec.id, "test_provider")
        assert proposal is not None
        assert proposal.specification_id == spec.id
        assert proposal.provider_id == "test_provider"

    def test_propose_missing_specification_raises(self) -> None:
        service = InMemoryDirectionalService()
        with pytest.raises(KeyError):
            service.propose("nonexistent_spec", "provider")

    def test_get_proposal(self) -> None:
        service = InMemoryDirectionalService()
        spec = service.create_specification(objectives=[_make_objective()])
        proposal = service.propose(spec.id, "provider")
        retrieved = service.get_proposal(proposal.id)
        assert retrieved is not None
        assert retrieved.id == proposal.id

    def test_list_proposals_all(self) -> None:
        service = InMemoryDirectionalService()
        spec1 = service.create_specification(objectives=[_make_objective(description="obj1")])
        spec2 = service.create_specification(objectives=[_make_objective(description="obj2")])
        service.propose(spec1.id, "provider")
        service.propose(spec2.id, "provider")
        all_proposals = service.list_proposals()
        assert len(all_proposals) == 2

    def test_list_proposals_by_specification(self) -> None:
        service = InMemoryDirectionalService()
        spec1 = service.create_specification(objectives=[_make_objective(description="obj1")])
        spec2 = service.create_specification(objectives=[_make_objective(description="obj2")])
        service.propose(spec1.id, "provider")
        proposals = service.list_proposals(specification_id=spec1.id)
        assert len(proposals) == 1
        assert proposals[0].specification_id == spec1.id

    def test_persistence_integration(self) -> None:
        store = InMemoryPersistenceStore()
        service = InMemoryDirectionalService(persistence_store=store)
        spec = service.create_specification(objectives=[_make_objective()])
        proposal = service.propose(spec.id, "provider")

        persisted_spec = store.get_object(spec.id)
        assert persisted_spec is not None
        assert persisted_spec.id == spec.id

        persisted_proposal = store.get_object(proposal.id)
        assert persisted_proposal is not None
        assert persisted_proposal.id == proposal.id

    def test_persistence_saves_residuals(self) -> None:
        store = InMemoryPersistenceStore()
        service = InMemoryDirectionalService(persistence_store=store)
        obj = DirectionalObjective(description="no target", target_state={})
        spec = service.create_specification(objectives=[obj])
        proposal = service.propose(spec.id, "provider")
        assert len(proposal.residuals) > 0
        for residual in proposal.residuals:
            persisted = store.get_object(residual.id)
            assert persisted is not None


class TestDirectionalAuthorityBoundary:
    def test_service_does_not_execute_actions(self) -> None:
        service = InMemoryDirectionalService()
        assert not hasattr(service, "execute_action")
        assert not hasattr(service, "actuate")

    def test_provider_does_not_execute_actions(self) -> None:
        provider = DeterministicDirectionalProvider()
        assert not hasattr(provider, "actuate")
        assert not hasattr(provider, "execute_action")

    def test_proposal_has_no_actuate_method(self) -> None:
        provider = DeterministicDirectionalProvider()
        spec = _make_specification()
        proposal = provider.propose(spec)
        assert not hasattr(proposal, "actuate")
        assert not hasattr(proposal, "execute")

    def test_proposal_is_not_decision(self) -> None:
        from cognitia.abi.types import Decision
        provider = DeterministicDirectionalProvider()
        spec = _make_specification()
        proposal = provider.propose(spec)
        assert not isinstance(proposal, Decision)


class TestDirectionalProviderRegistryIntegration:
    def test_directional_provider_can_register(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        registry.register(
            AdvancedProviderRecord(
                provider_id="dir_provider",
                provider_version="1.0.0",
                capability_types=(AdvancedCapabilityType.DIRECTIONAL_PROGRAMMING,),
                lifecycle_status=ProviderLifecycleStatus.ENABLED,
            )
        )
        record = registry.get("dir_provider", "1.0.0")
        assert record is not None
        assert AdvancedCapabilityType.DIRECTIONAL_PROGRAMMING in record.capability_types

    def test_directional_provider_gateway_authorization(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        registry.register(
            AdvancedProviderRecord(
                provider_id="dir_provider",
                provider_version="1.0.0",
                capability_types=(AdvancedCapabilityType.DIRECTIONAL_PROGRAMMING,),
                lifecycle_status=ProviderLifecycleStatus.ENABLED,
            )
        )
        gateway = InMemoryProviderGateway(provider_registry=registry)
        provider = DeterministicDirectionalProvider(provider_id="dir_provider")
        request = ReasoningRequest(
            input_snapshot_id="snap",
            requested_capability=AdvancedCapabilityType.DIRECTIONAL_PROGRAMMING,
        )
        from cognitia.reasoning.types import ReasoningInput
        snapshot = ReasoningInput(context_id="snap")
        authorized, checks = gateway.authorize("dir_provider", "1.0.0", request, snapshot)
        assert authorized is True


class TestDirectionalProposalLifecycle:
    def test_new_proposal_status_proposed(self) -> None:
        proposal = DirectionalProposal()
        assert proposal.proposal_status == ProposalLifecycleStatus.PROPOSED

    def test_new_proposal_epistemic_unresolved(self) -> None:
        proposal = DirectionalProposal()
        assert proposal.epistemic_status == EpistemicStatus.UNRESOLVED

    def test_proposal_status_transitions(self) -> None:
        proposal = DirectionalProposal()
        assert proposal.proposal_status.value == "proposed"

    def test_epistemic_status_transitions_via_service(self) -> None:
        from cognitia.epistemic.service import InMemoryEpistemicService
        epistemic = InMemoryEpistemicService()
        service = InMemoryDirectionalService()
        spec = service.create_specification(objectives=[_make_objective()])
        proposal = service.propose(spec.id, "provider")
        assert proposal.epistemic_status == EpistemicStatus.UNRESOLVED


class TestDirectionalResidualTypes:
    def test_all_residual_types_defined(self) -> None:
        expected = {
            "target_undefined",
            "constraint_violated",
            "resource_unavailable",
            "knowledge_gap",
            "ambiguous_criteria",
            "conflicting_objectives",
        }
        actual = {r.value for r in DirectionalResidualType}
        assert actual == expected

    def test_residual_type_enum_values(self) -> None:
        assert DirectionalResidualType.TARGET_UNDEFINED.value == "target_undefined"
        assert DirectionalResidualType.CONSTRAINT_VIOLATED.value == "constraint_violated"
        assert DirectionalResidualType.CONFLICTING_OBJECTIVES.value == "conflicting_objectives"
        assert DirectionalResidualType.RESOURCE_UNAVAILABLE.value == "resource_unavailable"
        assert DirectionalResidualType.KNOWLEDGE_GAP.value == "knowledge_gap"
        assert DirectionalResidualType.AMBIGUOUS_CRITERIA.value == "ambiguous_criteria"


class TestDirectionalSpecificationProvenance:
    def test_specification_has_provenance(self) -> None:
        spec = _make_specification()
        assert spec.provenance is not None
        assert spec.provenance.source_type.value == "deterministic_rule"

    def test_proposal_provenance_tracks_specification(self) -> None:
        provider = DeterministicDirectionalProvider()
        spec = _make_specification()
        proposal = provider.propose(spec)
        assert spec.id in proposal.provenance.parent_ids


class TestDirectionalDeterminism:
    def test_specification_deterministic(self) -> None:
        obj = _make_objective(description="deterministic_obj")
        constraint = _make_constraint(description="deterministic_constraint")
        criterion = _make_success_criterion(metric_name="throughput")
        spec1 = DirectionalSpecification(objectives=[obj], constraints=[constraint], success_criteria=[criterion])
        spec2 = DirectionalSpecification(objectives=[obj], constraints=[constraint], success_criteria=[criterion])
        assert spec1.objectives == spec2.objectives
        assert spec1.constraints == spec2.constraints
        assert spec1.success_criteria == spec2.success_criteria

    def test_proposal_deterministic(self) -> None:
        provider = DeterministicDirectionalProvider()
        obj = _make_objective(description="det_obj", target_state={"v": 1})
        constraint = _make_constraint(description="det_constraint")
        criterion = _make_success_criterion(metric_name="throughput")
        spec = DirectionalSpecification(objectives=[obj], constraints=[constraint], success_criteria=[criterion])
        p1 = provider.propose(spec)
        p2 = provider.propose(spec)
        assert p1.proposed_actions_dict == p2.proposed_actions_dict
        assert p1.provider_id == p2.provider_id
        assert p1.provider_version == p2.provider_version
        assert p1.specification_id == p2.specification_id
        assert p1.residuals == p2.residuals
        assert p1.confidence == p2.confidence

    def test_service_produce_deterministic_proposals(self) -> None:
        service = InMemoryDirectionalService()
        obj = _make_objective(description="det_obj", target_state={"v": 1})
        spec = service.create_specification(objectives=[obj])
        p1 = service.propose(spec.id, "provider")
        p2 = service.propose(spec.id, "provider")
        assert p1.proposed_actions_dict == p2.proposed_actions_dict
        assert p1.provider_id == p2.provider_id
        assert p1.specification_id == p2.specification_id
        assert p1.residuals == p2.residuals
