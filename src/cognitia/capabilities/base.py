"""Cognitia Capability Base Types & Service Provider Interface (SPI)."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from cognitia.abi.types import (
    Action,
    Decision,
    Observation,
)
from cognitia.provenance.record import ProvenanceRecord, SourceType


class CapabilityType(str, enum.Enum):
    """Enumeration of standard capability types in Cognitia."""

    DECISION = "decision"
    REASONING = "reasoning"
    PLANNING = "planning"
    PREDICTION = "prediction"
    CLASSIFICATION = "classification"
    ANOMALY_DETECTION = "anomaly_detection"
    SIMULATION = "simulation"
    DYNAMIC_DOCUMENT = "dynamic_document"


@dataclass(frozen=True)
class CapabilityDescriptor:
    """Metadata describing a capability provider implementation."""

    capability_id: str
    capability_type: CapabilityType
    provider_name: str
    version: str = "1.0.0"
    input_schema_version: str = "1.0.0"
    output_schema_version: str = "1.0.0"
    is_deterministic: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class BaseCapability(Protocol):
    """Base protocol for all cognitive capabilities."""

    @property
    def descriptor(self) -> CapabilityDescriptor: ...


@runtime_checkable
class DecisionCapability(BaseCapability, Protocol):
    """Protocol for provider-agnostic decision capabilities producing cognitive proposals."""

    def propose_decision(
        self,
        observation: Observation,
        context: dict[str, Any] | None = None,
    ) -> Decision: ...


class DeterministicMockDecisionProvider:
    """Deterministic reference implementation of DecisionCapability."""

    def __init__(
        self,
        capability_id: str = "mock_decision_provider_v1",
        provider_name: str = "deterministic_rules",
        version: str = "1.0.0",
    ) -> None:
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
        # Generate an advisory cognitive proposal
        proposed_action = Action(
            name="noop_recommendation",
            parameters={"source_observation_id": observation.id},
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
            proposal_type="deterministic_policy_proposal",
            proposed_action=proposed_action,
            confidence=1.0,
            rationale="Deterministic rule matched observation state",
            provenance=prov,
            metadata={"context": context or {}},
        )
