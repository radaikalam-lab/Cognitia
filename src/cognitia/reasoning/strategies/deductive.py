"""Cognitia Deductive Reasoning Strategy.

Implements deterministic rule-based deduction:
Premises + Rules -> Derived Candidate Conclusions.
Captures explicit step-by-step derivations, matched/unsatisfied conditions, and missing premise residuals.
"""

from __future__ import annotations

from typing import Any, Sequence

from cognitia.abi.types import (
    CognitiveObject,
    Observation,
    current_utc_timestamp,
    generate_entity_id,
)
from cognitia.epistemic.types import Claim, EpistemicStatus
from cognitia.provenance.record import ProvenanceRecord, SourceType
from cognitia.reasoning.types import (
    DeductiveConclusion,
    ReasoningInput,
    ReasoningMode,
    ReasoningResidual,
    ReasoningResult,
    ReasoningStep,
    ReasoningTrace,
)
from cognitia.rules.types import CognitiveRule, RuleStatus


def _extract_premise_facts(premises: Sequence[CognitiveObject]) -> dict[str, Any]:
    """Aggregate all observable attributes across premises into a unified fact dictionary."""
    facts: dict[str, Any] = {}
    for p in premises:
        if isinstance(p, Observation) and isinstance(p.payload, dict):
            facts.update(p.payload)
        if hasattr(p, "metadata") and isinstance(p.metadata, dict):
            facts.update(p.metadata)
        if isinstance(p, Claim):
            facts[f"claim_{p.id}"] = p.statement
            facts[f"claim_status_{p.id}"] = p.status.value
    return facts


def _evaluate_condition(expected: Any, actual: Any) -> bool:
    """Evaluate condition predicate against actual value deterministically."""
    if isinstance(expected, dict):
        # Comparison operator dict
        for op, target in expected.items():
            if op == ">":
                if not (actual > target):
                    return False
            elif op == ">=":
                if not (actual >= target):
                    return False
            elif op == "<":
                if not (actual < target):
                    return False
            elif op == "<=":
                if not (actual <= target):
                    return False
            elif op in ("==", "eq"):
                if actual != target:
                    return False
            elif op in ("!=", "neq"):
                if actual == target:
                    return False
            elif op in ("in", "contains"):
                if actual not in target:
                    return False
            elif op in ("within", "between"):
                if isinstance(target, (list, tuple)) and len(target) == 2:
                    if not (target[0] <= actual <= target[1]):
                        return False
            elif op == "prefix":
                if not str(actual).startswith(str(target)):
                    return False
            else:
                if actual != target:
                    return False
        return True
    return bool(actual == expected)


