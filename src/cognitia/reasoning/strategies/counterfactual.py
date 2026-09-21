"""Cognitia Counterfactual Reasoning Strategy.

Implements constrained hypothetical scenario evaluation:
Baseline State + Explicit Intervention + Explicit Transition Rules -> Derived Scenario.
MANDATORY BOUNDARY:
- Counterfactual != Observation.
- Missing transition rules create explicit residuals instead of manufactured extrapolations.
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
    CounterfactualScenario,
    ReasoningInput,
    ReasoningMode,
    ReasoningResidual,
    ReasoningResult,
    ReasoningStep,
    ReasoningTrace,
)
from cognitia.rules.types import CognitiveRule, RuleStatus


def _extract_baseline_facts(premises: Sequence[CognitiveObject]) -> dict[str, Any]:
    """Aggregate observable attributes from premises into a baseline state map."""
    baseline: dict[str, Any] = {}
    for p in premises:
        if isinstance(p, Observation) and isinstance(p.payload, dict):
            baseline.update(p.payload)
        if hasattr(p, "metadata") and isinstance(p.metadata, dict):
            baseline.update(p.metadata)
    return baseline


class CounterfactualReasoner:
    """Deterministic counterfactual reasoning strategy."""

    mode: ReasoningMode = ReasoningMode.COUNTERFACTUAL

    def reason(
        self,
        reasoning_input: ReasoningInput,
    ) -> tuple[ReasoningTrace, ReasoningResult]:
        """Compute hypothetical state outcome under explicit interventions."""
        baseline_state = _extract_baseline_facts(reasoning_input.premises)
        steps: list[ReasoningStep] = []
        residuals: list[ReasoningResidual] = []
        derivation_steps: list[str] = []
        premise_ids = [p.id for p in reasoning_input.premises]

        # 1. Extract interventions
        interventions = dict(reasoning_input.hypothetical_interventions_dict)
        if not interventions and "interventions" in reasoning_input.constraints_dict:
            inv_val = reasoning_input.constraints_dict["interventions"]
            if isinstance(inv_val, dict):
                interventions.update(inv_val)

        steps.append(
            ReasoningStep(
                step_number=1,
                inference_rule="baseline_state_capture",
                input_references=premise_ids,
                intermediate_claim=f"Captured baseline state with {len(baseline_state)} observed variables",
                confidence=1.0,
            )
        )

        steps.append(
            ReasoningStep(
                step_number=2,
                inference_rule="intervention_application",
                input_references=premise_ids,
                intermediate_claim=f"Applied {len(interventions)} hypothetical interventions: {interventions}",
                confidence=1.0,
            )
        )

        # 2. Extract explicit transition rules / dynamics
        transition_rules: list[dict[str, Any]] = []
        constraints = reasoning_input.constraints_dict
        if "transition_rules" in constraints and isinstance(constraints["transition_rules"], (list, tuple)):
            for tr in constraints["transition_rules"]:
                if isinstance(tr, dict):
                    transition_rules.append(tr)

        for rule in reasoning_input.rules:
            if rule.status == RuleStatus.ACTIVE and (rule.scope == "counterfactual" or rule.metadata.get("is_transition_rule")):
                transition_rules.append({
                    "id": rule.rule_id,
                    "target_variable": rule.recommendation.get("target_variable", rule.name),
                    "condition": rule.predicate,
                    "formula": rule.recommendation.get("formula"),
                    "value": rule.recommendation.get("value"),
                    "delta": rule.recommendation.get("delta"),
                })

        # 3. Derive hypothetical state
        derived_state: dict[str, Any] = dict(baseline_state)
        # Apply intervention overrides
        for var_name, inv_val in interventions.items():
            derived_state[var_name] = inv_val
            step_desc = f"Intervention: '{var_name}' set to {inv_val} (was {baseline_state.get(var_name, 'unobserved')})"
            derivation_steps.append(step_desc)

        # Apply transition rules
        step_counter = 3
        applied_transition_targets: set[str] = set()

        for tr in transition_rules:
            target_var = tr.get("target_variable")
            if not target_var:
                continue

            # Check condition if present
            cond = tr.get("condition", {})
            cond_satisfied = True
            if isinstance(cond, dict):
                for ck, cv in cond.items():
                    if ck not in derived_state:
                        cond_satisfied = False
                        break
                    if isinstance(cv, dict):
                        for op, op_val in cv.items():
                            if op == ">" and not (derived_state[ck] > op_val):
                                cond_satisfied = False
                            elif op == "<" and not (derived_state[ck] < op_val):
                                cond_satisfied = False
                            elif op == "==" and not (derived_state[ck] == op_val):
                                cond_satisfied = False
                    elif derived_state[ck] != cv:
                        cond_satisfied = False
                        break

            if cond_satisfied:
                if "value" in tr and tr["value"] is not None:
                    derived_state[target_var] = tr["value"]
                    applied_transition_targets.add(target_var)
                    d_step = f"Transition Rule '{tr.get('id', target_var)}': derived '{target_var}' = {tr['value']}"
                    derivation_steps.append(d_step)
                    steps.append(
                        ReasoningStep(
                            step_number=step_counter,
                            inference_rule=f"transition_rule:{tr.get('id', target_var)}",
                            input_references=premise_ids,
                            intermediate_claim=d_step,
                            confidence=1.0,
                        )
                    )
                    step_counter += 1
                elif "delta" in tr and tr["delta"] is not None and target_var in baseline_state:
                    base_val = baseline_state[target_var]
                    if isinstance(base_val, (int, float)):
                        new_val = base_val + tr["delta"]
                        derived_state[target_var] = new_val
                        applied_transition_targets.add(target_var)
                        d_step = f"Transition Rule '{tr.get('id', target_var)}': derived '{target_var}' = {new_val} (delta {tr['delta']})"
                        derivation_steps.append(d_step)
                        steps.append(
                            ReasoningStep(
                                step_number=step_counter,
                                inference_rule=f"transition_rule_delta:{tr.get('id', target_var)}",
                                input_references=premise_ids,
                                intermediate_claim=d_step,
                                confidence=1.0,
                            )
                        )
                        step_counter += 1

        # Check for requested downstream targets without transition rules
        requested_targets = constraints.get("requested_downstream_variables", [])
        if isinstance(requested_targets, (list, tuple)):
            for req_var in requested_targets:
                if req_var not in interventions and req_var not in applied_transition_targets:
                    residual_desc = f"Explicit transition rule unavailable for downstream variable '{req_var}'. No extrapolation performed."
                    residuals.append(
                        ReasoningResidual(
                            factor_name=req_var,
                            description=residual_desc,
                            residual_type="missing_rule",
                            target_variable=req_var,
                        )
                    )
                    derivation_steps.append(f"Residual: {residual_desc}")

        assumptions = (
            "Hypothetical scenario holds all non-intervened exogenous variables constant.",
            "Deterministic transition rules accurately model specified hypothetical dynamics.",
        )
        limitations = (
            "Counterfactual scenario is NOT an empirical observation.",
            "Results cannot be treated as observed data for domain actuation without empirical verification.",
        )

        scenario = CounterfactualScenario(
            id=generate_entity_id(),
            created_at=current_utc_timestamp(),
            baseline_state=tuple(sorted(baseline_state.items())),
            intervention=tuple(sorted(interventions.items())),
            derived_state=tuple(sorted(derived_state.items())),
            derivation_steps=tuple(derivation_steps),
            is_observed=False,  # Invariant: Counterfactual != Observation
            is_hypothetical=True,
            assumptions=assumptions,
            limitations=limitations,
            residuals=tuple(residuals),
        )

        # Candidate claim
        candidate_claims: list[Claim] = []
        claim_stmt = f"Counterfactual scenario derived with {len(derived_state)} state variables under intervention {interventions}"
        candidate_claims.append(
            Claim(
                id=generate_entity_id(),
                statement=claim_stmt,
                confidence=1.0 if not residuals else 0.5,
                status=EpistemicStatus.HYPOTHESIS,
                provenance=ProvenanceRecord(
                    source_type=SourceType.REASONING_ENGINE,
                    producer_id="counterfactual_reasoner",
                    parent_ids=premise_ids,
                    is_deterministic=True,
                ),
            )
        )

        trace_prov = ProvenanceRecord(
            source_type=SourceType.REASONING_ENGINE,
            producer_id="deterministic_counterfactual_reasoner",
            parent_ids=[reasoning_input.provenance.id] + premise_ids,
            is_deterministic=True,
        )

        trace = ReasoningTrace(
            id=generate_entity_id(),
            created_at=current_utc_timestamp(),
            mode=ReasoningMode.COUNTERFACTUAL,
            premises=list(reasoning_input.premises),
            steps=steps,
            conclusion=scenario,
            confidence=1.0 if not residuals else 0.5,
            provider="deterministic_counterfactual_reasoner",
            provenance=trace_prov,
        )

        result = ReasoningResult(
            id=generate_entity_id(),
            created_at=current_utc_timestamp(),
            reasoning_mode=ReasoningMode.COUNTERFACTUAL,
            reasoning_input_id=reasoning_input.context_id,
            candidate_conclusions=(scenario,),
            candidate_claims=tuple(candidate_claims),
            residuals=tuple(residuals),
            derivation_metadata=(
                ("interventions_count", len(interventions)),
                ("applied_transitions_count", len(applied_transition_targets)),
                ("residuals_count", len(residuals)),
            ),
            provenance=trace_prov,
        )

        return trace, result
