"""Canonical Cognitive ABI v1.0.0 and Runtime Validation for Cognitia.

Separates Canonical ABI Semantic Invariants from Runtime Transport Limits.
"""

from __future__ import annotations

import datetime
import re
import uuid
from typing import Any

# Canonical ABI Invariant: Globally Unique Identifier MUST be valid UUIDv4
UUID4_REGEX = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)

MAX_ALLOWED_PAYLOAD_BYTES = 512 * 1024  # 512 KB Transport Limit
MAX_NESTING_DEPTH = 10
MAX_KEY_COUNT = 500
MAX_ARRAY_LENGTH = 1000
MAX_STRING_LENGTH = 256 * 1024  # 256 KB max single string


class ABIValidationError(ValueError):
    """Raised when an incoming message violates Canonical ABI v1.0.0 rules."""


class RuntimeValidationError(ValueError):
    """Raised when an incoming message violates Runtime transport or size limits."""


class ABIValidator:
    """Validates raw dictionaries against Cognitia Cognitive ABI v1.0.0 and runtime limits."""

    @staticmethod
    def is_valid_uuid4(val: str) -> bool:
        if not isinstance(val, str):
            return False
        return bool(UUID4_REGEX.match(val))

    @staticmethod
    def is_valid_iso_timestamp(ts: str) -> bool:
        if not isinstance(ts, str):
            return False
        try:
            clean_ts = ts.replace("Z", "+00:00")
            dt = datetime.datetime.fromisoformat(clean_ts)
            return dt.tzinfo is not None
        except ValueError:
            return False

    @classmethod
    def validate_observation_dict(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Validate an observation dictionary against Canonical ABI 1.0.0 and runtime limits."""
        if not isinstance(data, dict):
            raise ABIValidationError("Message root must be a JSON object")

        # 1. Canonical ABI Identity: Canonical UUIDv4
        entity_id = data.get("id")
        if not entity_id or not cls.is_valid_uuid4(entity_id):
            raise ABIValidationError(
                f"Invalid entity ID: '{entity_id}'. Canonical ABI requires UUIDv4."
            )

        # 2. Canonical ABI Schema Version: Must be SemVer 1.x.x
        schema_version = data.get("schema_version")
        if not schema_version or not isinstance(schema_version, str):
            raise ABIValidationError("Missing or invalid 'schema_version'")
        if not schema_version.startswith("1."):
            raise ABIValidationError(
                f"Incompatible schema_version: '{schema_version}'. Canonical ABI requires 1.x.x"
            )

        # 3. Canonical ABI Timestamp: UTC ISO-8601
        created_at = data.get("created_at")
        if not created_at or not cls.is_valid_iso_timestamp(created_at):
            raise ABIValidationError(
                f"Invalid 'created_at' timestamp: '{created_at}'. Canonical ABI requires ISO-8601 UTC."
            )

        # 4. Canonical ABI Source ID
        source_id = data.get("source_id")
        if not source_id or not isinstance(source_id, str):
            raise ABIValidationError("Missing or invalid 'source_id'")

        # 5. Canonical ABI Payload
        payload = data.get("payload")
        if payload is None or not isinstance(payload, dict):
            raise ABIValidationError("Missing or invalid 'payload' dictionary")

        # 6. Runtime Boundary Validation (Resource Protection)
        cls._validate_resource_limits(data, depth=0)

        return data

    @classmethod
    def validate_evidence_dict(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Validate an evidence dictionary against Canonical Epistemic Contract 1.0.0."""
        if not isinstance(data, dict):
            raise ABIValidationError("Evidence root must be a JSON object")

        # 1. Identity
        entity_id = data.get("id")
        if not entity_id or not cls.is_valid_uuid4(entity_id):
            raise ABIValidationError(
                f"Invalid evidence ID: '{entity_id}'. Canonical ABI requires UUIDv4."
            )

        # 2. Schema Version
        schema_version = data.get("schema_version")
        if not schema_version or not schema_version.startswith("1."):
            raise ABIValidationError(
                f"Incompatible schema_version: '{schema_version}'. Required: 1.x.x"
            )

        # 3. Timestamp
        created_at = data.get("created_at")
        if not created_at or not cls.is_valid_iso_timestamp(created_at):
            raise ABIValidationError(f"Invalid created_at: '{created_at}'")

        # 4. Target ID
        target_id = data.get("target_id")
        if not target_id or not isinstance(target_id, str):
            raise ABIValidationError("Missing or invalid 'target_id'")

        # 5. Direction: SUPPORT, REFUTE, NEUTRAL
        direction = data.get("direction", "SUPPORT").upper()
        if direction not in ("SUPPORT", "REFUTE", "NEUTRAL"):
            raise ABIValidationError(f"Invalid evidence direction: '{direction}'")

        # 6. Confidence: [0.0, 1.0]
        confidence = data.get("confidence", 1.0)
        if not isinstance(confidence, (int, float)) or not (0.0 <= confidence <= 1.0):
            raise ABIValidationError(f"Confidence must be in range [0.0, 1.0], got {confidence}")

        cls._validate_resource_limits(data, depth=0)
        return data

    @classmethod
    def validate_directional_spec_dict(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Validate a directional specification dictionary against Canonical Contract 1.0.0."""
        if not isinstance(data, dict):
            raise ABIValidationError("DirectionalSpecification root must be a JSON object")

        # 1. Identity
        entity_id = data.get("id")
        if not entity_id or not cls.is_valid_uuid4(entity_id):
            raise ABIValidationError(
                f"Invalid specification ID: '{entity_id}'. Canonical ABI requires UUIDv4."
            )

        # 2. Schema Version
        schema_version = data.get("schema_version")
        if not schema_version or not schema_version.startswith("1."):
            raise ABIValidationError(
                f"Incompatible schema_version: '{schema_version}'. Required: 1.x.x"
            )

        # 3. Timestamp
        created_at = data.get("created_at")
        if not created_at or not cls.is_valid_iso_timestamp(created_at):
            raise ABIValidationError(f"Invalid created_at: '{created_at}'")

        # 4. Objectives tuple/list
        objectives = data.get("objectives")
        if not isinstance(objectives, list) or len(objectives) == 0:
            raise ABIValidationError("DirectionalSpecification requires at least one objective")

        cls._validate_resource_limits(data, depth=0)
        return data

    @classmethod
    def _validate_resource_limits(cls, obj: Any, depth: int) -> None:
        if depth > MAX_NESTING_DEPTH:
            raise RuntimeValidationError(
                f"Payload exceeds maximum nesting depth ({MAX_NESTING_DEPTH})"
            )

        if isinstance(obj, dict):
            if len(obj) > MAX_KEY_COUNT:
                raise RuntimeValidationError(
                    f"Object exceeds maximum key count ({MAX_KEY_COUNT})"
                )
            for k, v in obj.items():
                if len(str(k)) > 1024:
                    raise RuntimeValidationError("Key name exceeds maximum length (1024 chars)")
                cls._validate_resource_limits(v, depth + 1)
        elif isinstance(obj, list):
            if len(obj) > MAX_ARRAY_LENGTH:
                raise RuntimeValidationError(
                    f"Array exceeds maximum length ({MAX_ARRAY_LENGTH})"
                )
            for item in obj:
                cls._validate_resource_limits(item, depth + 1)
        elif isinstance(obj, str):
            if len(obj) > MAX_STRING_LENGTH:
                raise RuntimeValidationError(
                    f"String exceeds maximum length ({MAX_STRING_LENGTH} bytes)"
                )

    @classmethod
    def validate_learning_predict_dict(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Validate an adaptive learning prediction request against schema and transport limits."""
        if not isinstance(data, dict):
            raise ABIValidationError("Message root must be a JSON object")

        model_id = data.get("model_id")
        if not model_id or not isinstance(model_id, str):
            raise ABIValidationError("Field 'model_id' must be a non-empty string")

        task = data.get("task", "classification")
        if not isinstance(task, str):
            raise ABIValidationError("Field 'task' must be a string")

        payload = data.get("payload")
        if payload is None:
            raise ABIValidationError("Field 'payload' is required for prediction")

        cls._validate_resource_limits(data, 0)
        return data

    @classmethod
    def validate_learning_evaluate_dict(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Validate an adaptive learning evaluation request."""
        if not isinstance(data, dict):
            raise ABIValidationError("Message root must be a JSON object")

        model_id = data.get("model_id")
        if not model_id or not isinstance(model_id, str):
            raise ABIValidationError("Field 'model_id' must be a non-empty string")

        dataset = data.get("dataset")
        if not isinstance(dataset, list):
            raise ABIValidationError("Field 'dataset' must be a list of evaluation samples")

        cls._validate_resource_limits(data, 0)
        return data

    @classmethod
    def validate_learning_compare_dict(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Validate an adaptive learning model comparison request."""
        if not isinstance(data, dict):
            raise ABIValidationError("Message root must be a JSON object")

        models = data.get("models")
        if not isinstance(models, list) or len(models) < 2:
            raise ABIValidationError("Field 'models' must be a list of at least 2 candidate model tuples [model_id, version]")

        dataset = data.get("dataset")
        if not isinstance(dataset, list):
            raise ABIValidationError("Field 'dataset' must be a list of evaluation samples")

        cls._validate_resource_limits(data, 0)
        return data
