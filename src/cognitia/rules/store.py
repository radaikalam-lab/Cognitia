"""Cognitia Cognitive Rule Store and Lifecycle Management.

Defines the RuleStore SPI and in-memory reference implementation
enforcing rule immutability, versioning, supersession, and retirement.
"""

from __future__ import annotations

import threading
from typing import Protocol, runtime_checkable

from cognitia.abi.types import current_utc_timestamp
from cognitia.provenance.record import ProvenanceRecord, SourceType
from cognitia.rules.types import CognitiveRule, RuleStatus


@runtime_checkable
class RuleStore(Protocol):
    """Protocol governing versioned cognitive rule persistence and lifecycle."""

    def create_rule(self, rule: CognitiveRule) -> CognitiveRule:
        """Register a new cognitive rule."""
        ...

    def get_rule(self, rule_id: str, version: str | None = None) -> CognitiveRule | None:
        """Retrieve a rule by logical rule_id and optional version (defaults to active/latest)."""
        ...

    def list_rules(
        self,
        status: RuleStatus | None = None,
        scope: str | None = None,
    ) -> list[CognitiveRule]:
        """List rules filtered by status and/or scope."""
        ...

    def supersede_rule(
        self,
        rule_id: str,
        new_version_rule: CognitiveRule,
        rationale: str = "",
    ) -> tuple[CognitiveRule, CognitiveRule]:
        """Supersede an existing active rule version with a new version (Version N -> Version N+1)."""
        ...

    def retire_rule(
        self,
        rule_id: str,
        version: str | None = None,
        rationale: str = "",
    ) -> CognitiveRule:
        """Retire an active rule without destroying historical records."""
        ...

    def get_rule_history(self, rule_id: str) -> list[CognitiveRule]:
        """Return all historical versions of a rule in chronological order."""
        ...


