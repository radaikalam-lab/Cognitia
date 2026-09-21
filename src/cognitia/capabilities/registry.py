"""Cognitia Capability Registry."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from cognitia.capabilities.base import BaseCapability, CapabilityType


@runtime_checkable
class CapabilityRegistry(Protocol):
    """Protocol for capability registration and discovery."""

    def register(self, capability: BaseCapability) -> None: ...
    def get(self, capability_id: str) -> BaseCapability | None: ...
    def list_by_type(self, capability_type: CapabilityType) -> list[BaseCapability]: ...
    def list_all(self) -> list[BaseCapability]: ...


class InMemoryCapabilityRegistry:
    """Thread-safe in-memory registry of cognitive capability providers."""

    def __init__(self) -> None:
        self._capabilities: dict[str, BaseCapability] = {}

    def register(self, capability: BaseCapability) -> None:
        cap_id = capability.descriptor.capability_id
        self._capabilities[cap_id] = capability

    def get(self, capability_id: str) -> BaseCapability | None:
        return self._capabilities.get(capability_id)

    def list_by_type(self, capability_type: CapabilityType) -> list[BaseCapability]:
        return [
            cap
            for cap in self._capabilities.values()
            if cap.descriptor.capability_type == capability_type
        ]

    def list_all(self) -> list[BaseCapability]:
        return list(self._capabilities.values())
