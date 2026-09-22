"""Cognitia Phase 10: Integrated Cognitive Loop Types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from cognitia.abi.types import CognitiveObject, current_utc_timestamp, generate_entity_id


@dataclass(frozen=True)
class CognitiveLoopResult(CognitiveObject):
    """Immutable result of a single cognitive loop execution.

    Encapsulates the identities of all produced artifacts and the
    reconstructable provenance chain. Does not represent execution
    authority or domain action.
    """

    observation_id: str = ""
    experience_id: str = ""
    reasoning_trace_id: str = ""
    proposal_id: str | None = None
    decision_id: str | None = None
    document_id: str | None = None
    provenance_chain: tuple[str, ...] = ()
    loop_id: str = "deterministic_cognitive_loop"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __init__(
        self,
        observation_id: str = "",
        experience_id: str = "",
        reasoning_trace_id: str = "",
        proposal_id: str | None = None,
        decision_id: str | None = None,
        document_id: str | None = None,
        provenance_chain: tuple[str, ...] | None = None,
        loop_id: str = "deterministic_cognitive_loop",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "id", generate_entity_id())
        object.__setattr__(self, "schema_version", "1.0.0")
        object.__setattr__(self, "created_at", current_utc_timestamp())
        object.__setattr__(self, "observation_id", str(observation_id))
        object.__setattr__(self, "experience_id", str(experience_id))
        object.__setattr__(self, "reasoning_trace_id", str(reasoning_trace_id))
        object.__setattr__(self, "proposal_id", proposal_id)
        object.__setattr__(self, "decision_id", decision_id)
        object.__setattr__(self, "document_id", document_id)
        object.__setattr__(self, "provenance_chain", tuple(provenance_chain or ()))
        object.__setattr__(self, "loop_id", str(loop_id))
        object.__setattr__(self, "metadata", dict(metadata or {}))

