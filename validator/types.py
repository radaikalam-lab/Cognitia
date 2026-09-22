"""Independent Deterministic Validator Types.

Defines the minimum validation result model for project directional
programming conformance checks.

The validator is independent of Cognitia's reasoning authority.
It consumes the public project_spec data model and produces
structured evidence without approval, governance, or execution semantics.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from cognitia.abi.types import (
    CognitiveObject,
    SCHEMA_VERSION_V1,
    current_utc_timestamp,
    generate_entity_id,
)
from cognitia.provenance.record import ProvenanceRecord, SourceType


class ValidationStatus(str, enum.Enum):
    """Conformance status for a validation check or overall result.

    The validator must never return governance/authority statuses.
    """

    PASS = "pass"
    FAIL = "fail"
    INCONCLUSIVE = "inconclusive"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True)
class ValidationFinding(CognitiveObject):
    """Single deterministic finding from a validation check."""

    validation_id: str = ""
    rule_id: str = ""
    subject_id: str = ""
    check: str = ""
    expected: str = ""
    observed: str = ""
    status: str = ValidationStatus.NOT_APPLICABLE.value
    explanation: str = ""
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(
            source_type=SourceType.DETERMINISTIC_RULE
        )
    )

    def __init__(
        self,
        validation_id: str = "",
        rule_id: str = "",
        subject_id: str = "",
        check: str = "",
        expected: str = "",
        observed: str = "",
        status: str = ValidationStatus.NOT_APPLICABLE.value,
        explanation: str = "",
        provenance: ProvenanceRecord | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "id", generate_entity_id())
        object.__setattr__(self, "schema_version", SCHEMA_VERSION_V1)
        object.__setattr__(self, "created_at", current_utc_timestamp())

        object.__setattr__(self, "validation_id", str(validation_id))
        object.__setattr__(self, "rule_id", str(rule_id))
        object.__setattr__(self, "subject_id", str(subject_id))
        object.__setattr__(self, "check", str(check))
        object.__setattr__(self, "expected", str(expected))
        object.__setattr__(self, "observed", str(observed))
        object.__setattr__(self, "status", str(status))
        object.__setattr__(self, "explanation", str(explanation))

        prov = provenance or ProvenanceRecord(
            source_type=SourceType.DETERMINISTIC_RULE,
            producer_id="validation_finding_builder",
            is_deterministic=True,
        )
        object.__setattr__(self, "provenance", prov)
        object.__setattr__(self, "metadata", dict(metadata or {}))


@dataclass(frozen=True)
class ValidationResult(CognitiveObject):
    """Immutable validation result for a directional specification and candidate.

    INVARIANTS:
    1. Validation result is evidence, not approval.
    2. Validation result is not a governance decision.
    3. Validation result does not authorize execution.
    """

    validation_id: str = ""
    subject_id: str = ""
    specification_id: str = ""
    validator_id: str = ""
    validator_version: str = "1.0.0"
    status: str = ValidationStatus.NOT_APPLICABLE.value
    findings: tuple[ValidationFinding, ...] = ()
    checked_constraints: tuple[str, ...] = ()
    checked_invariants: tuple[str, ...] = ()
    traceability: tuple[str, ...] = ()
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(
            source_type=SourceType.DETERMINISTIC_RULE
        )
    )

    def __init__(
        self,
        validation_id: str = "",
        subject_id: str = "",
        specification_id: str = "",
        validator_id: str = "",
        validator_version: str = "1.0.0",
        status: str = ValidationStatus.NOT_APPLICABLE.value,
        findings: Sequence[ValidationFinding] = (),
        checked_constraints: Sequence[str] = (),
        checked_invariants: Sequence[str] = (),
        traceability: Sequence[str] = (),
        provenance: ProvenanceRecord | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "id", generate_entity_id())
        object.__setattr__(self, "schema_version", SCHEMA_VERSION_V1)
        object.__setattr__(self, "created_at", current_utc_timestamp())

        object.__setattr__(self, "validation_id", str(validation_id))
        object.__setattr__(self, "subject_id", str(subject_id))
        object.__setattr__(self, "specification_id", str(specification_id))
        object.__setattr__(self, "validator_id", str(validator_id))
        object.__setattr__(self, "validator_version", str(validator_version))
        object.__setattr__(self, "status", str(status))
        object.__setattr__(self, "findings", tuple(findings))
        object.__setattr__(self, "checked_constraints", tuple(checked_constraints))
        object.__setattr__(self, "checked_invariants", tuple(checked_invariants))
        object.__setattr__(self, "traceability", tuple(traceability))

        prov = provenance or ProvenanceRecord(
            source_type=SourceType.DETERMINISTIC_RULE,
            producer_id="validation_result_builder",
            is_deterministic=True,
        )
        object.__setattr__(self, "provenance", prov)
        object.__setattr__(self, "metadata", dict(metadata or {}))
