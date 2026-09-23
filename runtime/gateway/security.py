"""Security filters, rate limiters, and payload sanitizers for Cognitia Gateway."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any


class SecurityValidationError(ValueError):
    """Raised when an incoming request violates security constraints."""


# Sensitive key pattern to detect accidental credential/token leakage in payload
SENSITIVE_KEY_PATTERN = re.compile(
    r"^(password|passwd|secret|api_key|token|access_token|refresh_token|cookie|set-cookie|authorization)$",
    re.IGNORECASE,
)


@dataclass
class RateLimiter:
    """In-memory sliding window rate limiter per provider."""

    max_requests_per_minute: int = 600
    _history: dict[str, list[float]] = field(default_factory=dict)

    def check_rate_limit(self, provider_id: str) -> bool:
        now = time.time()
        window_start = now - 60.0

        if provider_id not in self._history:
            self._history[provider_id] = [now]
            return True

        # Purge timestamps older than 60s
        self._history[provider_id] = [
            t for t in self._history[provider_id] if t > window_start
        ]

        if len(self._history[provider_id]) >= self.max_requests_per_minute:
            return False

        self._history[provider_id].append(now)
        return True


class SecuritySanitizer:
    """Sanitizes incoming payloads to enforce untrusted data boundaries."""

    @classmethod
    def sanitize_observation_payload(
        cls, payload: dict[str, Any], provider_id: str
    ) -> dict[str, Any]:
        """Ensures untrusted external data (e.g. from web/browser) is safely tagged

        and stripped of prohibited control semantics or credential leakage.
        """
        if not isinstance(payload, dict):
            raise SecurityValidationError("Payload must be a dictionary")

        # Scan for prohibited keys or sensitive leaks
        cls._scan_for_sensitive_leakage(payload)

        # Enforce that all content payloads are strictly data, not execution directives
        if "execute" in payload or "exec" in payload or "command" in payload:
            raise SecurityValidationError(
                "Prohibited execution directive found in observation payload"
            )

        # If it's a browser provider with content, enforce untrusted tag
        if provider_id.startswith("thorium.") or "content" in payload or "html" in payload:
            payload["is_untrusted_external_content"] = True

        return payload

    @classmethod
    def _scan_for_sensitive_leakage(cls, obj: Any, depth: int = 0) -> None:
        if depth > 10:
            raise SecurityValidationError("Payload exceeds maximum nesting depth (10)")

        if isinstance(obj, dict):
            for k, v in obj.items():
                if SENSITIVE_KEY_PATTERN.match(str(k)):
                    raise SecurityValidationError(
                        f"Prohibited sensitive credential/token key detected: '{k}'"
                    )
                cls._scan_for_sensitive_leakage(v, depth + 1)
        elif isinstance(obj, list):
            for item in obj:
                cls._scan_for_sensitive_leakage(item, depth + 1)