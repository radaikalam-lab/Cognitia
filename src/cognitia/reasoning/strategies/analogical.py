"""Cognitia Analogical Reasoning Strategy.

Implements structural analogy:
Source Pattern Structure + Target Context -> Analogical Correspondences.
Strict semantic boundary: Structural similarity != Semantic equivalence.
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
    AnalogicalMapping,
    ReasoningInput,
    ReasoningMode,
    ReasoningResidual,
    ReasoningResult,
    ReasoningStep,
    ReasoningTrace,
)


def _extract_target_structure(premises: Sequence[CognitiveObject]) -> dict[str, Any]:
    """Extract structural elements, entities, and attributes from target premises."""
    target_elements: dict[str, Any] = {}
    for p in premises:
        if isinstance(p, Observation):
            target_elements[f"obs_{p.source_id}"] = p.payload
            for k, v in p.payload.items():
                target_elements[k] = v
        if hasattr(p, "metadata") and isinstance(p.metadata, dict):
            target_elements.update(p.metadata)
    return target_elements


class AnalogicalReasoner:
    """Deterministic structural analogical reasoning strategy."""

    mode: ReasoningMode = ReasoningMode.ANALOGY

    def reason(
        self,
        reasoning_input: ReasoningInput,
    ) -> tuple[ReasoningTrace, ReasoningResult]:
        """Perform structural mapping between source pattern and target context."""
        target_facts = _extract_target_structure(reasoning_input.premises)
        steps: list[ReasoningStep] = []
        residuals: list[ReasoningResidual] = []
        premise_ids = [p.id for p in reasoning_input.premises]

        source_data = reasoning_input.analogy_source_dict
        if not source_data and "analogy_source" in reasoning_input.constraints_dict:
            src_val = reasoning_input.constraints_dict["analogy_source"]
            if isinstance(src_val, dict):
                source_data = src_val

        source_id = str(source_data.get("source_id", "source_pattern_ref"))
        source_elements = source_data.get("elements", {})
        if isinstance(source_elements, (list, tuple)):
            source_elements = {str(elem): elem for elem in source_elements}

        source_relations = source_data.get("relations", [])
        similarity_basis = str(source_data.get("basis", "structural_topology_and_sequence_alignment"))

        steps.append(
            ReasoningStep(
                step_number=1,
                inference_rule="source_structure_parsing",
                input_references=premise_ids,
                intermediate_claim=f"Parsed source pattern '{source_id}' with {len(source_elements)} elements",
                confidence=1.0,
            )
        )

        correspondences: list[tuple[str, str]] = []
        unmapped_source: list[str] = []

        # Map source elements to target facts based on key names or explicit correspondence hints
        explicit_mapping = source_data.get("mapping_hints", {})
        for src_key, src_type in source_elements.items():
            if src_key in explicit_mapping and explicit_mapping[src_key] in target_facts:
                correspondences.append((src_key, str(explicit_mapping[src_key])))
            elif src_key in target_facts:
                correspondences.append((src_key, src_key))
            else:
                # Fuzzy match by type or name substring
                matched_target = None
                for tgt_key in target_facts.keys():
                    if src_key.lower() in tgt_key.lower() or tgt_key.lower() in src_key.lower():
                        matched_target = tgt_key
                        break
                if matched_target:
                    correspondences.append((src_key, matched_target))
                else:
                    unmapped_source.append(src_key)
                    residuals.append(
                        ReasoningResidual(
                            factor_name=src_key,
                            description=f"Source element '{src_key}' has no corresponding structural counterpart in target context",
                            residual_type="unmodeled_dynamic",
                        )
                    )

        # Sort correspondences deterministically
        correspondences.sort(key=lambda x: (x[0], x[1]))

        total_source_count = max(len(source_elements), 1)
        sim_score = round(len(correspondences) / total_source_count, 4)

        steps.append(
            ReasoningStep(
                step_number=2,
                inference_rule="structural_correspondence_mapping",
                input_references=premise_ids,
                intermediate_claim=f"Established {len(correspondences)}/{len(source_elements)} structural correspondences (similarity: {sim_score})",
                confidence=sim_score,
            )
        )

        known_limitations = (
            "Structural analogy indicates topological/pattern alignment, NOT physical or semantic equivalence.",
            "Domain-specific physical laws, scale factors, and actuator constraints are not transferred by analogy.",
            f"Unmapped source elements: {', '.join(unmapped_source) if unmapped_source else 'None'}",
        )

        # Build candidate claim
        candidate_claims: list[Claim] = []
        if correspondences:
            claim_stmt = f"Target context is structurally analogous to pattern '{source_id}' with similarity {sim_score}"
            candidate_claims.append(
                Claim(
                    id=generate_entity_id(),
                    statement=claim_stmt,
                    confidence=sim_score,
                    status=EpistemicStatus.HYPOTHESIS,
                    provenance=ProvenanceRecord(
                        source_type=SourceType.REASONING_ENGINE,
                        producer_id="analogical_reasoner",
                        parent_ids=premise_ids,
                        is_deterministic=True,
                    ),
                )
            )

        mapping_outcome = AnalogicalMapping(
            id=generate_entity_id(),
            created_at=current_utc_timestamp(),
            source_structure_id=source_id,
            target_structure_id=reasoning_input.context_id,
            correspondences=tuple(correspondences),
            structural_basis=similarity_basis,
            similarity_score=sim_score,
            known_limitations=known_limitations,
            is_equivalent=False,  # Invariant: Structural similarity != Semantic equivalence
            residuals=tuple(residuals),
        )

        trace_prov = ProvenanceRecord(
            source_type=SourceType.REASONING_ENGINE,
            producer_id="deterministic_analogical_reasoner",
            parent_ids=[reasoning_input.provenance.id] + premise_ids,
            is_deterministic=True,
        )

        trace = ReasoningTrace(
            id=generate_entity_id(),
            created_at=current_utc_timestamp(),
            mode=ReasoningMode.ANALOGY,
            premises=list(reasoning_input.premises),
            steps=steps,
            conclusion=mapping_outcome,
            confidence=sim_score,
            provider="deterministic_analogical_reasoner",
            provenance=trace_prov,
        )

        result = ReasoningResult(
            id=generate_entity_id(),
            created_at=current_utc_timestamp(),
            reasoning_mode=ReasoningMode.ANALOGY,
            reasoning_input_id=reasoning_input.context_id,
            candidate_conclusions=(mapping_outcome,),
            candidate_claims=tuple(candidate_claims),
            residuals=tuple(residuals),
            derivation_metadata=(
                ("source_id", source_id),
                ("similarity_score", sim_score),
                ("correspondences_count", len(correspondences)),
                ("unmapped_elements_count", len(unmapped_source)),
            ),
            provenance=trace_prov,
        )

        return trace, result
