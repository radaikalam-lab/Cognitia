"""Cognitia Dynamic Document Capability Provider.

Defines the capability protocol and deterministic reference implementation
for dynamic cognitive document projection.
"""

from __future__ import annotations

from typing import Any

from cognitia.capabilities.base import (
    BaseCapability,
    CapabilityDescriptor,
    CapabilityType,
)
from cognitia.documents.projection import DeterministicDocumentProjection
from cognitia.documents.specification import DocumentSpecification
from cognitia.documents.types import DynamicDocument
from cognitia.memory.types import MemoryContext
from cognitia.provenance.record import ProvenanceRecord, SourceType


class DynamicDocumentCapability(BaseCapability):
    """Protocol for document projection capabilities."""

    def project(
        self,
        specification: DocumentSpecification,
        memory_context: MemoryContext | None = None,
        conflicts: list[Any] | None = None,
    ) -> DynamicDocument:
        """Project canonical state into a DynamicDocument."""
        ...


class DeterministicMockDocumentProvider:
    """Deterministic reference implementation of DynamicDocumentCapability."""

    def __init__(
        self,
        capability_id: str = "mock_document_provider_v1",
        provider_name: str = "deterministic_projection",
        version: str = "1.0.0",
    ) -> None:
        self._descriptor = CapabilityDescriptor(
            capability_id=capability_id,
            capability_type=CapabilityType.DYNAMIC_DOCUMENT,
            provider_name=provider_name,
            version=version,
            is_deterministic=True,
        )
        self._projection = DeterministicDocumentProjection(
            projection_id=f"{provider_name}:{capability_id}",
        )

    @property
    def descriptor(self) -> CapabilityDescriptor:
        return self._descriptor

    def project(
        self,
        specification: DocumentSpecification,
        memory_context: MemoryContext | None = None,
        conflicts: list[Any] | None = None,
    ) -> DynamicDocument:
        """Project canonical state into a DynamicDocument deterministically."""
        return self._projection.project(
            specification=specification,
            memory_context=memory_context,
            conflicts=conflicts,
        )
