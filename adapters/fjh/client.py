"""Flash Joule Heating (FJH) Cognitia Application Adapter.

Provides the primary integration interface connecting FJH experimental environments
to Cognitia runtime services while strictly preserving the authority boundary.
"""

from __future__ import annotations

from typing import Any

from cognitia.abi.types import Decision, Observation, generate_entity_id
from cognitia.experience.record import ExperienceRecord
from cognitia.memory.types import MemoryQuery
from cognitia.persistence.events import CognitiveEvent, CognitiveEventType
from cognitia.provenance.record import ProvenanceRecord, SourceType
from cognitia.runtime.local import LocalCognitiveRuntime

from adapters.fjh.advisory import FJHAdvisory
from adapters.fjh.events import FJHEvent, FJHStage
from adapters.fjh.experience import FJHExperienceBuilder, FJHLifecycleType
from adapters.fjh.schemas import FJHDerivedMetricSchema, FJHMeasurementSchema, FJHRequestSchema
from adapters.fjh.translator import FJHEventTranslator


class FJHCognitiaAdapter:
    """External application adapter bridging Flash Joule Heating experiments to Cognitia Core.

    INVARIANTS:
    1. Adapter depends on Cognitia; Cognitia Core has ZERO dependencies on this adapter or FJH.
    2. Authority remains with the FJH operator/human; Cognitia outputs non-authoritative advisories.
    3. All ingested events, experiences, and rules carry complete lineage provenance.
    4. This adapter produces representations only; it never issues hardware commands.
    """

    def __init__(self, runtime: LocalCognitiveRuntime | None = None) -> None:
        self._runtime = runtime or LocalCognitiveRuntime()

    @property
    def runtime(self) -> LocalCognitiveRuntime:
        """Access the underlying Cognitia runtime."""
        return self._runtime

    def ingest_event(
        self,
        event: FJHEvent | dict[str, Any],
    ) -> Observation:
        """Translate and persist an FJH event into Cognitia memory and event journal."""
        if isinstance(event, dict):
            stage = event.get("stage", "FJH_REQUESTED")
            if isinstance(stage, str):
                try:
                    stage = FJHStage(stage)
                except ValueError:
                    stage = FJHStage.REQUESTED
            event = FJHEvent(
                stage=stage,
                experiment_id=event.get("experiment_id", "UNKNOWN"),
                payload=event.get("payload", {}),
                precursor_id=event.get("precursor_id"),
                chamber_id=event.get("chamber_id"),
                operator_id=event.get("operator_id", "fjh_operator"),
                timestamp=event.get("timestamp"),
                metadata=event.get("metadata", {}),
            )

        observation = FJHEventTranslator.translate(event)

        # Persist observation in ObjectStore via PersistenceStore
        self._runtime.persistence.save_object(observation)

        # Log timeline event in EventJournal
        cog_event = CognitiveEvent(
            event_type=CognitiveEventType.OBSERVATION_RECORDED.value,
            source_type=SourceType.SENSOR,
            source_id=observation.id,
            subject_id=observation.metadata.get("experiment_id"),
            payload={
                "stage": str(event.stage),
                "experiment_id": event.experiment_id,
                "precursor_id": event.precursor_id,
                "chamber_id": event.chamber_id,
            },
            provenance=ProvenanceRecord(
                source_type=SourceType.SENSOR,
                producer_id="fjh_adapter",
                parent_ids=[observation.id],
            ),
        )
        self._runtime.persistence.append_event(cog_event)

        return observation

    def validate_request(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Validate an FJH experiment request payload against the request schema."""
        return FJHRequestSchema.validate(payload)

    def validate_measurement(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Validate an FJH measurement payload against the measurement schema."""
        return FJHMeasurementSchema.validate(payload)

    def validate_derived_metric(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Validate an FJH derived metric payload against the derived metric schema."""
        return FJHDerivedMetricSchema.validate(payload)

    def record_lifecycle_experience(
        self,
        lifecycle_id: str,
        lifecycle_type: str | FJHLifecycleType,
        observations: list[Observation],
        agent_id: str = "fjh_operator",
        additional_context: dict[str, Any] | None = None,
    ) -> ExperienceRecord:
        """Group a set of FJH observations into an ExperienceRecord and persist it."""
        experience = FJHExperienceBuilder.build_lifecycle_experience(
            lifecycle_id=lifecycle_id,
            lifecycle_type=lifecycle_type,
            observations=observations,
            environment_id="fjh_lab",
            agent_id=agent_id,
            additional_context=additional_context,
        )

        # Store in ExperienceService and PersistenceStore
        self._runtime.experience.record_experience(experience)
        self._runtime.persistence.save_object(experience)

        # Log timeline event
        cog_event = CognitiveEvent(
            event_type=CognitiveEventType.EXPERIENCE_RECORDED.value,
            source_type=SourceType.COMPOSITE,
            source_id=experience.id,
            subject_id=lifecycle_id,
            payload={
                "lifecycle_id": lifecycle_id,
                "lifecycle_type": str(lifecycle_type),
                "observation_count": len(observations),
            },
            provenance=ProvenanceRecord(
                source_type=SourceType.COMPOSITE,
                producer_id="fjh_adapter",
                parent_ids=[experience.id],
            ),
        )
        self._runtime.persistence.append_event(cog_event)

        return experience

    def get_advisory(
        self,
        experiment_id: str,
        stage: str,
        payload: dict[str, Any],
        scope: str | None = None,
    ) -> FJHAdvisory:
        """Query Cognitia memory and rules to construct a read-only FJHAdvisory.

        This method NEVER modifies FJH hardware state or issues any commands.
        """
        # Create an observation representing the current experiment state
        event = FJHEvent(
            stage=FJHStage(stage) if stage in [s.value for s in FJHStage] else FJHStage.REQUESTED,
            experiment_id=experiment_id,
            payload=payload,
        )
        current_obs = FJHEventTranslator.translate(event)

        # Query historical experiences via Memory Layer
        mem_query = MemoryQuery(
            source_application="fjh",
            object_types=["ExperienceRecord", "Observation"],
        )
        retrieved_items = self._runtime.memory.retrieve(mem_query)

        # Filter items matching experiment if available
        similar_count = 0
        evidence_count = 0
        for item in retrieved_items:
            meta = getattr(item, "metadata", {})
            if isinstance(meta, dict):
                item_experiment = meta.get("experiment_id")
                if item_experiment == experiment_id:
                    similar_count += 1
            else:
                similar_count += 1

            if isinstance(item, Observation) or type(item).__name__ in ("Observation", "Evidence"):
                evidence_count += 1

        # Request decision from runtime (evaluating rules)
        eval_scope = scope or f"fjh.{stage.lower()}"
        decision_context = {
            "scope": eval_scope,
            "experiment_id": experiment_id,
            "stage": stage,
        }
        decision = self._runtime.request_decision(
            current_obs,
            capability_id="cognitive_rule_evaluator_v1",
            context=decision_context,
        )

        triggered_rule_id = decision.metadata.get("triggered_rule_id")
        triggered_rule_version = decision.metadata.get("rule_version")
        recommendation_text = (
            f"{decision.proposed_action.name}: {decision.rationale}"
            if decision.rationale and decision.proposed_action.name not in decision.rationale
            else (decision.rationale or decision.proposed_action.name)
        )

        context_summary = (
            f"Retrieved {similar_count} historical experiences for {experiment_id}."
            if similar_count > 0
            else f"No previous history found for {experiment_id}."
        )

        return FJHAdvisory(
            experiment_id=experiment_id,
            stage=stage,
            historical_context_summary=context_summary,
            similar_experiments_count=similar_count,
            epistemic_status="SUPPORTED",
            evidence_count=evidence_count,
            triggered_rule_id=triggered_rule_id,
            triggered_rule_version=triggered_rule_version,
            recommendation=recommendation_text,
            confidence=decision.confidence,
            decision=decision,
            is_authoritative=False,
            metadata={
                "source_observation_id": current_obs.id,
                "scope": eval_scope,
            },
        )
