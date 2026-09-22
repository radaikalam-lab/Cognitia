"""Cognitia Project Erector Types.

Defines the minimum types for deterministic project erection:

- AcceptedScaffold: externally accepted scaffold specification
- GeneratedArtifact: a single generated filesystem artifact
- GeneratedArtifactType: category of generated artifact
- ErectionResult: overall erection outcome
- ErectionStatus: success/failure/partial outcome

The erector never creates acceptance; it consumes it.
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


class GeneratedArtifactType(str, enum.Enum):
    """Category of a generated project artifact."""

    DIRECTORY = "directory"
    FILE = "file"
    CONTRACT = "contract"
    TEST_SURFACE = "test_surface"
    INTERFACE_SURFACE = "interface_surface"
    DOCUMENT = "document"
    MANIFEST = "manifest"


class ErectionStatus(str, enum.Enum):
    """Outcome of a project erection attempt."""

    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass(frozen=True)
class AcceptedScaffold(CognitiveObject):
    """Immutable wrapper indicating a ScaffoldSpec has been externally accepted.

    The erector never creates acceptance.
    The erector only consumes acceptance evidence supplied by governance.
    """

    scaffold: Any = None
    acceptance_reference: str = ""
    accepted_by: str = ""
    accepted_at: str = ""
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(
            source_type=SourceType.DETERMINISTIC_RULE
        )
    )

    def __init__(
        self,
        scaffold: Any = None,
        acceptance_reference: str = "",
        accepted_by: str = "",
        accepted_at: str = "",
        provenance: ProvenanceRecord | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "id", generate_entity_id())
        object.__setattr__(self, "schema_version", SCHEMA_VERSION_V1)
        object.__setattr__(self, "created_at", current_utc_timestamp())
        object.__setattr__(self, "scaffold", scaffold)
        object.__setattr__(self, "acceptance_reference", str(acceptance_reference))
        object.__setattr__(self, "accepted_by", str(accepted_by))
        object.__setattr__(self, "accepted_at", str(accepted_at))

        prov = provenance or ProvenanceRecord(
            source_type=SourceType.DETERMINISTIC_RULE,
            producer_id="accepted_scaffold_builder",
            is_deterministic=True,
        )
        object.__setattr__(self, "provenance", prov)
        object.__setattr__(self, "metadata", dict(metadata or {}))


@dataclass(frozen=True)
class GeneratedArtifact(CognitiveObject):
    """Immutable description of a generated project artifact."""

    artifact_id: str = ""
    relative_path: str = ""
    artifact_type: str = ""
    content_checksum: str = ""
    source_reference: str = ""
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(
            source_type=SourceType.DETERMINISTIC_RULE
        )
    )

    def __init__(
        self,
        artifact_id: str = "",
        relative_path: str = "",
        artifact_type: str = "",
        content_checksum: str = "",
        source_reference: str = "",
        provenance: ProvenanceRecord | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "id", generate_entity_id())
        object.__setattr__(self, "schema_version", SCHEMA_VERSION_V1)
        object.__setattr__(self, "created_at", current_utc_timestamp())

        object.__setattr__(self, "artifact_id", str(artifact_id))
        object.__setattr__(self, "relative_path", str(relative_path))
        object.__setattr__(self, "artifact_type", str(artifact_type))
        object.__setattr__(self, "content_checksum", str(content_checksum))
        object.__setattr__(self, "source_reference", str(source_reference))

        prov = provenance or ProvenanceRecord(
            source_type=SourceType.DETERMINISTIC_RULE,
            producer_id="generated_artifact_builder",
            is_deterministic=True,
        )
        object.__setattr__(self, "provenance", prov)
        object.__setattr__(self, "metadata", dict(metadata or {}))


@dataclass(frozen=True)
class ErectionResult(CognitiveObject):
    """Immutable result of a project erection attempt."""

    erection_id: str = ""
    scaffold_id: str = ""
    target_directory: str = ""
    status: str = ErectionStatus.FAILED.value
    generated_artifacts: tuple[GeneratedArtifact, ...] = ()
    findings: tuple[str, ...] = ()
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(
            source_type=SourceType.DETERMINISTIC_RULE
        )
    )

    def __init__(
        self,
        erection_id: str = "",
        scaffold_id: str = "",
        target_directory: str = "",
        status: str = ErectionStatus.FAILED.value,
        generated_artifacts: Sequence[GeneratedArtifact] = (),
        findings: Sequence[str] = (),
        provenance: ProvenanceRecord | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "id", generate_entity_id())
        object.__setattr__(self, "schema_version", SCHEMA_VERSION_V1)
        object.__setattr__(self, "created_at", current_utc_timestamp())

        object.__setattr__(self, "erection_id", str(erection_id))
        object.__setattr__(self, "scaffold_id", str(scaffold_id))
        object.__setattr__(self, "target_directory", str(target_directory))
        object.__setattr__(self, "status", str(status))
        object.__setattr__(self, "generated_artifacts", tuple(generated_artifacts))
        object.__setattr__(self, "findings", tuple(findings))

        prov = provenance or ProvenanceRecord(
            source_type=SourceType.DETERMINISTIC_RULE,
            producer_id="erection_result_builder",
            is_deterministic=True,
        )
        object.__setattr__(self, "provenance", prov)
        object.__setattr__(self, "metadata", dict(metadata or {}))
