"""Cognitia Experience Module.

Defines the domain-neutral experience schema connecting consuming applications
with cognitive services across single-agent, multi-agent, and swarm topologies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from cognitia.abi.types import (
    SCHEMA_VERSION_V1,
    Action,
    CognitiveObject,
    Observation,
    Outcome,
)
from cognitia.provenance.record import ProvenanceRecord, SourceType


@dataclass(frozen=True)
class ExperienceRecord(CognitiveObject):
    """Domain-neutral episodic record capturing operational interaction."""

    source_application: str = "generic_application"
    source_node: str = "primary_node"
    agent_id: str = "agent_0"
    environment_id: str = "default_environment"
    episode_id: str = "episode_0"
    observation: Observation = field(default_factory=Observation)
    action: Action = field(default_factory=Action)
    expected_outcome: Outcome | None = None
    actual_outcome: Outcome | None = None
    model_version: str | None = None
    cognitive_library_version: str = "0.1.0"
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(source_type=SourceType.SENSOR)
    )


class ExperienceBuilder:
    """Builder utility for creating structured ExperienceRecords."""

    def __init__(self, source_application: str, episode_id: str) -> None:
        self._source_application = source_application
        self._episode_id = episode_id
        self._source_node = "default_node"
        self._agent_id = "agent_0"
        self._environment_id = "default_env"
        self._observation = Observation()
        self._action = Action()
        self._expected_outcome: Outcome | None = None
        self._actual_outcome: Outcome | None = None
        self._model_version: str | None = None
        self._cognitive_library_version = "0.1.0"
        self._provenance: ProvenanceRecord | None = None
        self._metadata: dict[str, Any] = {}

    def with_node(self, source_node: str) -> ExperienceBuilder:
        self._source_node = source_node
        return self

    def with_agent(self, agent_id: str) -> ExperienceBuilder:
        self._agent_id = agent_id
        return self

    def with_environment(self, environment_id: str) -> ExperienceBuilder:
        self._environment_id = environment_id
        return self

    def with_observation(self, observation: Observation) -> ExperienceBuilder:
        self._observation = observation
        return self

    def with_action(self, action: Action) -> ExperienceBuilder:
        self._action = action
        return self

    def with_expected_outcome(self, outcome: Outcome) -> ExperienceBuilder:
        self._expected_outcome = outcome
        return self

    def with_actual_outcome(self, outcome: Outcome) -> ExperienceBuilder:
        self._actual_outcome = outcome
        return self

    def with_model_version(self, model_version: str) -> ExperienceBuilder:
        self._model_version = model_version
        return self

    def with_provenance(self, provenance: ProvenanceRecord) -> ExperienceBuilder:
        self._provenance = provenance
        return self

    def with_metadata(self, key: str, value: Any) -> ExperienceBuilder:
        self._metadata[key] = value
        return self

    def build(self) -> ExperienceRecord:
        prov = self._provenance or ProvenanceRecord(
            source_type=SourceType.SENSOR,
            producer_id=f"{self._source_application}:{self._agent_id}",
            model_version=self._model_version,
        )
        return ExperienceRecord(
            source_application=self._source_application,
            source_node=self._source_node,
            agent_id=self._agent_id,
            environment_id=self._environment_id,
            episode_id=self._episode_id,
            observation=self._observation,
            action=self._action,
            expected_outcome=self._expected_outcome,
            actual_outcome=self._actual_outcome,
            model_version=self._model_version,
            cognitive_library_version=self._cognitive_library_version,
            provenance=prov,
            metadata=dict(self._metadata),
        )
