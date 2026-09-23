"""Provider Registry and Capability Gating for Cognitia Gateway."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ProviderRecord:
    provider_id: str
    provider_name: str
    provider_version: str
    adapter_version: str
    supported_abi_versions: list[str]
    capabilities: list[str]
    authority_level: str = "NONE"
    transport: str = "local_http"
    allowed_content_types: list[str] = field(default_factory=list)


class ProviderRegistry:
    """Manages registered providers, capabilities, and authority boundaries."""

    def __init__(self, config_path: str | Path | None = None) -> None:
        self._providers: dict[str, ProviderRecord] = {}
        if config_path:
            self.load_from_file(config_path)

    def load_from_file(self, config_path: str | Path) -> None:
        path = Path(config_path)
        if not path.exists():
            return
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        for p in data.get("providers", []):
            record = ProviderRecord(
                provider_id=p["provider_id"],
                provider_name=p["provider_name"],
                provider_version=p["provider_version"],
                adapter_version=p["adapter_version"],
                supported_abi_versions=p.get("supported_abi_versions", ["1.0.0"]),
                capabilities=p.get("capabilities", []),
                authority_level=p.get("authority_level", "NONE"),
                transport=p.get("transport", "local_http"),
                allowed_content_types=p.get("allowed_content_types", []),
            )
            self._providers[record.provider_id] = record

    def register_provider(self, record: ProviderRecord) -> None:
        self._providers[record.provider_id] = record

    def get_provider(self, provider_id: str) -> ProviderRecord | None:
        return self._providers.get(provider_id)

    def is_registered(self, provider_id: str) -> bool:
        return provider_id in self._providers

    def validate_capability(self, provider_id: str, capability_id: str) -> bool:
        provider = self.get_provider(provider_id)
        if not provider:
            return False
        return capability_id in provider.capabilities

    def list_providers(self) -> list[dict[str, Any]]:
        return [
            {
                "provider_id": p.provider_id,
                "provider_name": p.provider_name,
                "provider_version": p.provider_version,
                "adapter_version": p.adapter_version,
                "capabilities": p.capabilities,
                "authority_level": p.authority_level,
            }
            for p in self._providers.values()
        ]