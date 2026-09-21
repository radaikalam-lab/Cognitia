"""Cognitia Context Assembler Engine and SPI.

Orchestrates multi-dimensional situational cognitive context assembly and enrichment
from Persistence, Memory, Cognitive Rules, and Epistemic structures deterministically.
Delegates structural transformations to modular enrichers without monolithic coupling.
"""

from __future__ import annotations

import datetime
from typing import Any, Protocol, runtime_checkable

from cognitia.abi.types import (
    Observation,
    generate_entity_id,
)
from cognitia.epistemic.service import EpistemicService
from cognitia.epistemic.types import EpistemicStatus
from cognitia.experience.record import ExperienceRecord
from cognitia.memory.store import MemoryStore
from cognitia.memory.types import MemoryContext, MemoryQuery
from cognitia.persistence.store import PersistenceStore
from cognitia.provenance.record import ProvenanceRecord, SourceType
from cognitia.rules.capability import evaluate_predicate
from cognitia.rules.store import RuleStore
from cognitia.rules.types import CognitiveRule, RuleStatus

from cognitia.context.enrichers.compression import ContextCompressionEnricher
from cognitia.context.enrichers.epistemic import EpistemicTensionEnricher
from cognitia.context.enrichers.provenance import ProvenanceNeighbourhoodEnricher
from cognitia.context.enrichers.relationships import RelationshipEnricher
from cognitia.context.enrichers.sequences import SequenceEnricher
from cognitia.context.enrichers.state import StateReconstructionEnricher
from cognitia.context.enrichers.statistics import StatisticalEnricher
from cognitia.context.enrichers.temporal import (
    TemporalNeighbourhoodEnricher,
    parse_iso_timestamp,
)
from cognitia.context.types import (
    CognitiveContext,
    ContextItem,
    ContextQuery,
    RelevanceReason,
    TemporalContext,
)


@runtime_checkable
class ContextAssembler(Protocol):
    """Protocol for provider-neutral cognitive context assembly."""

    def assemble_context(
        self,
        observation: Observation,
        query: ContextQuery | None = None,
    ) -> CognitiveContext:
        """Assemble structured cognitive context around an observation."""
        ...


