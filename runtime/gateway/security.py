"""Security filters, rate limiters, and payload sanitizers for Cognitia Standalone Runtime."""

from __future__ import annotations

import re
import threading
import time
from dataclasses import dataclass, field
from typing import Any


class SecurityValidationError(ValueError):
    """Raised when an incoming request violates security constraints."""


# Sensitive key pattern: Only matches exact dictionary keys, not substring in natural text
SENSITIVE_KEY_PATTERN = re.compile(
    r"^(password|passwd|api_key|apikey|secret|access_token|refresh_token|cookie|set-cookie|authorization|auth_token)$",
    re.IGNORECASE,
)

# Prohibited execution keys that imply autonomous command execution
PROHIBITED_EXECUTION_KEYS = {
    "command",
    "cmd",
    "execute",
    "exec",
    "shell",
    "powershell",
    "subprocess",
    "spawn_process",
    "system",
    "eval",
    "os_system",
    "run_command",
}

# Regex to detect embedded credentials in URLs (e.g., https://user:password@example.com)
EMBEDDED_URL_CREDENTIAL_REGEX = re.compile(
    r"^https?://[a-zA-Z0-9_\-\.]+:[^@\s]+@[a-zA-Z0-9_\-\.]+",
    re.IGNORECASE,
)


@dataclass
class RateLimiter:
    """Thread-safe sliding window rate limiter per provider with memory bounding."""

    max_requests_per_minute: int = 600
    _history: dict[str, list[float]] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _max_tracked_providers: int = 1000

    def check_rate_limit(self, provider_id: str) -> bool:
        now = time.time()
        window_start = now - 60.0

        with self._lock:
            # Periodic cleanup of expired providers if tracker gets large
            if len(self._history) > self._max_tracked_providers:
                self._prune_expired(window_start)

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

    def _prune_expired(self, window_start: float) -> None:
        to_delete = [
            pid
            for pid, timestamps in self._history.items()
            if not timestamps or timestamps[-1] <= window_start
        ]
        for pid in to_delete:
            del self._history[pid]


class SecuritySanitizer:
    """Sanitizes incoming payloads to enforce untrusted data boundaries and prevent leaks."""

    @classmethod
    def sanitize_observation_payload(
        cls, payload: dict[str, Any], provider_id: str
    ) -> dict[str, Any]:
        """Ensures untrusted external data (e.g. from web/browser) is safely tagged

        and stripped of prohibited control directives or credential leakage.
        """
        if not isinstance(payload, dict):
            raise SecurityValidationError("Payload must be a dictionary")

        # 1. Scan for prohibited execution directives and structured credential keys
        cls._scan_payload_recursively(payload)

        # 2. Tag external provider content as untrusted data
        if (
            provider_id.startswith("thorium.")
            or "content" in payload
            or "html" in payload
            or "extracted_text" in payload
        ):
            payload["is_untrusted_external_content"] = True

        return payload

    @classmethod
    def _scan_payload_recursively(cls, obj: Any, depth: int = 0) -> None:
        if depth > 10:
            raise SecurityValidationError("Payload exceeds maximum nesting depth (10)")

        if isinstance(obj, dict):
            for k, v in obj.items():
                key_str = str(k).strip()
                lower_key = key_str.lower()

                # Execution directive rejection
                if lower_key in PROHIBITED_EXECUTION_KEYS:
                    raise SecurityValidationError(
                        f"Prohibited execution directive detected in key: '{key_str}'"
                    )

                # Credential key detection (exact structural match)
                if SENSITIVE_KEY_PATTERN.match(lower_key):
                    raise SecurityValidationError(
                        f"Prohibited sensitive credential/token key detected: '{key_str}'"
                    )

                # Check string values for embedded URL credentials (e.g., http://user:pass@host)
                if isinstance(v, str) and EMBEDDED_URL_CREDENTIAL_REGEX.search(v):
                    raise SecurityValidationError(
                        "Embedded URL credentials detected in payload value"
                    )

                cls._scan_payload_recursively(v, depth + 1)
        elif isinstance(obj, list):
            for item in obj:
                cls._scan_payload_recursively(item, depth + 1)