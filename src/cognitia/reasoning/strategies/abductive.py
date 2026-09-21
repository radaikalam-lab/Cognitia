"""Cognitia Abductive Reasoning Strategy.

Implements deterministic candidate-explanation generation:
Observations / Symptoms -> Candidate Hypotheses.
Generates competing explanatory hypotheses without asserting truth or fabricating probabilities.
"""

from __future__ import annotations

from typing import Any, Sequence

from cognitia.abi.types import (
    CognitiveObject,
    Observation,
    current_utc_timestamp,
    generate_entity_id,
)
from cognitia.epistemic.types import EpistemicStatus, Hypothesis
from cognitia.provenance.record import ProvenanceRecord, SourceType
from cognitia.reasoning.types import (
    AbductiveHypotheses,
    ReasoningInput,
    ReasoningMode,
    ReasoningResidual,
    ReasoningResult,
    ReasoningStep,
    ReasoningTrace,
)
from cognitia.rules.types import CognitiveRule, RuleStatus


def _extract_observed_keys_and_values(premises: Sequence[CognitiveObject]) -> dict[str, Any]:
    """Aggregate all observable attributes across premises."""
    facts: dict[str, Any] = {}
    for p in premises:
        if isinstance(p, Observation) and isinstance(p.payload, dict):
            facts.update(p.payload)
        if hasattr(p, "metadata") and isinstance(p.metadata, dict):
            facts.update(p.metadata)
    return facts