class DeductiveReasoner:
    """Deterministic deductive reasoning strategy."""

    mode: ReasoningMode = ReasoningMode.DEDUCTION

    def reason(
        self,
        reasoning_input: ReasoningInput,
    ) -> tuple[ReasoningTrace, ReasoningResult]:
        """Perform deterministic rule-based deduction over the input snapshot."""
        facts = _extract_premise_facts(reasoning_input.premises)
        steps: list[ReasoningStep] = []
        matched_rule_ids: list[str] = []
        satisfied_conditions: list[str] = []
        unsatisfied_conditions: list[str] = []
        residuals: list[ReasoningResidual] = []
        derived_attributes: dict[str, Any] = {}
        candidate_claims: list[Claim] = []

        # 1. Record input premise analysis step
        premise_ids = [p.id for p in reasoning_input.premises]
        steps.append(
            ReasoningStep(
                step_number=1,
                inference_rule="premise_extraction",
                input_references=premise_ids,
                intermediate_claim=f"Extracted {len(facts)} observable attributes across {len(reasoning_input.premises)} premises",
                confidence=1.0,
            )
        )

        step_counter = 2
        # 2. Evaluate active rules deterministically
        for rule in reasoning_input.rules:
            if rule.status != RuleStatus.ACTIVE:
                continue

            rule_matched = True
            rule_satisfied: list[str] = []
            rule_unsatisfied: list[str] = []

            for field_name, expected_val in rule.predicate.items():
                if field_name not in facts:
                    rule_matched = False
                    unsatisfied_desc = f"Rule '{rule.name}': Missing required variable '{field_name}' in premises"
                    rule_unsatisfied.append(unsatisfied_desc)
                    unsatisfied_conditions.append(unsatisfied_desc)
                    residuals.append(
                        ReasoningResidual(
                            factor_name=field_name,
                            description=unsatisfied_desc,
                            residual_type="missing_observation",
                            target_variable=field_name,
                        )
                    )
                else:
                    actual_val = facts[field_name]
                    is_match = _evaluate_condition(expected_val, actual_val)
                    if is_match:
                        sat_desc = f"Rule '{rule.name}': Condition '{field_name}' satisfied ({actual_val} matches {expected_val})"
                        rule_satisfied.append(sat_desc)
                        satisfied_conditions.append(sat_desc)
                    else:
                        rule_matched = False
                        unsat_desc = f"Rule '{rule.name}': Condition '{field_name}' not satisfied ({actual_val} vs {expected_val})"
                        rule_unsatisfied.append(unsat_desc)
                        unsatisfied_conditions.append(unsat_desc)

            if rule_matched and rule.predicate:
                matched_rule_ids.append(rule.rule_id)
                steps.append(
                    ReasoningStep(
                        step_number=step_counter,
                        inference_rule=f"rule_evaluation:{rule.rule_id}",
                        input_references=[rule.id] + premise_ids,
                        intermediate_claim=f"Rule '{rule.name}' matched with all {len(rule.predicate)} conditions satisfied",
                        confidence=rule.confidence,
                    )
                )
                step_counter += 1

                # Apply rule recommendations
                for k, v in rule.recommendation.items():
                    derived_attributes[k] = v

                # Formulate candidate claim
                claim_stmt = f"Rule '{rule.name}' derived {rule.recommendation}"
                candidate_claims.append(
                    Claim(
                        id=generate_entity_id(),
                        statement=claim_stmt,
                        confidence=rule.confidence,
                        status=EpistemicStatus.HYPOTHESIS,
                        provenance=ProvenanceRecord(
                            source_type=SourceType.REASONING_ENGINE,
                            producer_id="deductive_reasoner",
                            parent_ids=[rule.id] + premise_ids,
                            is_deterministic=True,
                        ),
                    )
                )

        # If no rules evaluated or matched
        if not matched_rule_ids:
            steps.append(
                ReasoningStep(
                    step_number=step_counter,
                    inference_rule="deductive_closure",
                    input_references=premise_ids,
                    intermediate_claim="No active deductive rules satisfied by current premises",
                    confidence=1.0,
                )
            )

        # Build DeductiveConclusion
        conclusion = DeductiveConclusion(
            id=generate_entity_id(),
            created_at=current_utc_timestamp(),
            derived_attributes=tuple(sorted(derived_attributes.items())),
            matched_rule_ids=tuple(matched_rule_ids),
            satisfied_conditions=tuple(satisfied_conditions),
            unsatisfied_conditions=tuple(unsatisfied_conditions),
            residuals=tuple(residuals),
        )

        trace_prov = ProvenanceRecord(
            source_type=SourceType.REASONING_ENGINE,
            producer_id="deterministic_deductive_reasoner",
            parent_ids=[reasoning_input.provenance.id] + premise_ids + [r.id for r in reasoning_input.rules],
            is_deterministic=True,
        )

        trace = ReasoningTrace(
            id=generate_entity_id(),
            created_at=current_utc_timestamp(),
            mode=ReasoningMode.DEDUCTION,
            premises=list(reasoning_input.premises),
            steps=steps,
            conclusion=conclusion,
            confidence=1.0 if matched_rule_ids else (0.5 if not residuals else 0.0),
            provider="deterministic_deductive_reasoner",
            provenance=trace_prov,
        )

        result = ReasoningResult(
            id=generate_entity_id(),
            created_at=current_utc_timestamp(),
            reasoning_mode=ReasoningMode.DEDUCTION,
            reasoning_input_id=reasoning_input.context_id,
            candidate_conclusions=(conclusion,),
            candidate_claims=tuple(candidate_claims),
            residuals=tuple(residuals),
            derivation_metadata=(
                ("matched_rules_count", len(matched_rule_ids)),
                ("satisfied_conditions_count", len(satisfied_conditions)),
                ("unsatisfied_conditions_count", len(unsatisfied_conditions)),
            ),
            provenance=trace_prov,
        )

        return trace, result
