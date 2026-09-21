"""Cognitia Plasticity Operator Registry.

Provides versioned registration, lifecycle tracking, and deterministic retrieval
of plasticity operators. Reuses the registry pattern established by the
Advanced Provider layer.
"""

from __future__ import annotations

import threading
from typing import Protocol, runtime_checkable

from cognitia.memory.types import OperatorLifecycleStatus, OperatorRecord


@runtime_checkable
class PlasticityOperatorRegistry(Protocol):
    """Protocol governing plasticity operator registration and lifecycle states."""

    def register(self, record: OperatorRecord) -> None: ...
    def get(self, operator_id: str, version: str | None = None) -> OperatorRecord | None: ...
    def list_operators(
        self,
        status: OperatorLifecycleStatus | None = None,
        operator_type: str | None = None,
    ) -> list[OperatorRecord]: ...
    def list_versions(self, operator_id: str) -> list[OperatorRecord]: ...
    def set_lifecycle_status(
        self,
        operator_id: str,
        version: str,
        status: OperatorLifecycleStatus,
    ) -> None: ...
    def is_enabled(self, operator_id: str, version: str | None = None) -> bool: ...


class InMemoryPlasticityOperatorRegistry:
    """Thread-safe in-memory reference implementation of PlasticityOperatorRegistry."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._operators: dict[tuple[str, str], OperatorRecord] = {}
        self._history: dict[str, list[str]] = {}

    def register(self, record: OperatorRecord) -> None:
        with self._lock:
            key = (record.operator_id, record.operator_version)
            if key in self._operators:
                raise ValueError(
                    f"Operator '{record.operator_id}' version '{record.operator_version}' is already registered and immutable"
                )
            self._operators[key] = record
            if record.operator_id not in self._history:
                self._history[record.operator_id] = []
            self._history[record.operator_id].append(record.operator_version)

    def get(self, operator_id: str, version: str | None = None) -> OperatorRecord | None:
        with self._lock:
            if version is not None:
                return self._operators.get((operator_id, version))
            versions = self._history.get(operator_id, [])
            if not versions:
                return None
            latest_version = versions[-1]
            return self._operators.get((operator_id, latest_version))

    def list_versions(self, operator_id: str) -> list[OperatorRecord]:
        with self._lock:
            versions = self._history.get(operator_id, [])
            return [
                self._operators[(operator_id, v)]
                for v in versions
                if (operator_id, v) in self._operators
            ]

    def list_operators(
        self,
        status: OperatorLifecycleStatus | None = None,
        operator_type: str | None = None,
    ) -> list[OperatorRecord]:
        with self._lock:
            results: list[OperatorRecord] = []
            for record in self._operators.values():
                if status is not None and record.lifecycle_status != status:
                    continue
                if operator_type is not None and record.operator_type != operator_type:
                    continue
                results.append(record)
            return sorted(results, key=lambda r: (r.operator_id, r.operator_version))

    def set_lifecycle_status(
        self,
        operator_id: str,
        version: str,
        status: OperatorLifecycleStatus,
    ) -> None:
        with self._lock:
            key = (operator_id, version)
            existing = self._operators.get(key)
            if not existing:
                raise KeyError(f"Operator '{operator_id}' version '{version}' not found")

            updated = OperatorRecord(
                operator_id=existing.operator_id,
                operator_version=existing.operator_version,
                operator_type=existing.operator_type,
                is_deterministic=existing.is_deterministic,
                registered_at=existing.registered_at,
                provenance=existing.provenance,
                lifecycle_status=status,
            )
            self._operators[key] = updated

    def is_enabled(self, operator_id: str, version: str | None = None) -> bool:
        record = self.get(operator_id, version)
        if not record:
            return False
        return record.lifecycle_status == OperatorLifecycleStatus.ENABLED
