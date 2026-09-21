"""Cognitia Cognitive Attention Data Types and Schemas.

Defines domain-neutral structures for cognitive attention queries, explainable attention items,
deterministic attention results, and attention reasons.
All attention structures use deeply immutable primitives (tuples and frozen dataclasses).
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Mapping

from cognitia.abi.types import (
    CognitiveObject,
    SCHEMA_VERSION_V1,
    current_utc_timestamp,
    generate_entity_id,
)
from cognitia.epistemic.types import EpistemicStatus
from cognitia.provenance.record import ProvenanceRecord, SourceType


class AttentionReason(str, enum.Enum):
    """Enumeration of why an item received cognitive attention."""

    REFERENCE_ITEM = "reference_item"
    TASK_MATCH = "task_match"
    SUBJECT_MATCH = "subject_match"
    TEMPORAL_PROXIMITY = "temporal_proximity"
    EPISODE_RELEVANCE = "episode_relevance"
    SOURCE_RELEVANCE = "source_relevance"
    EPISTEMIC_RELEVANCE = "epistemic_relevance"
    RULE_RELEVANCE = "rule_relevance"
    MEMORY_RELEVANCE = "memory_relevance"
    EXPLICIT_SELECTION = "explicit_selection"


@dataclass(frozen=True)
class AttentionQuery:
    """Lightweight immutable specification for focusing attention over a Cognitive Context.
    
    INVARIANT: AttentionQuery is NOT a general-purpose goal or planning engine.
    It specifies deterministic task-oriented filters and budget limits for cognitive focus.
    """

    task_id: str = "default_task"
    task_type: str = "general_focus"
    focus_subject_ids: tuple[str, ...] = ()
    requested_item_types: tuple[str, ...] = ()
    maximum_items: int = 5
    minimum_score: float = 0.0
    target_epistemic_statuses: tuple[EpistemicStatus, ...] = ()
    scope: str | None = None
    parameters: tuple[tuple[str, Any], ...] = ()

    def __init__(
        self,
        task_id: str = "default_task",
        task_type: str = "general_focus",
        focus_subject_ids: tuple[str, ...] | list[str] = (),
        requested_item_types: tuple[str, ...] | list[str] = (),
        maximum_items: int = 5,
        minimum_score: float = 0.0,
        target_epistemic_statuses: tuple[EpistemicStatus, ...] | list[EpistemicStatus] = (),
        scope: str | None = None,
        parameters: Mapping[str, Any] | tuple[tuple[str, Any], ...] | None = None,
    ) -> None:
        object.__setattr__(self, "task_id", str(task_id))
        object.__setattr__(self, "task_type", str(task_type))
        object.__setattr__(self, "focus_subject_ids", tuple(focus_subject_ids))
        object.__setattr__(self, "requested_item_types", tuple(requested_item_types))
        object.__setattr__(self, "maximum_items", max(1, int(maximum_items)))
        object.__setattr__(self, "minimum_score", float(minimum_score))
        object.__setattr__(self, "target_epistemic_statuses", tuple(target_epistemic_statuses))
        object.__setattr__(self, "scope", scope)
        if parameters is None:
            params_tuple: tuple[tuple[str, Any], ...] = ()
        elif isinstance(parameters, Mapping):
            params_tuple = tuple(parameters.items())
        else:
            params_tuple = tuple(parameters)
        object.__setattr__(self, "parameters", params_tuple)

    @property
    def parameters_dict(self) -> dict[str, Any]:
        """Convenience dictionary mapping parameters key to value."""
        return dict(self.parameters)


@dataclass(frozen=True)
class AttentionItem:
    """Auditable immutable reference to a focused item from Cognitive Context.
    
    INVARIANT: attention_score is strictly a deterministic prioritization value.
    It is NOT confidence, probability, truth, epistemic certainty, or causal strength.
    """

    item_id: str
    rank: int
    attention_score: float
    source_context_item_id: str
    selection_reasons: tuple[AttentionReason, ...]
    epistemic_status: EpistemicStatus | None = None
    metadata: tuple[tuple[str, Any], ...] = ()

    def __init__(
        self,
        item_id: str,
        rank: int,
        attention_score: float,
        source_context_item_id: str,
        selection_reasons: tuple[AttentionReason, ...] | list[AttentionReason],
        epistemic_status: EpistemicStatus | None = None,
        metadata: Mapping[str, Any] | tuple[tuple[str, Any], ...] | None = None,
    ) -> None:
        object.__setattr__(self, "item_id", str(item_id))
        object.__setattr__(self, "rank", int(rank))
        object.__setattr__(self, "attention_score", round(float(attention_score), 6))
        object.__setattr__(self, "source_context_item_id", str(source_context_item_id))
        object.__setattr__(self, "selection_reasons", tuple(selection_reasons))
        object.__setattr__(self, "epistemic_status", epistemic_status)
        if metadata is None:
            meta_tuple: tuple[tuple[str, Any], ...] = ()
        elif isinstance(metadata, Mapping):
            meta_tuple = tuple(metadata.items())
        else:
            meta_tuple = tuple(metadata)
        object.__setattr__(self, "metadata", meta_tuple)

    @property
    def metadata_dict(self) -> dict[str, Any]:
        """Convenience dictionary mapping metadata key to value."""
        return dict(self.metadata)


@dataclass(frozen=True)
class AttentionResult(CognitiveObject):
    """Immutable snapshot containing the focused and ranked attention items over a CognitiveContext.
    
    INVARIANTS:
    1. Attention prioritizes context; it does NOT duplicate Context, Persistence, or Memory.
    2. Attention snapshots are deeply immutable once generated.
    3. Attention does NOT infer causality, execute rules, generate decisions, or resolve contradictions.
    """

    reference_observation_id: str = ""
    context_id: str = ""
    task_id: str = "default_task"
    task_type: str = "general_focus"
    selected_item_ids: tuple[str, ...] = ()
    attention_items: tuple[AttentionItem, ...] = ()
    budget_limit: int = 5
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(
            source_type=SourceType.COMPOSITE,
            producer_id="deterministic_attention_engine",
            is_deterministic=True,
        )
    )

    def get_item(self, item_id: str) -> AttentionItem | None:
        """Find an attention item by its item_id."""
        for item in self.attention_items:
            if item.item_id == item_id:
                return item
        return None