class AbductiveReasoner:
    """Deterministic abductive reasoning strategy."""

    mode: ReasoningMode = ReasoningMode.ABDUCTION

    def reason(
        self,
        reasoning_input: ReasoningInput,
    ) -> tuple[ReasoningTrace, ReasoningResult]:
        """Generate candidate explanatory hypotheses for observed premises."""
        facts = _extract_observed_keys_and_values(reasoning_input.premises)
        steps: list[ReasoningStep] = []
        residuals: list[ReasoningResidual] = []
        premise_ids = [p.id for p in reasoning_input.premises]

        steps.append(
            ReasoningStep(
                step_number=1,
                inference_rule="symptom_extraction",
                input_references=premise_ids,
                intermediate_claim=f"Identified {len(facts)} observable symptoms/attributes from premises",
                confidence=1.0,
            )
        )

        # Collect candidate explanation definitions from rules and constraints
        # 1. From rules
        raw_candidates: list[dict[str, Any]] = []
        for rule in reasoning_input.rules:
            if rule.status != RuleStatus.ACTIVE:
                continue
            # Check if rule is an explanatory/abductive rule
            is_abductive = (
                rule.scope in ("abductive", "diagnostic", "explanation")
                or "hypothesis" in rule.recommendation
                or "explanation" in rule.recommendation
                or "cause" in rule.recommendation
            )
            if is_abductive:
                hyp_statement = (
                    rule.recommendation.get("hypothesis")
                    or rule.recommendation.get("explanation")
                    or rule.recommendation.get("cause")
                    or rule.description
                    or rule.name
                )
                test_criteria = rule.recommendation.get("test_criteria", [])
                if isinstance(test_criteria, str):
                    test_criteria = [test_criteria]
                raw_candidates.append({
                    "id": rule.rule_id,
                    "statement": str(hyp_statement),
                    "required_symptoms": rule.predicate,
                    "test_criteria": list(test_criteria),
                    "source_rule_id": rule.id,
                })

        # 2. From constraints / parameters
        constraints = reasoning_input.constraints_dict
        if "explanatory_candidates" in constraints and isinstance(constraints["explanatory_candidates"], (list, tuple)):
            for idx, cand in enumerate(constraints["explanatory_candidates"]):
                if isinstance(cand, dict):
                    raw_candidates.append({
                        "id": cand.get("id", f"cand_{idx}"),
                        "statement": cand.get("statement", cand.get("hypothesis", "Unknown explanation")),
                        "required_symptoms": cand.get("symptoms", {}),
                        "test_criteria": cand.get("test_criteria", []),
                        "source_rule_id": None,
                    })

        # Evaluate each candidate against observed facts
        evaluated_candidates: list[tuple[int, str, dict[str, Any], list[str], list[str]]] = []
        for cand in raw_candidates:
            req_symptoms = cand["required_symptoms"]
            matched_symptoms: list[str] = []
            unmatched_symptoms: list[str] = []

            if isinstance(req_symptoms, dict):
                for k, v in req_symptoms.items():
                    if k in facts:
                        # Check match
                        if facts[k] == v or (isinstance(v, dict) and any(facts[k] > v.get(">", float("-inf")) for _ in [1])):
                            matched_symptoms.append(k)
                        else:
                            unmatched_symptoms.append(k)
                    else:
                        unmatched_symptoms.append(k)
            elif isinstance(req_symptoms, (list, tuple)):
                for k in req_symptoms:
                    if k in facts:
                        matched_symptoms.append(str(k))
                    else:
                        unmatched_symptoms.append(str(k))

            # Only consider candidate if at least one symptom matches or if req_symptoms is empty/wildcard
            if matched_symptoms or not req_symptoms:
                score = len(matched_symptoms)
                evaluated_candidates.append((score, cand["id"], cand, matched_symptoms, unmatched_symptoms))

        # Sort deterministically: (-matched_symptoms_count, candidate_id ASC)
        evaluated_candidates.sort(key=lambda x: (-x[0], x[1]))

        # Generate Hypothesis objects
        candidate_hypotheses: list[Hypothesis] = []
        explanation_bases: list[tuple[str, str]] = []
        all_hyp_ids = [generate_entity_id() for _ in evaluated_candidates]

        step_counter = 2
        for idx, (score, cand_id, cand_dict, matched_syms, unmatched_syms) in enumerate(evaluated_candidates):
            hyp_id = all_hyp_ids[idx]
            competing_ids = [hid for hid in all_hyp_ids if hid != hyp_id]

            parent_ids = premise_ids[:]
            if cand_dict.get("source_rule_id"):
                parent_ids.append(cand_dict["source_rule_id"])

            hyp = Hypothesis(
                id=hyp_id,
                created_at=current_utc_timestamp(),
                statement=cand_dict["statement"],
                test_criteria=cand_dict["test_criteria"],
                competing_hypothesis_ids=competing_ids,
                initial_status=EpistemicStatus.HYPOTHESIS,
                provenance=ProvenanceRecord(
                    source_type=SourceType.REASONING_ENGINE,
                    producer_id="abductive_reasoner",
                    parent_ids=parent_ids,
                    is_deterministic=True,
                ),
            )
            candidate_hypotheses.append(hyp)

            basis_desc = f"Explains {len(matched_syms)} observed symptoms: {', '.join(matched_syms)}"
            explanation_bases.append((hyp_id, basis_desc))

            steps.append(
                ReasoningStep(
                    step_number=step_counter,
                    inference_rule=f"abductive_hypothesis_generation:{cand_id}",
                    input_references=parent_ids,
                    intermediate_claim=f"Formulated candidate hypothesis: '{hyp.statement}' ({basis_desc})",
                    confidence=1.0,
                )
            )
            step_counter += 1

            # Note missing expected symptoms as residuals
            for unsat in unmatched_syms:
                residuals.append(
                    ReasoningResidual(
                        factor_name=unsat,
                        description=f"Expected symptom '{unsat}' for hypothesis '{hyp.statement}' was not observed",
                        residual_type="missing_observation",
                        target_variable=unsat,
                    )
                )

        if not evaluated_candidates:
            steps.append(
                ReasoningStep(
                    step_number=step_counter,
                    inference_rule="abductive_residual_recording",
                    input_references=premise_ids,
                    intermediate_claim="No candidate explanatory hypotheses matched observed symptoms",
                    confidence=1.0,
                )
            )
            residuals.append(
                ReasoningResidual(
                    factor_name="unexplained_phenomenon",
                    description="No known explanatory rule or candidate structure matches observed premises",
                    residual_type="unmodeled_dynamic",
                )
            )

        abductive_outcome = AbductiveHypotheses(
            id=generate_entity_id(),
            created_at=current_utc_timestamp(),
            candidate_hypotheses=tuple(candidate_hypotheses),
            explanation_bases=tuple(explanation_bases),
            unexplained_observations=tuple(k for k in facts.keys()),
            residuals=tuple(residuals),
        )

        trace_prov = ProvenanceRecord(
            source_type=SourceType.REASONING_ENGINE,
            producer_id="deterministic_abductive_reasoner",
            parent_ids=[reasoning_input.provenance.id] + premise_ids,
            is_deterministic=True,
        )

        trace = ReasoningTrace(
            id=generate_entity_id(),
            created_at=current_utc_timestamp(),
            mode=ReasoningMode.ABDUCTION,
            premises=list(reasoning_input.premises),
            steps=steps,
            conclusion=abductive_outcome,
            confidence=1.0 if candidate_hypotheses else 0.0,
            provider="deterministic_abductive_reasoner",
            provenance=trace_prov,
        )

        result = ReasoningResult(
            id=generate_entity_id(),
            created_at=current_utc_timestamp(),
            reasoning_mode=ReasoningMode.ABDUCTION,
            reasoning_input_id=reasoning_input.context_id,
            candidate_conclusions=(abductive_outcome,),
            candidate_hypotheses=tuple(candidate_hypotheses),
            residuals=tuple(residuals),
            derivation_metadata=(
                ("candidate_hypotheses_count", len(candidate_hypotheses)),
                ("unexplained_symptoms_count", len(facts)),
            ),
            provenance=trace_prov,
        )

        return trace, result
