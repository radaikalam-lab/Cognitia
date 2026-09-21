"""Cognitia Cognitive Service Facade and Subsystem Protocols.

Composes Epistemics, Experience, Reasoning, Capabilities, and Model Registry
into a unified advisory cognitive interface without domain coupling.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from cognitia.abi.types import Decision, Observation
from cognitia.capabilities.base import CapabilityType, DecisionCapability
from cognitia.capabilities.registry import CapabilityRegistry
from cognitia.epistemic.service import EpistemicService
from cognitia.experience.record import ExperienceRecord
from cognitia.models.registry import ModelRegistry
from cognitia.reasoning.capability import ReasoningCapability
from cognitia.reasoning.types import ReasoningMode, ReasoningTrace


@runtime_checkable
class ExperienceService(Protocol):
    """Protocol for recording and querying domain-neutral experience records."""

    def record_experience(self, experience: ExperienceRecord) -> None: ...
    def get_experience(self, experience_id: str) -> ExperienceRecord | None: ...
    def list_by_episode(self, episode_id: str) -> list[ExperienceRecord]: ...
    def list_by_agent(self, agent_id: str) -> list[ExperienceRecord]: ...
    def list_all(self) -> list[ExperienceRecord]: ...


class InMemoryExperienceService:
    """Thread-safe in-memory reference implementation of ExperienceService."""

    def __init__(self) -> None:
        self._experiences: dict[str, ExperienceRecord] = {}

    def record_experience(self, experience: ExperienceRecord) -> None:
        self._experiences[experience.id] = experience

    def get_experience(self, experience_id: str) -> ExperienceRecord | None:
        return self._experiences.get(experience_id)

    def list_by_episode(self, episode_id: str) -> list[ExperienceRecord]:
        return [
            exp for exp in self._experiences.values() if exp.episode_id == episode_id
        ]

    def list_by_agent(self, agent_id: str) -> list[ExperienceRecord]:
        return [exp for exp in self._experiences.values() if exp.agent_id == agent_id]

    def list_all(self) -> list[ExperienceRecord]:
        return list(self._experiences.values())


@runtime_checkable
class CognitiveService(Protocol):
    """Unified facade protocol exposing coordinated cognitive services."""

    @property
    def epistemics(self) -> EpistemicService: ...

    @property
    def experience(self) -> ExperienceService: ...

    @property
    def capabilities(self) -> CapabilityRegistry: ...

    @property
    def models(self) -> ModelRegistry: ...

    def request_decision(
        self,
        observation: Observation,
        capability_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> Decision: ...

    def request_reasoning(
        self,
        mode: ReasoningMode,
        premises: list[Any],
        capability_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> ReasoningTrace: ...
