"""Cognitia Directional Programming Provider SPI.

Defines the provider-neutral interface for directional proposal generation
and a deterministic baseline reference implementation.
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol, runtime_checkable

from cognitia.abi.types import generate_entity_id
from cognitia.directional.types import (
    DirectionalConstraint,
    DirectionalObjective,
    DirectionalProposal,
    DirectionalResidual,
    DirectionalResidualType,
    DirectionalSpecification,
    SuccessCriterion,
)
from cognitia.epistemic.types import EpistemicStatus
from cognitia.provenance.record import ProvenanceRecord, SourceType
from cognitia.providers.types import ProposalLifecycleStatus


@runtime_checkable
class DirectionalProvider(Protocol):
    """Protocol for directional programming capability providers."""

    provider_id: str
    provider_version: str

    def propose(
        self,
        specification: DirectionalSpecification,
    ) -> DirectionalProposal: ...


class DeterministicDirectionalProvider:
    """Deterministic baseline directional provider.

    Analyzes a DirectionalSpecification and produces a DirectionalProposal
    with explicit residuals for any unachievable or violated aspects.

    This provider contains no AI/ML/network/filesystem dependencies.
    """

    def __init__(
        self,
        provider_id: str = "deterministic_directional_provider",
        provider_version: str = "1.0.0",
    ) -> None:
        self.provider_id = provider_id
        self.provider_version = provider_version

    def _check_objectives(self, specification: DirectionalSpecification) -> list[DirectionalResidual]:
        residuals: list[DirectionalResidual] = []
        for obj in specification.objectives:
            if not obj.target_state:
                residuals.append(
                    DirectionalResidual(
                        factor_name=obj.description or obj.id,
                        description=f"Objective has no defined target_state: {obj.description}",
                        residual_type=DirectionalResidualType.TARGET_UNDEFINED,
                        target_variable=obj.id,
                    )
                )
            if not obj.metrics:
                residuals.append(
                    DirectionalResidual(
                        factor_name=obj.description or obj.id,
                        description=f"Objective has no success metrics: {obj.description}",
                        residual_type=DirectionalResidualType.AMBIGUOUS_CRITERIA,
                        target_variable=obj.id,
                    )
                )
        return residuals

    def _check_constraints(self, specification: DirectionalSpecification) -> list[DirectionalResidual]:
        residuals: list[DirectionalResidual] = []
        hard_constraints = [c for c in specification.constraints if c.is_hard]
        soft_constraints = [c for c in specification.constraints if not c.is_hard]

        if hard_constraints and soft_constraints:
            for c in soft_constraints:
                residuals.append(
                    DirectionalResidual(
                        factor_name=c.description or c.id,
                        description=(
                            f"Soft constraint may conflict with hard constraints: {c.description}"
                        ),
                        residual_type=DirectionalResidualType.CONFLICTING_OBJECTIVES,
                        target_variable=c.id,
                    )
                )

        if len(specification.objectives) > 1:
            priorities = [o.priority for o in specification.objectives]
            if len(set(priorities)) == 1:
                residuals.append(
                    DirectionalResidual(
                        factor_name="objectives",
                        description="Multiple objectives share identical priority; conflict resolution ambiguous",
                        residual_type=DirectionalResidualType.CONFLICTING_OBJECTIVES,
                        target_variable="objectives",
                    )
                )

        return residuals

    def _check_success_criteria(self, specification: DirectionalSpecification) -> list[DirectionalResidual]:
        residuals: list[DirectionalResidual] = []
        for criterion in specification.success_criteria:
            if not criterion.metric_name:
                residuals.append(
                    DirectionalResidual(
                        factor_name=criterion.description or criterion.id,
                        description="Success criterion has no metric_name",
                        residual_type=DirectionalResidualType.AMBIGUOUS_CRITERIA,
                        target_variable=criterion.id,
                    )
                )
            if criterion.direction not in (">=", "<=", "=="):
                residuals.append(
                    DirectionalResidual(
                        factor_name=criterion.description or criterion.id,
                        description=f"Unknown comparison direction: {criterion.direction}",
                        residual_type=DirectionalResidualType.AMBIGUOUS_CRITERIA,
                        target_variable=criterion.id,
                    )
                )
        return residuals

    def propose(
        self,
        specification: DirectionalSpecification,
    ) -> DirectionalProposal:
        residuals: list[DirectionalResidual] = []
        residuals.extend(self._check_objectives(specification))
        residuals.extend(self._check_constraints(specification))
        residuals.extend(self._check_success_criteria(specification))

        if not specification.objectives:
            residuals.append(
                DirectionalResidual(
                    factor_name="specification",
                    description="Specification contains no objectives",
                    residual_type=DirectionalResidualType.TARGET_UNDEFINED,
                    target_variable="objectives",
                )
            )

        proposed_actions: list[tuple[str, Any]] = []
        for obj in specification.objectives:
            if obj.target_state:
                proposed_actions.append(
                    (
                        "pursue_objective",
                        {
                            "objective_id": obj.id,
                            "target_state": obj.target_state_dict,
                            "priority": obj.priority,
                            "metrics": list(obj.metrics),
                        },
                    )
                )

        for constraint in specification.constraints:
            proposed_actions.append(
                (
                    "enforce_constraint",
                    {
                        "constraint_id": constraint.id,
                        "constraint_type": constraint.constraint_type,
                        "is_hard": constraint.is_hard,
                        "bound": constraint.bound_dict,
                    },
                )
            )

        confidence = 1.0
        if residuals:
            hard_residuals = [r for r in residuals if r.residual_type == DirectionalResidualType.CONSTRAINT_VIOLATED]
            if hard_residuals:
                confidence = 0.0
            else:
                confidence = max(0.0, 1.0 - (len(residuals) * 0.1))

        prov = ProvenanceRecord(
            source_type=SourceType.DETERMINISTIC_RULE,
            producer_id=f"{self.provider_id}:{self.provider_version}",
            parent_ids=[specification.id, specification.provenance.id],
            is_deterministic=True,
        )

        return DirectionalProposal(
            specification_id=specification.id,
            provider_id=self.provider_id,
            provider_version=self.provider_version,
            proposed_actions=proposed_actions,
            residuals=residuals,
            confidence=confidence,
            proposal_status=ProposalLifecycleStatus.PROPOSED,
            epistemic_status=EpistemicStatus.UNRESOLVED,
            provenance=prov,
        )
