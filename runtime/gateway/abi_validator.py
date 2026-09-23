"""Canonical Cognitive ABI v1.0.0 Validator."""

from __future__ import annotations

import datetime
import re
import uuid
from typing import Any

UUID4_REGEX = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
HEX32_TOKEN_REGEX = re.compile(r"^[0-9A-Fa-f]{32}$")

MAX_ALLOWED_PAYLOAD_BYTES = 512 * 1024  # 512 KB


class ABIValidationError(ValueError):
    """Raised when an incoming message fails Canonical ABI v1.0.0 validation."""


class ABIValidator:
    """Validates raw dictionaries against Cognitia Cognitive ABI v1.0.0 rules."""

    @staticmethod
    def is_valid_uuid(val: str) -> bool:
        if not isinstance(val, str):
            return False
        if UUID4_REGEX.match(val):
            return True
        if HEX32_TOKEN_REGEX.match(val):
            return True
        try:
            uuid.UUID(val)
            return True
        except ValueError:
            return False

    @staticmethod
    def is_valid_iso_timestamp(ts: str) -> bool:
        if not isinstance(ts, str):
            return False
        try:
            # Supports ISO-8601 with Z or offset
            clean_ts = ts.replace("Z", "+00:00")
            datetime.datetime.fromisoformat(clean_ts)
            return True
        except ValueError:
            return False

    @classmethod
    def validate_observation_dict(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Validate an observation dictionary against the Canonical ABI."""
        if not isinstance(data, dict):
            raise ABIValidationError("Message root must be a JSON object")

        # 1. Identity Check
        entity_id = data.get("id")
        if not entity_id or not cls.is_valid_uuid(entity_id):
            raise ABIValidationError(f"Invalid entity ID: {entity_id}. Must be valid UUID/token.")

        # 2. Schema Version Check
        schema_version = data.get("schema_version")
        if not schema_version:
            raise ABIValidationError("Missing 'schema_version'")
        if not schema_version.startswith("1."):
            raise ABIValidationError(
                f"Incompatible schema_version: {schema_version}. Gateway requires 1.x.x"
            )

        # 3. Timestamp Check
        created_at = data.get("created_at")
        if not created_at or not cls.is_valid_iso_timestamp(created_at):
            raise ABIValidationError(
                f"Invalid 'created_at' timestamp: {created_at}. Must be ISO-8601 UTC."
            )

        # 4. Source ID Check
        source_id = data.get("source_id")
        if not source_id or not isinstance(source_id, str):
            raise ABIValidationError("Missing or invalid 'source_id'")

        # 5. Payload Check
        payload = data.get("payload")
        if payload is None or not isinstance(payload, dict):
            raise ABIValidationError("Missing or invalid 'payload' dictionary")

        return data
