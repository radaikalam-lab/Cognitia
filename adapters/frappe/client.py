"""Frappe Cognitia Application Adapter.

Provides the primary integration interface connecting Frappe / ERPNext
environments to Cognitia runtime services while strictly preserving the authority boundary.
"""

from __future__ import annotations

from typing import Any

from cognitia.abi.types import Decision, Observation, generate_entity_id
from cognitia.experience.record import ExperienceRecord
from cognitia.memory.types import MemoryQuery
from cognitia.persistence.events import CognitiveEvent, CognitiveEventType
from cognitia.provenance.record import ProvenanceRecord, SourceType
from cognitia.rules.types import CognitiveRule, RuleStatus
from cognitia.runtime.local import LocalCognitiveRuntime

from adapters.frappe.advisory import FrappeAdvisory
from adapters.frappe.events import FrappeEvent, FrappeEventType
from adapters.frappe.experience import ERPLifecycleType, FrappeExperienceBuilder
from adapters.frappe.translator import FrappeEventTranslator


class FrappeCognitiaAdapter:
    """External application adapter bridging Frappe / ERPNext to Cognitia Core.
    
    INVARIANTS:
    1. Adapter depends on Cognitia; Cognitia Core has ZERO dependencies on this adapter or Frappe.
    2. Authority remains with Frappe/Human; Cognitia outputs non-authoritative advisories.
    3. All ingested events, experiences, and rules carry complete lineage provenance.
    """

    def __init__(self, runtime: LocalCognitiveRuntime | None = None) -> None:
        self._runtime = runtime or LocalCognitiveRuntime()

    @property
    def runtime(self) -> LocalCognitiveRuntime:
        """Access the underlying Cognitia runtime."""
        return self._runtime

    def ingest_event(
        self,
        event: FrappeEvent | dict[str, Any],
    ) -> Observation:
        """Translate and persist a Frappe ERP event into Cognitia memory and event journal."""
        if isinstance(event, dict):
            event = FrappeEvent(
                event_type=event.get("event_type", "GenericFrappeEvent"),
                doc_type=event.get("doc_type", "UnknownDocType"),
                doc_name=event.get("doc_name", "UNKNOWN"),
                payload=event.get("payload", {}),
                subject_id=event.get("subject_id"),
                timestamp=event.get("timestamp"),
                user=event.get("user", "Administrator"),
            )

        observation = FrappeEventTranslator.translate(event)

        # Persist observation in ObjectStore via PersistenceStore
        self._runtime.persistence.save_object(observation)

        # Log timeline event in EventJournal
        cog_event = CognitiveEvent(
            event_type=CognitiveEventType.OBSERVATION_RECORDED.value,
            source_type=SourceType.SENSOR,
            source_id=observation.id,
            subject_id=observation.metadata.get("subject_id"),
            payload={
                "doc_type": event.doc_type,
                "doc_name": event.doc_name,
                "event_type": str(event.event_type),
                "subject_id": observation.metadata.get("subject_id"),
            },
            provenance=ProvenanceRecord(
                source_type=SourceType.SENSOR,
                producer_id="frappe_adapter",
                parent_ids=[observation.id],
            ),
        )
        self._runtime.persistence.append_event(cog_event)

        return observation

    def record_lifecycle_experience(
        self,
        lifecycle_id: str,
        lifecycle_type: str | ERPLifecycleType,
        observations: list[Observation],
        agent_id: str = "frappe_system",
        additional_context: dict[str, Any] | None = None,
    ) -> ExperienceRecord:
        """Group a set of ERP observations into an ExperienceRecord and persist it."""
        experience = FrappeExperienceBuilder.build_lifecycle_experience(
            lifecycle_id=lifecycle_id,
            lifecycle_type=lifecycle_type,
            observations=observations,
            environment_id="frappe_erpnext",
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
                producer_id="frappe_adapter",
                parent_ids=[experience.id],
            ),
        )
        self._runtime.persistence.append_event(cog_event)

        return experience

    def get_advisory(
        self,
        doc_type: str,
        doc_name: str,
        payload: dict[str, Any],
        subject_id: str | None = None,
        scope: str | None = None,
    ) -> FrappeAdvisory:
        """Query Cognitia memory and rules to construct a read-only FrappeAdvisory.
        
        This method NEVER modifies the input document or any ERP database records.
        """
        # Create an observation representing the current document state
        event = FrappeEvent(
            event_type=f"{doc_type}Inspection",
            doc_type=doc_type,
            doc_name=doc_name,
            payload=payload,
            subject_id=subject_id,
        )
        current_obs = FrappeEventTranslator.translate(event)

        # Query historical experiences via Memory Layer
        target_subject = subject_id or current_obs.metadata.get("subject_id")
        mem_query = MemoryQuery(
            source_application="frappe",
            object_types=["ExperienceRecord", "Observation"],
        )
        retrieved_items = self._runtime.memory.retrieve(mem_query)

        # Filter items matching subject if available
        similar_count = 0
        evidence_count = 0
        for item in retrieved_items:
            meta = getattr(item, "metadata", {})
            if isinstance(meta, dict):
                item_subject = meta.get("subject_id")
                if target_subject and item_subject == target_subject:
                    similar_count += 1
                elif not target_subject:
                    similar_count += 1
            else:
                similar_count += 1

            if isinstance(item, Observation) or type(item).__name__ in ("Observation", "Evidence"):
                evidence_count += 1

        # Request decision from runtime (evaluating rules)
        eval_scope = scope or f"erp.{doc_type.lower().replace(' ', '_')}"
        decision_context = {
            "scope": eval_scope,
            "doc_type": doc_type,
            "doc_name": doc_name,
            "subject_id": target_subject,
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
            f"Retrieved {similar_count} historical experiences for {target_subject or doc_name}."
            if similar_count > 0
            else f"No previous history found for {target_subject or doc_name}."
        )

        return FrappeAdvisory(
            document_type=doc_type,
            document_name=doc_name,
            historical_context_summary=context_summary,
            similar_experiences_count=similar_count,
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

    # --- Human-Governed Rule Management ---

    def create_human_rule(
        self,
        rule_id: str,
        name: str,
        description: str,
        predicate: dict[str, Any],
        recommendation: dict[str, Any],
        scope: str = "general",
        rationale: str = "",
        author_id: str = "frappe_administrator",
        confidence: float = 1.0,
        version: str = "1.0.0",
        evidence_ids: list[str] | None = None,
    ) -> CognitiveRule:
        """Register a human-authored cognitive rule with explicit human provenance."""
        prov = ProvenanceRecord(
            source_type=SourceType.HUMAN,
            producer_id=author_id,
            is_deterministic=True,
        )

        rule = CognitiveRule(
            rule_id=rule_id,
            version=version,
            name=name,
            description=description,
            scope=scope,
            predicate=predicate,
            recommendation=recommendation,
            rationale=rationale,
            confidence=confidence,
            author_id=author_id,
            status=RuleStatus.ACTIVE,
            evidence_ids=evidence_ids or [],
            provenance=prov,
        )

        registered = self._runtime.rules.create_rule(rule)
        return registered

    def supersede_human_rule(
        self,
        rule_id: str,
        new_version: str,
        name: str | None = None,
        description: str | None = None,
        predicate: dict[str, Any] | None = None,
        recommendation: dict[str, Any] | None = None,
        scope: str | None = None,
        rationale: str = "",
        author_id: str = "frappe_administrator",
        confidence: float = 1.0,
        evidence_ids: list[str] | None = None,
    ) -> tuple[CognitiveRule, CognitiveRule]:
        """Supersede an active rule to Version N+1, preserving the immutable historical version."""
        old_rule = self._runtime.rules.get_rule(rule_id)
        if not old_rule:
            raise ValueError(f"Rule '{rule_id}' not found for supersession")

        prov = ProvenanceRecord(
            source_type=SourceType.HUMAN,
            producer_id=author_id,
            parent_ids=[old_rule.id],
            is_deterministic=True,
        )

        new_rule = CognitiveRule(
            rule_id=rule_id,
            version=new_version,
            name=name or old_rule.name,
            description=description or old_rule.description,
            scope=scope or old_rule.scope,
            predicate=predicate if predicate is not None else old_rule.predicate,
            recommendation=recommendation if recommendation is not None else old_rule.recommendation,
            rationale=rationale or old_rule.rationale,
            confidence=confidence,
            author_id=author_id,
            status=RuleStatus.ACTIVE,
            parent_rule_version_id=old_rule.id,
            evidence_ids=evidence_ids if evidence_ids is not None else old_rule.evidence_ids,
            provenance=prov,
        )

        return self._runtime.rules.supersede_rule(rule_id, new_rule, rationale=rationale)

    def retire_human_rule(
        self,
        rule_id: str,
        version: str | None = None,
        rationale: str = "",
    ) -> CognitiveRule:
        """Retire a cognitive rule while preserving audit history."""
        return self._runtime.rules.retire_rule(rule_id, version=version, rationale=rationale)
