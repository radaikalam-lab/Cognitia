"""Cognitia Dynamic Cognitive Document Diff.

Defines structural change explanations between document versions.
Changes are descriptive only; they never express epistemic judgment.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Sequence

from cognitia.abi.types import (
    CognitiveObject,
    SCHEMA_VERSION_V1,
    current_utc_timestamp,
    generate_entity_id,
)
from cognitia.provenance.record import ProvenanceRecord, SourceType


class ChangeType(str, enum.Enum):
    """Categories of structural document changes."""

    ADDED = "added"
    REMOVED = "removed"
    CHANGED = "changed"
    UNCHANGED = "unchanged"


@dataclass(frozen=True)
class ChangeEntry:
    """Single structural change between document versions."""

    change_type: ChangeType = ChangeType.UNCHANGED
    path: str = ""
    old_value: Any | None = None
    new_value: Any | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __init__(
        self,
        change_type: ChangeType | str = ChangeType.UNCHANGED,
        path: str = "",
        old_value: Any | None = None,
        new_value: Any | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if isinstance(change_type, str):
            change_type = ChangeType(change_type)
        object.__setattr__(self, "change_type", change_type)
        object.__setattr__(self, "path", str(path))
        object.__setattr__(self, "old_value", old_value)
        object.__setattr__(self, "new_value", new_value)
        object.__setattr__(self, "metadata", dict(metadata or {}))


@dataclass(frozen=True)
class DocumentChange(CognitiveObject):
    """Structured explanation of changes between two document versions."""

    change_id: str = field(default_factory=generate_entity_id)
    document_id: str = ""
    from_version: str = ""
    to_version: str = ""
    changes: tuple[ChangeEntry, ...] = ()
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(source_type=SourceType.DETERMINISTIC_RULE)
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    def __init__(
        self,
        document_id: str = "",
        from_version: str = "",
        to_version: str = "",
        changes: Sequence[ChangeEntry] | None = None,
        provenance: ProvenanceRecord | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "change_id", generate_entity_id())
        object.__setattr__(self, "schema_version", SCHEMA_VERSION_V1)
        object.__setattr__(self, "created_at", current_utc_timestamp())
        object.__setattr__(self, "document_id", str(document_id))
        object.__setattr__(self, "from_version", str(from_version))
        object.__setattr__(self, "to_version", str(to_version))
        object.__setattr__(self, "changes", tuple(changes or ()))
        prov = provenance or ProvenanceRecord(
            source_type=SourceType.DETERMINISTIC_RULE,
            producer_id="document_change_builder",
            is_deterministic=True,
        )
        object.__setattr__(self, "provenance", prov)
        object.__setattr__(self, "metadata", dict(metadata or {}))
