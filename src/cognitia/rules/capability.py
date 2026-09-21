"""Cognitia Rule Evaluation Capability.

Evaluates active cognitive rules against observations to produce
advisory Decisions with lineage provenance referencing the matched rule version.
"""

from __future__ import annotations

from typing import Any

from cognitia.abi.types import Action, Decision, Observation
from cognitia.capabilities.base import BaseCapability, CapabilityDescriptor, CapabilityType
from cognitia.provenance.record import ProvenanceRecord, SourceType
from cognitia.rules.store import RuleStore
from cognitia.rules.types import CognitiveRule, RuleStatus


def evaluate_predicate(predicate: dict[str, Any], payload: dict[str, Any]) -> bool:
    """Evaluate a structured predicate against a dictionary payload.
    
    Supports:
    - direct key-value match: {"field": value}
    - operator match: {"field": "x", "op": ">", "value": 3}
    - nested dot-lookup: {"field": "customer.overdue_invoices", ...}
    - compound: {"all": [...]} or {"any": [...]}
    """
    if not predicate:
        return True

    # Compound 'all'
    if "all" in predicate:
        return all(evaluate_predicate(p, payload) for p in predicate["all"])

    # Compound 'any'
    if "any" in predicate:
        return any(evaluate_predicate(p, payload) for p in predicate["any"])

    # Explicit operator format
    if "field" in predicate and "op" in predicate and "value" in predicate:
        field_path = predicate["field"]
        op = predicate["op"]
        expected = predicate["value"]
        actual = _resolve_path(payload, field_path)

        if actual is None:
            return False

        if op in ("==", "eq"):
            return actual == expected
        if op in ("!=", "neq"):
            return actual != expected
        if op in (">", "gt"):
            return actual > expected
        if op in (">=", "gte"):
            return actual >= expected
        if op in ("<", "lt"):
            return actual < expected
        if op in ("<=", "lte"):
            return actual <= expected
        if op in ("in", "contains"):
            return expected in actual or (isinstance(actual, (list, set, tuple)) and expected in actual)
        return False

    # Simple key-value matching
    for k, v in predicate.items():
        actual = _resolve_path(payload, k)
        if actual != v:
            return False
    return True


def _resolve_path(data: dict[str, Any], path: str) -> Any:
    """Resolve dot-notation path into nested dictionaries."""
    parts = path.split(".")
    current: Any = data
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


class RuleEvaluationCapability:
    """Capability that evaluates active CognitiveRules against input observations."""

    def __init__(
        self,
        rule_store: RuleStore,
        capability_id: str = "cognitive_rule_evaluator_v1",
        provider_name: str = "cognitia_rules",
        version: str = "1.0.0",
    ) -> None:
        self._rule_store = rule_store
        self._descriptor = CapabilityDescriptor(
            capability_id=capability_id,
            capability_type=CapabilityType.DECISION,
            provider_name=provider_name,
            version=version,
            is_deterministic=True,
        )

    @property
    def descriptor(self) -> CapabilityDescriptor:
        return self._descriptor

    def propose_decision(
        self,
        observation: Observation,
        context: dict[str, Any] | None = None,
    ) -> Decision:
        """Evaluate active rules against observation payload and return advisory Decision."""
        ctx = context or {}
        scope = ctx.get("scope")
        active_rules = self._rule_store.list_rules(status=RuleStatus.ACTIVE, scope=scope)

        matched_rule: CognitiveRule | None = None
        for rule in active_rules:
            # Combine observation payload and context for predicate matching
            eval_payload = dict(observation.payload)
            if "metadata" in eval_payload and isinstance(eval_payload["metadata"], dict):
                eval_payload.update(eval_payload["metadata"])
            eval_payload.update(ctx)

            if evaluate_predicate(rule.predicate, eval_payload):
                matched_rule = rule
                break

        if matched_rule:
            action_name = matched_rule.recommendation.get("action_name", "advisory_flag")
            action_params = dict(matched_rule.recommendation.get("parameters", {}))
            action_params["triggered_rule_id"] = matched_rule.rule_id
            action_params["rule_version"] = matched_rule.version

            proposed_action = Action(
                name=action_name,
                parameters=action_params,
                target_node=observation.source_id,
            )

            prov = ProvenanceRecord(
                source_type=SourceType.DETERMINISTIC_RULE,
                producer_id=f"{self._descriptor.provider_name}:{self._descriptor.capability_id}",
                capability_id=self._descriptor.capability_id,
                parent_ids=[observation.id, matched_rule.id],
                is_deterministic=True,
            )

            return Decision(
                proposal_type=matched_rule.recommendation.get("proposal_type", "rule_advisory"),
                proposed_action=proposed_action,
                confidence=matched_rule.confidence,
                rationale=f"Rule {matched_rule.rule_id} (v{matched_rule.version}) triggered: {matched_rule.rationale or matched_rule.description}",
                provenance=prov,
                metadata={
                    "triggered_rule_id": matched_rule.rule_id,
                    "rule_version": matched_rule.version,
                    "rule_name": matched_rule.name,
                    "rule_scope": matched_rule.scope,
                    "input_observation_ids": [observation.id],
                    "evidence_ids": matched_rule.evidence_ids,
                },
            )

        # No rule triggered: return neutral noop decision
        proposed_action = Action(
            name="no_advisory_flag",
            parameters={"observation_id": observation.id},
            target_node=observation.source_id,
        )
        prov = ProvenanceRecord(
            source_type=SourceType.DETERMINISTIC_RULE,
            producer_id=f"{self._descriptor.provider_name}:{self._descriptor.capability_id}",
            capability_id=self._descriptor.capability_id,
            parent_ids=[observation.id],
            is_deterministic=True,
        )
        return Decision(
            proposal_type="neutral_advisory",
            proposed_action=proposed_action,
            confidence=1.0,
            rationale="No cognitive rules matched observation",
            provenance=prov,
            metadata={"input_observation_ids": [observation.id]},
        )
