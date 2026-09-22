"""Cognitia Dynamic Cognitive Document Intent.

Defines human-requested document changes as structured intents.
Intents are validated and translated into canonical artifacts or specifications;
they never mutate hidden document state or grant authority.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Sequence

from cognitia.abi.types import (
    SCHEMA_VERSION_V1,
    current_utc_timestamp,
    generate_entity_id,
)
from cognitia.provenance.record import ProvenanceRecord, SourceType


class IntentType(str, enum.Enum):
    """Categories of human-requested document intents."""

    ADD_REFERENCE = "add_reference"
    REMOVE_REFERENCE = "remove_reference"
    CHANGE_SECTION = "change_section"
    CHANGE_FILTER = "change_filter"
    CHANGE_ORDER = "change_order"
    UPDATE_DIRECTION = "update_direction"
    ANNOTATE = "annotate"
    REQUEST_REFRESH = "request_refresh"
    REQUEST_PROJECTION = "request_projection"


@dataclass(frozen=True)
class DocumentIntent:
    """Structured representation of a human-requested document change."""

    intent_id: str = field(default_factory=generate_entity_id)
    document_id: str = ""
    intent_type: IntentType = IntentType.ANNOTATE
    parameters: tuple[tuple[str, Any], ...] = ()
    rationale: str | None = None
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(source_type=SourceType.HUMAN)
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    def __init__(
        self,
        document_id: str = "",
        intent_type: IntentType | str = IntentType.ANNOTATE,
        parameters: Sequence[tuple[str, Any]] | None = None,
        rationale: str | None = None,
        provenance: ProvenanceRecord | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "intent_id", generate_entity_id())
        object.__setattr__(self, "schema_version", SCHEMA_VERSION_V1)
        object.__setattr__(self, "created_at", current_utc_timestamp())
        object.__setattr__(self, "document_id", str(document_id))
        if isinstance(intent_type, str):
            intent_type = IntentType(intent_type)
        object.__setattr__(self, "intent_type", intent_type)
        object.__setattr__(self, "parameters", tuple(parameters or ()))
        object.__setattr__(self, "rationale", rationale)
        prov = provenance or ProvenanceRecord(
            source_type=SourceType.HUMAN,
            producer_id="document_intent_builder",
            is_deterministic=True,
        )
        object.__setattr__(self, "provenance", prov)
        object.__setattr__(self, "metadata", dict(metadata or {}))

    @property
    def parameters_dict(self) -> dict[str, Any]:
        return dict(self.parameters)