class DeterministicContextAssembler:
    """Deterministic reference implementation of ContextAssembler with modular Phase 3A Enrichment.
    
    INVARIANTS:
    1. References underlying objects by stable IDs rather than copying full domain objects.
    2. Enforces deterministic selection and ordering: (relevance_score desc, timestamp desc, ID asc).
    3. Produces deeply immutable CognitiveContext snapshots.
    4. Enriches context structurally without asserting causality, truth, or decisions.
    """

    def __init__(
        self,
        persistence_store: PersistenceStore,
        memory_store: MemoryStore,
        rule_store: RuleStore,
        epistemic_service: EpistemicService,
    ) -> None:
        self._persistence = persistence_store
        self._memory = memory_store
        self._rules = rule_store
        self._epistemics = epistemic_service

        # Modular deterministic enrichers
        self._temporal_enricher = TemporalNeighbourhoodEnricher()
        self._relationship_enricher = RelationshipEnricher()
        self._state_enricher = StateReconstructionEnricher()
        self._sequence_enricher = SequenceEnricher()
        self._statistical_enricher = StatisticalEnricher()
        self._provenance_enricher = ProvenanceNeighbourhoodEnricher()
        self._epistemic_enricher = EpistemicTensionEnricher()
        self._compression_enricher = ContextCompressionEnricher()

    def assemble_context(
        self,
        observation: Observation,
        query: ContextQuery | None = None,
    ) -> CognitiveContext:
        """Assemble situational context around the reference observation with deterministic sorting and modular enrichment."""
        q = query or ContextQuery()

        # Resolve subject identifier
        subject_id = q.explicit_subject_id or observation.metadata.get("subject_id")
        if not subject_id and isinstance(observation.payload, dict):
            subject_id = (
                observation.payload.get("subject_id")
                or observation.payload.get("customer")
                or observation.payload.get("supplier")
                or observation.payload.get("item_code")
                or observation.payload.get("material")
                or observation.payload.get("sample_id")
                or observation.payload.get("vehicle_id")
                or observation.payload.get("design_id")
            )

        source_app = observation.metadata.get("source_application") or ""
        episode_id = observation.metadata.get("episode_id") or observation.metadata.get("doc_name")
        scope = q.scope or observation.metadata.get("scope")

        # 1. Temporal Context Assembly & Relations
        all_persisted = [
            obj for obj in self._persistence.list_all_objects()
            if isinstance(obj, Observation)
        ]
        temporal_ctx, temporal_observations = self._temporal_enricher.compute_temporal_context(
            reference_observation=observation,
            persisted_observations=all_persisted,
            query=q,
        )

        # 2. Memory Context Assembly
        related_experiences: list[ExperienceRecord] = []
        memory_observations: list[Observation] = []
        epistemic_tuples: list[tuple[str, EpistemicStatus]] = []

        if q.include_memory:
            mem_query = MemoryQuery(
                source_application=source_app if source_app else None,
                episode_id=episode_id,
                object_types=["ExperienceRecord", "Observation"],
            )
            memory_ctx = self._memory.get_context(mem_query)
            related_experiences.extend(memory_ctx.experiences[: q.max_related_experiences])
            memory_observations.extend(memory_ctx.observations[: q.max_related_observations])
            if q.include_epistemics:
                epistemic_tuples.extend(sorted(memory_ctx.epistemic_states.items()))

        # 3. Rule Discovery (identify ACTIVE rules without executing inference)
        active_rules: list[CognitiveRule] = []
        if q.include_rules:
            candidate_rules = self._rules.list_rules(status=RuleStatus.ACTIVE)
            eval_payload = dict(observation.payload)
            if "metadata" in eval_payload and isinstance(eval_payload["metadata"], dict):
                eval_payload.update(eval_payload["metadata"])
            eval_payload.update(observation.metadata)

            for r in candidate_rules:
                if scope and r.scope not in (scope, "general"):
                    continue
                if not r.predicate or evaluate_predicate(r.predicate, eval_payload):
                    active_rules.append(r)

        # 4. Build ContextItem Inventory with explicit relevance reasons
        context_items_map: dict[str, ContextItem] = {}

        # Reference observation
        context_items_map[observation.id] = ContextItem(
            item_id=observation.id,
            item_type="Observation",
            relevance_reason=RelevanceReason.REFERENCE_OBSERVATION,
            relevance_score=1.0,
            provenance_id=observation.provenance.id if hasattr(observation, "provenance") else None,
        )

        # Temporal and Subject observations
        for obs in temporal_observations:
            reason = RelevanceReason.TEMPORAL_MATCH
            score = 0.70
            obs_subject = obs.metadata.get("subject_id") or (
                obs.payload.get("subject_id") if isinstance(obs.payload, dict) else None
            )
            if subject_id and obs_subject == subject_id:
                reason = RelevanceReason.SUBJECT_MATCH
                score = 0.90
            elif episode_id and obs.metadata.get("episode_id") == episode_id:
                reason = RelevanceReason.EPISODE_MATCH
                score = 0.80

            context_items_map[obs.id] = ContextItem(
                item_id=obs.id,
                item_type="Observation",
                relevance_reason=reason,
                relevance_score=score,
                provenance_id=getattr(obs, "provenance", None),
            )

        # Related experiences
        for exp in related_experiences:
            context_items_map[exp.id] = ContextItem(
                item_id=exp.id,
                item_type="ExperienceRecord",
                relevance_reason=RelevanceReason.MEMORY_MATCH,
                relevance_score=0.85,
                provenance_id=exp.provenance.id if hasattr(exp, "provenance") else None,
            )

        # Active rules
        for rule in active_rules:
            context_items_map[rule.id] = ContextItem(
                item_id=rule.id,
                item_type="CognitiveRule",
                relevance_reason=RelevanceReason.RULE_MATCH,
                relevance_score=0.95,
                provenance_id=rule.provenance.id if hasattr(rule, "provenance") else None,
            )

        # Combine observations for ID sorting
        all_obs_dict: dict[str, Observation] = {}
        for obs in temporal_observations + memory_observations:
            if obs.id != observation.id:
                all_obs_dict[obs.id] = obs

        # 5. Deterministic Sorting
        sorted_obs_ids = tuple(
            o.id for o in sorted(
                all_obs_dict.values(),
                key=lambda o: (o.created_at, o.id),
                reverse=True,
            )[: q.max_related_observations]
        )

        sorted_exp_ids = tuple(
            e.id for e in sorted(
                related_experiences,
                key=lambda e: (e.created_at, e.id),
                reverse=True,
            )
        )

        sorted_rule_ids = tuple(
            r.rule_id for r in sorted(
                active_rules,
                key=lambda r: (-r.confidence, r.rule_id, r.version),
            )
        )

        sorted_context_items = tuple(
            sorted(
                context_items_map.values(),
                key=lambda item: (-item.relevance_score, item.relevance_reason.value, item.item_id),
            )
        )

        # All chronological observations in context (including reference observation)
        all_chronological_obs = sorted(
            [observation] + list(all_obs_dict.values()),
            key=lambda o: (parse_iso_timestamp(o.created_at), o.id),
        )

        # --- MODULAR PHASE 3A ENRICHMENTS ---

        # 1. Entity Neighbourhood & Structural Associations
        entity_relations = self._relationship_enricher.compute_entity_neighbourhood(
            reference_observation=observation,
            all_observations=all_chronological_obs,
            related_experiences=related_experiences,
            subject_id=subject_id,
            episode_id=episode_id,
            source_app=source_app,
        )

        # 2. State Reconstruction
        state_reconstruction = self._state_enricher.reconstruct_state(
            reference_observation=observation,
            chronological_observations=all_chronological_obs,
        ) if q.include_state_reconstruction else None

        # 3. Event Sequence Context
        sequences = self._sequence_enricher.compute_sequences(
            reference_observation=observation,
            chronological_observations=all_chronological_obs,
        ) if q.include_sequences else ()

        # 4. Recurrence Patterns
        recurrence = self._statistical_enricher.compute_recurrence(
            chronological_observations=all_chronological_obs,
            subject_id=subject_id,
            pattern_name=source_app or "general_event",
        ) if q.include_recurrence else ()

        # 5. Deterministic Aggregates & Contextual Deviations
        aggregates, deviations = self._statistical_enricher.compute_aggregates_and_deviations(
            chronological_observations=all_chronological_obs,
        ) if (q.include_aggregates or q.include_deviations) else ((), ())

        # 6. Cross-Source Correlation
        correlations = self._relationship_enricher.compute_cross_source_correlations(
            all_chronological_obs=all_chronological_obs,
        ) if q.include_correlations else ()

        # 7. Provenance Neighbourhood
        prov_neighbourhood = self._provenance_enricher.compute_provenance_neighbourhood(
            reference_observation=observation,
            source_app=source_app,
            related_experience_ids=sorted_exp_ids,
            active_rule_ids=sorted_rule_ids,
        ) if q.include_provenance_neighbourhood else ()

        # 8. Epistemic Tension
        epistemic_tensions = self._epistemic_enricher.compute_epistemic_tensions(
            epistemic_service=self._epistemics,
        ) if q.include_epistemic_tensions else ()

        # 9. Context Conflicts
        conflicts = self._epistemic_enricher.compute_conflicts(
            chronological_observations=all_chronological_obs,
        ) if q.include_conflicts else ()

        # 10. Context Compression
        compression = self._compression_enricher.compute_compression(
            chronological_observations=all_chronological_obs,
            epistemic_context=tuple(epistemic_tuples),
            sequence_count=len(sequences),
            deviation_count=len(deviations),
            conflict_count=len(conflicts),
        ) if q.include_compression else None

        # Composite Provenance
        parent_ids = [observation.id] + [item.item_id for item in sorted_context_items if item.item_id != observation.id]
        prov = ProvenanceRecord(
            source_type=SourceType.COMPOSITE,
            producer_id="context_assembly_engine",
            parent_ids=parent_ids,
            is_deterministic=True,
        )

        from cognitia.context.types import StateReconstruction
        final_state_reconstruction = state_reconstruction or StateReconstruction()

        return CognitiveContext(
            id=generate_entity_id(),
            reference_observation_id=observation.id,
            reference_subject_id=subject_id,
            temporal_context=temporal_ctx,
            related_observation_ids=sorted_obs_ids,
            related_experience_ids=sorted_exp_ids,
            active_rule_ids=sorted_rule_ids,
            epistemic_context=tuple(epistemic_tuples),
            context_items=sorted_context_items,
            entity_neighbourhood=entity_relations,
            state_reconstruction=final_state_reconstruction,
            sequences=sequences,
            recurrence=recurrence,
            aggregates=aggregates,
            deviations=deviations,
            correlations=correlations,
            provenance_neighbourhood=prov_neighbourhood,
            epistemic_tensions=epistemic_tensions,
            conflicts=conflicts,
            compression=compression,
            provenance=prov,
            metadata={
                "source_application": source_app,
                "episode_id": episode_id,
                "scope": scope,
            },
        )
