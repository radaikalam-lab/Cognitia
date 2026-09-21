"""Cognitia Provider Gateway.

Provides execution authorization for advanced reasoning providers.
The Gateway enforces lifecycle, capability, resource, and snapshot-boundary checks.
It does NOT perform epistemic evaluation — that is an explicit downstream step.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from cognitia.providers.registry import AdvancedProviderRegistry
from cognitia.providers.types import (
    AdvancedCapabilityType,
    AdvancedProviderRecord,
    CandidateReasoningArtifact,
    ProviderLifecycleStatus,
    ReasoningRequest,
    ResourceRequirements,
)
from cognitia.reasoning.types import ReasoningInput


class ProviderExecutionError(Exception):
    """Raised when provider execution is rejected by the Gateway."""

    def __init__(self, reason: str, provider_id: str = "", provider_version: str = "") -> None:
        self.reason = reason
        self.provider_id = provider_id
        self.provider_version = provider_version
        super().__init__(f"Provider execution rejected [{provider_id}:{provider_version}]: {reason}")


class GatewayCheckResult:
    """Deterministic result of a single Gateway authorization check."""

    def __init__(self, check_name: str, passed: bool, detail: str = "") -> None:
        self.check_name = check_name
        self.passed = passed
        self.detail = detail

    def __repr__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return f"GatewayCheckResult({self.check_name}={status}, detail={self.detail!r})"


@runtime_checkable
class ProviderGateway(Protocol):
    """Protocol governing provider execution authorization."""

    def authorize(
        self,
        provider_id: str,
        provider_version: str,
        request: ReasoningRequest,
        input_snapshot: ReasoningInput,
    ) -> tuple[bool, list[GatewayCheckResult]]:
        ...

    def execute(
        self,
        provider: Any,
        request: ReasoningRequest,
        input_snapshot: ReasoningInput,
    ) -> CandidateReasoningArtifact:
        ...


class InMemoryProviderGateway:
    """Thread-safe reference implementation of ProviderGateway.

    Enforces:
    - provider existence
    - version existence
    - lifecycle == ENABLED
    - requested capability is declared by provider
    - resource requirements are satisfied
    - reasoning input is valid
    - input snapshot is immutable (ReasoningInput enforces this)
    """

    def __init__(
        self,
        provider_registry: AdvancedProviderRegistry,
        available_resources: dict[str, bool] | None = None,
    ) -> None:
        self._provider_registry = provider_registry
        self._available_resources = available_resources or {
            "network": False,
            "gpu": False,
            "external_runtime": False,
            "filesystem": False,
        }

    def _check_provider_exists(
        self,
        provider_id: str,
        provider_version: str,
    ) -> GatewayCheckResult:
        record = self._provider_registry.get(provider_id, provider_version)
        if record is None:
            return GatewayCheckResult(
                check_name="provider_exists",
                passed=False,
                detail=f"Provider '{provider_id}' version '{provider_version}' not registered",
            )
        return GatewayCheckResult(
            check_name="provider_exists",
            passed=True,
            detail=f"Provider '{provider_id}:{provider_version}' found",
        )

    def _check_lifecycle_enabled(
        self,
        record: AdvancedProviderRecord,
    ) -> GatewayCheckResult:
        if record.lifecycle_status != ProviderLifecycleStatus.ENABLED:
            return GatewayCheckResult(
                check_name="lifecycle_enabled",
                passed=False,
                detail=(
                    f"Provider status is '{record.lifecycle_status.value}', "
                    f"must be '{ProviderLifecycleStatus.ENABLED.value}'"
                ),
            )
        return GatewayCheckResult(
            check_name="lifecycle_enabled",
            passed=True,
            detail=f"Status = {record.lifecycle_status.value}",
        )

    def _check_capability_supported(
        self,
        record: AdvancedProviderRecord,
        requested_capability: AdvancedCapabilityType,
    ) -> GatewayCheckResult:
        if requested_capability not in record.capability_types:
            return GatewayCheckResult(
                check_name="capability_supported",
                passed=False,
                detail=(
                    f"Provider declares {[c.value for c in record.capability_types]}; "
                    f"requested '{requested_capability.value}'"
                ),
            )
        return GatewayCheckResult(
            check_name="capability_supported",
            passed=True,
            detail=f"Capability '{requested_capability.value}' is supported",
        )

    def _check_resources_satisfied(
        self,
        resources: ResourceRequirements,
    ) -> GatewayCheckResult:
        if resources.requires_network and not self._available_resources.get("network", False):
            return GatewayCheckResult(
                check_name="resources_satisfied",
                passed=False,
                detail="requires_network=True but network is unavailable",
            )
        if resources.requires_gpu and not self._available_resources.get("gpu", False):
            return GatewayCheckResult(
                check_name="resources_satisfied",
                passed=False,
                detail="requires_gpu=True but GPU is unavailable",
            )
        if resources.requires_external_runtime and not self._available_resources.get(
            "external_runtime", False
        ):
            return GatewayCheckResult(
                check_name="resources_satisfied",
                passed=False,
                detail="requires_external_runtime=True but external runtime is unavailable",
            )
        if resources.requires_filesystem and not self._available_resources.get(
            "filesystem", False
        ):
            return GatewayCheckResult(
                check_name="resources_satisfied",
                passed=False,
                detail="requires_filesystem=True but filesystem is unavailable",
            )
        return GatewayCheckResult(
            check_name="resources_satisfied",
            passed=True,
            detail="All declared resource requirements are satisfied",
        )

    def _check_input_snapshot_valid(
        self,
        request: ReasoningRequest,
        input_snapshot: ReasoningInput,
    ) -> GatewayCheckResult:
        if request.input_snapshot_id != input_snapshot.context_id:
            return GatewayCheckResult(
                check_name="input_snapshot_valid",
                passed=False,
                detail=(
                    f"request.input_snapshot_id='{request.input_snapshot_id}' "
                    f"does not match input_snapshot.context_id='{input_snapshot.context_id}'"
                ),
            )
        return GatewayCheckResult(
            check_name="input_snapshot_valid",
            passed=True,
            detail="Input snapshot ID matches request",
        )

    def authorize(
        self,
        provider_id: str,
        provider_version: str,
        request: ReasoningRequest,
        input_snapshot: ReasoningInput,
    ) -> tuple[bool, list[GatewayCheckResult]]:
        """Run all authorization checks without executing the provider.

        Returns (authorized: bool, checks: list[GatewayCheckResult]).
        """
        checks: list[GatewayCheckResult] = []

        exist_check = self._check_provider_exists(provider_id, provider_version)
        checks.append(exist_check)
        if not exist_check.passed:
            return False, checks

        record = self._provider_registry.get(provider_id, provider_version)
        assert record is not None

        enabled_check = self._check_lifecycle_enabled(record)
        checks.append(enabled_check)
        if not enabled_check.passed:
            return False, checks

        cap_check = self._check_capability_supported(record, request.requested_capability)
        checks.append(cap_check)
        if not cap_check.passed:
            return False, checks

        res_check = self._check_resources_satisfied(record.resources)
        checks.append(res_check)
        if not res_check.passed:
            return False, checks

        snap_check = self._check_input_snapshot_valid(request, input_snapshot)
        checks.append(snap_check)
        if not snap_check.passed:
            return False, checks

        return True, checks

    def execute(
        self,
        provider: Any,
        request: ReasoningRequest,
        input_snapshot: ReasoningInput,
    ) -> CandidateReasoningArtifact:
        """Authorize and execute a provider.

        Raises ProviderExecutionError if any authorization check fails.
        The provider must expose provider_id and provider_version attributes.
        """
        provider_id = getattr(provider, "provider_id", "")
        provider_version = getattr(provider, "provider_version", "")

        authorized, checks = self.authorize(provider_id, provider_version, request, input_snapshot)

        if not authorized:
            failed_checks = [c for c in checks if not c.passed]
            primary = failed_checks[0] if failed_checks else checks[0]
            raise ProviderExecutionError(
                reason=primary.detail,
                provider_id=provider_id,
                provider_version=provider_version,
            )

        return provider.reason(request, input_snapshot)