class InMemoryRuleStore:
    """Thread-safe reference implementation of RuleStore enforcing version immutability."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        # map (rule_id, version) -> CognitiveRule
        self._rules: dict[tuple[str, str], CognitiveRule] = {}
        # map rule_id -> list of version strings in chronological order
        self._history: dict[str, list[str]] = {}

    def create_rule(self, rule: CognitiveRule) -> CognitiveRule:
        with self._lock:
            key = (rule.rule_id, rule.version)
            if key in self._rules:
                raise ValueError(f"Rule '{rule.rule_id}' version '{rule.version}' already exists")

            self._rules[key] = rule
            if rule.rule_id not in self._history:
                self._history[rule.rule_id] = []
            self._history[rule.rule_id].append(rule.version)
            return rule

    def get_rule(self, rule_id: str, version: str | None = None) -> CognitiveRule | None:
        with self._lock:
            if version is not None:
                return self._rules.get((rule_id, version))

            # Default: return active version, or latest version if none active
            versions = self._history.get(rule_id, [])
            if not versions:
                return None

            for v in reversed(versions):
                r = self._rules.get((rule_id, v))
                if r and r.status == RuleStatus.ACTIVE:
                    return r

            # If no active, return latest
            latest_version = versions[-1]
            return self._rules.get((rule_id, latest_version))

    def list_rules(
        self,
        status: RuleStatus | None = None,
        scope: str | None = None,
    ) -> list[CognitiveRule]:
        with self._lock:
            results: list[CognitiveRule] = []
            for rule in self._rules.values():
                if status is not None and rule.status != status:
                    continue
                if scope is not None and rule.scope != scope:
                    continue
                results.append(rule)
            return results

    def supersede_rule(
        self,
        rule_id: str,
        new_version_rule: CognitiveRule,
        rationale: str = "",
    ) -> tuple[CognitiveRule, CognitiveRule]:
        with self._lock:
            current_rule = self.get_rule(rule_id)
            if not current_rule:
                raise ValueError(f"Rule '{rule_id}' not found for supersession")

            if current_rule.status != RuleStatus.ACTIVE:
                raise ValueError(f"Cannot supersede non-active rule '{rule_id}' (status={current_rule.status.value})")

            # Create superseded version of old rule
            old_prov = ProvenanceRecord(
                source_type=current_rule.provenance.source_type,
                producer_id=current_rule.provenance.producer_id,
                parent_ids=[current_rule.id],
                is_deterministic=True,
            )
            superseded_old_rule = CognitiveRule(
                id=current_rule.id,
                schema_version=current_rule.schema_version,
                created_at=current_rule.created_at,
                metadata=dict(current_rule.metadata, supersession_rationale=rationale),
                rule_id=current_rule.rule_id,
                version=current_rule.version,
                name=current_rule.name,
                description=current_rule.description,
                scope=current_rule.scope,
                predicate=current_rule.predicate,
                recommendation=current_rule.recommendation,
                rationale=current_rule.rationale,
                confidence=current_rule.confidence,
                author_id=current_rule.author_id,
                status=RuleStatus.SUPERSEDED,
                parent_rule_version_id=current_rule.parent_rule_version_id,
                evidence_ids=current_rule.evidence_ids,
                provenance=old_prov,
            )

            # Update old key
            self._rules[(current_rule.rule_id, current_rule.version)] = superseded_old_rule

            # Register new version
            new_key = (new_version_rule.rule_id, new_version_rule.version)
            if new_key in self._rules:
                raise ValueError(f"New rule version '{new_version_rule.version}' already exists for rule '{rule_id}'")

            # Ensure parent link
            if not new_version_rule.parent_rule_version_id:
                new_version_rule = CognitiveRule(
                    id=new_version_rule.id,
                    schema_version=new_version_rule.schema_version,
                    created_at=new_version_rule.created_at,
                    metadata=new_version_rule.metadata,
                    rule_id=new_version_rule.rule_id,
                    version=new_version_rule.version,
                    name=new_version_rule.name,
                    description=new_version_rule.description,
                    scope=new_version_rule.scope,
                    predicate=new_version_rule.predicate,
                    recommendation=new_version_rule.recommendation,
                    rationale=new_version_rule.rationale,
                    confidence=new_version_rule.confidence,
                    author_id=new_version_rule.author_id,
                    status=new_version_rule.status,
                    parent_rule_version_id=current_rule.id,
                    evidence_ids=new_version_rule.evidence_ids,
                    provenance=new_version_rule.provenance,
                )

            self._rules[new_key] = new_version_rule
            if new_version_rule.version not in self._history[rule_id]:
                self._history[rule_id].append(new_version_rule.version)

            return superseded_old_rule, new_version_rule

    def retire_rule(
        self,
        rule_id: str,
        version: str | None = None,
        rationale: str = "",
    ) -> CognitiveRule:
        with self._lock:
            rule = self.get_rule(rule_id, version=version)
            if not rule:
                raise ValueError(f"Rule '{rule_id}' version '{version}' not found for retirement")

            retired_prov = ProvenanceRecord(
                source_type=rule.provenance.source_type,
                producer_id=rule.provenance.producer_id,
                parent_ids=[rule.id],
                is_deterministic=True,
            )
            retired_rule = CognitiveRule(
                id=rule.id,
                schema_version=rule.schema_version,
                created_at=rule.created_at,
                metadata=dict(rule.metadata, retirement_rationale=rationale),
                rule_id=rule.rule_id,
                version=rule.version,
                name=rule.name,
                description=rule.description,
                scope=rule.scope,
                predicate=rule.predicate,
                recommendation=rule.recommendation,
                rationale=rule.rationale,
                confidence=rule.confidence,
                author_id=rule.author_id,
                status=RuleStatus.RETIRED,
                parent_rule_version_id=rule.parent_rule_version_id,
                evidence_ids=rule.evidence_ids,
                provenance=retired_prov,
            )

            self._rules[(rule.rule_id, rule.version)] = retired_rule
            return retired_rule

    def get_rule_history(self, rule_id: str) -> list[CognitiveRule]:
        with self._lock:
            versions = self._history.get(rule_id, [])
            return [self._rules[(rule_id, v)] for v in versions if (rule_id, v) in self._rules]
