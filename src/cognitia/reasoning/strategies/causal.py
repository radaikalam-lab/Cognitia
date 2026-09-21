"""Cognitia Causal Reasoning Strategy.

Implements causal evaluation over explicit causal graphs and mechanisms.
STRICT BOUNDARY:
- Temporal order (A BEFORE B) != Causality.
- Correlation (A CORRELATES_WITH B) != Causality.
- Causality can ONLY be evaluated from explicitly supplied causal graphs, rules, or mechanisms.
"""

from __future__ import annotations

from typing import Any, Sequence

from cognitia.abi.types import (
    CognitiveObject,
    Observation,
    current_utc_timestamp,
    generate_entity_id,
)
from cognitia.epistemic.types import (
    Claim,
    EpistemicStatus,
    Evidence,
    EvidenceDirection,
    Hypothesis,
)
from cognitia.provenance.record import ProvenanceRecord, SourceType
from cognitia.reasoning.types import (
    CausalHypothesis,
    ReasoningInput,
    ReasoningMode,
    ReasoningResidual,
    ReasoningResult,
    ReasoningStep,
    ReasoningTrace,
)
from cognitia.rules.types import CognitiveRule, RuleStatus


def _extract_premise_elements(premises: Sequence[CognitiveObject]) -> tuple[dict[str, Any], list[Evidence]]:
    """Extract observable values and evidence objects from premises."""
    facts: dict[str, Any] = {}
    evidences: list[Evidence] = []
    for p in premises:
        if isinstance(p, Evidence):
            evidences.append(p)
        if isinstance(p, Observation) and isinstance(p.payload, dict):
            facts.update(p.payload)
        if hasattr(p, "metadata") and isinstance(p.metadata, dict):
            facts.update(p.metadata)
    return facts, evidences


class CausalReasoner:
    """Deterministic causal reasoning strategy enforcing strict non-inference from temporal/correlational data."""

    mode: ReasoningMode = ReasoningMode.CAUSAL

    def reason(
        self,
        reasoning_input: ReasoningInput,
    ) -> tuple[ReasoningTrace, ReasoningResult]:
        """Evaluate explicit causal relationships against input evidence and observations."""
        facts, evidences = _extract_premise_elements(reasoning_input.premises)
        steps: list[ReasoningStep] = []
        residuals: list[ReasoningResidual] = []
        contradictions: list[str] = []
        premise_ids = [p.id for p in reasoning_input.premises]

        # 1. Collect explicit causal relationships from causal_graph and causal rules
        causal_edges: list[tuple[str, str, str]] = list(reasoning_input.causal_graph)

        constraints = reasoning_input.constraints_dict
        if "causal_graph" in constraints:
            cg = constraints["causal_graph"]
            if isinstance(cg, (list, tuple)):
                for edge in cg:
                    if isinstance(edge, (list, tuple)) and len(edge) >= 3:
                        causal_edges.append((str(edge[0]), str(edge[1]), str(edge[2])))
                    elif isinstance(edge, dict):
                        causal_edges.append((str(edge.get("cause")), str(edge.get("effect")), str(edge.get("mechanism", "unspecified_mechanism"))))

        for rule in reasoning_input.rules:
            if rule.status == RuleStatus.ACTIVE and (rule.scope == "causal" or rule.metadata.get("is_causal_rule")):
                cause = rule.predicate.get("cause", rule.predicate.get("variable", rule.name))
                effect = rule.recommendation.get("effect", rule.recommendation.get("consequence", "state_change"))
                mechanism = rule.recommendation.get("mechanism", rule.rationale or "explicit_rule_mechanism")
                causal_edges.append((str(cause), str(effect), str(mechanism)))

        steps.append(
            ReasoningStep(
                step_number=1,
                inference_rule="causal_structure_validation",
                input_references=premise_ids,
                intermediate_claim=f"Identified {len(causal_edges)} explicit causal edges in input snapshot",
                confidence=1.0,
            )
        )

        # 2. Strict Guardrail: If NO explicit causal graph is provided
        if not causal_edges:
            guardrail_claim = (
                "No explicit causal graph or mechanism supplied. "
                "Causality CANNOT be inferred from temporal succession or correlation alone."
            )
            steps.append(
                ReasoningStep(
                    step_number=2,
                    inference_rule="causal_guardrail_rejection",
                    input_references=premise_ids,
                    intermediate_claim=guardrail_claim,
                    confidence=1.0,
                )
            )
            residuals.append(
                ReasoningResidual(
                    factor_name="causal_graph",
                    description=guardrail_claim,
                    residual_type="missing_rule",
                )
            )

            trace_prov = ProvenanceRecord(
                source_type=SourceType.REASONING_ENGINE,
                producer_id="deterministic_causal_reasoner",
                parent_ids=[reasoning_input.provenance.id] + premise_ids,
                is_deterministic=True,
            )

            empty_conclusion = CognitiveObject(
                metadata={"status": "rejected_no_causal_structure", "reason": guardrail_claim}
            )

            trace = ReasoningTrace(
                id=generate_entity_id(),
                created_at=current_utc_timestamp(),
                mode=ReasoningMode.CAUSAL,
                premises=list(reasoning_input.premises),
                steps=steps,
                conclusion=empty_conclusion,
                confidence=0.0,
                provider="deterministic_causal_reasoner",
                provenance=trace_prov,
            )

            result = ReasoningResult(
                id=generate_entity_id(),
                created_at=current_utc_timestamp(),
                reasoning_mode=ReasoningMode.CAUSAL,
                reasoning_input_id=reasoning_input.context_id,
                candidate_conclusions=(empty_conclusion,),
                candidate_hypotheses=(),
                residuals=tuple(residuals),
                derivation_metadata=(("guardrail_triggered", "no_causal_graph"),),
                provenance=trace_prov,
            )
            return trace, result

        # 3. Evaluate each explicit causal edge against premises & evidence
        causal_hypotheses: list[CausalHypothesis] = []
        candidate_hypotheses: list[Hypothesis] = []
        step_counter = 2

        # Sort edges deterministically
        causal_edges.sort(key=lambda e: (e[0], e[1], e[2]))

        for cause, effect, mechanism in causal_edges:
            supporting_ids: list[str] = []
            contradictory_ids: list[str] = []

            # Check facts for presence of cause/effect
            cause_present = cause in facts or any(k.startswith(cause) for k in facts)
            effect_present = effect in facts or any(k.startswith(effect) for k in facts)

            for ev in evidences:
                # Check if evidence references this cause or effect
                if ev.target_id in (cause, effect) or ev.metadata.get("target_variable") in (cause, effect):
                    if ev.direction == EvidenceDirection.SUPPORT:
                        supporting_ids.append(ev.id)
                    elif ev.direction == EvidenceDirection.REFUTE:
                        contradictory_ids.append(ev.id)

            if cause_present:
                supporting_ids.extend([p.id for p in reasoning_input.premises if isinstance(p, Observation)])

            status = EpistemicStatus.HYPOTHESIS
            if contradictory_ids and supporting_ids:
                status = EpistemicStatus.UNRESOLVED
                contra_desc = f"Causal link '{cause} -> {effect}' has conflicting evidence (supporting: {len(supporting_ids)}, refuting: {len(contradictory_ids)})"
                contradictions.append(contra_desc)
            elif not cause_present and not supporting_ids:
                residuals.append(
                    ReasoningResidual(
                        factor_name=cause,
                        description=f"Cause variable '{cause}' not observed in current premises",
                        residual_type="missing_observation",
                        target_variable=cause,
                    )
                )

            causal_hyp = CausalHypothesis(
                id=generate_entity_id(),
                created_at=current_utc_timestamp(),
                cause=cause,
                effect=effect,
                mechanism=mechanism,
                supporting_evidence_ids=tuple(sorted(set(supporting_ids))),
                contradictory_evidence_ids=tuple(sorted(set(contradictory_ids))),
                status=status,
                assumptions=(
                    "Causal mechanism operates under unperturbed domain conditions.",
                    "No unobserved confounders completely override the declared mechanism.",
                ),
                limitations=(
                    "Causal hypothesis is an advisory cognitive model, not a physical certainty.",
                    "Downstream epistemic confirmation is required.",
                ),
                residuals=tuple(residuals),
            )
            causal_hypotheses.append(causal_hyp)

            # Epistemic candidate hypothesis
            stmt = f"Causal hypothesis: '{cause}' causes '{effect}' via mechanism '{mechanism}'"
            candidate_hypotheses.append(
                Hypothesis(
                    id=generate_entity_id(),
                    created_at=current_utc_timestamp(),
                    statement=stmt,
                    test_criteria=[
                        f"Controlled intervention on '{cause}'",
                        f"Observe corresponding response in '{effect}'",
                    ],
                    initial_status=status,
                    provenance=ProvenanceRecord(
                        source_type=SourceType.REASONING_ENGINE,
                        producer_id="causal_reasoner",
                        parent_ids=premise_ids,
                        is_deterministic=True,
                    ),
                )
            )

            steps.append(
                ReasoningStep(
                    step_number=step_counter,
                    inference_rule=f"causal_mechanism_evaluation:{cause}->{effect}",
                    input_references=premise_ids,
                    intermediate_claim=f"Evaluated causal link '{cause} -> {effect}' via '{mechanism}' (status: {status.value})",
                    confidence=1.0 if not contradictory_ids else 0.5,
                )
            )
            step_counter += 1

        primary_conclusion = causal_hypotheses[0] if causal_hypotheses else CognitiveObject()

        trace_prov = ProvenanceRecord(
            source_type=SourceType.REASONING_ENGINE,
            producer_id="deterministic_causal_reasoner",
            parent_ids=[reasoning_input.provenance.id] + premise_ids,
            is_deterministic=True,
        )

        trace = ReasoningTrace(
            id=generate_entity_id(),
            created_at=current_utc_timestamp(),
            mode=ReasoningMode.CAUSAL,
            premises=list(reasoning_input.premises),
            steps=steps,
            conclusion=primary_conclusion,
            confidence=1.0 if not contradictions else 0.5,
            provider="deterministic_causal_reasoner",
            provenance=trace_prov,
        )

        result = ReasoningResult(
            id=generate_entity_id(),
            created_at=current_utc_timestamp(),
            reasoning_mode=ReasoningMode.CAUSAL,
            reasoning_input_id=reasoning_input.context_id,
            candidate_conclusions=tuple(causal_hypotheses),
            candidate_hypotheses=tuple(candidate_hypotheses),
            residuals=tuple(residuals),
            contradictions_detected=tuple(contradictions),
            derivation_metadata=(
                ("causal_edges_count", len(causal_edges)),
                ("contradictions_count", len(contradictions)),
            ),
            provenance=trace_prov,
        )

        return trace, result
