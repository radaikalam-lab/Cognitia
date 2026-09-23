"""Representation Boundary Adapter for Adaptive Learning.

Translates canonical Cognitia objects (Observation, Evidence, DirectionalSpecification,
etc.) into sanitized, versioned ModelInputRepresentation instances.
Enforces security boundaries by isolating prompt-injection, execution directives,
and credentials.
"""

from __future__ import annotations

import re
from typing import Any

from cognitia.abi.types import CognitiveObject, Observation
from cognitia.directional.types import DirectionalSpecification
from cognitia.epistemic.types import Evidence
from cognitia.learning.contract import ModelInputRepresentation


DANGEROUS_DIRECTIVE_PATTERNS = [
    re.compile(r"\b(exec|eval|os\.system|subprocess|import\s+os|import\s+sys)\b", re.IGNORECASE),
    re.compile(r"\b(rm\s+-rf|del\s+/f|powershell|cmd\.exe|/bin/sh|/bin/bash)\b", re.IGNORECASE),
    re.compile(r"\b(bearer\s+[a-zA-Z0-9_\-\.]+|ghp_[a-zA-Z0-9]+|sk-[a-zA-Z0-9]{20,})\b", re.IGNORECASE),
    re.compile(r"\b(set-cookie:|authorization:|password=|secret=)\b", re.IGNORECASE),
]


class RepresentationAdapter:
    """Adapts and sanitizes Cognitia domain objects into model representations."""

    DEFAULT_VERSION = "1.0.0"

    @classmethod
    def sanitize_content(cls, raw: str) -> tuple[str, list[str]]:
        """Sanitize raw text payload, redacting potential execution directives or credentials.
        
        Returns:
            (sanitized_text, list_of_detected_threats)
        """
        if not raw:
            return "", []

        sanitized = raw
        detected: list[str] = []

        for pattern in DANGEROUS_DIRECTIVE_PATTERNS:
            matches = pattern.findall(sanitized)
            if matches:
                detected.extend([str(m) for m in matches])
                sanitized = pattern.sub("[REDACTED_SECURITY_PAYLOAD]", sanitized)

        return sanitized, detected

    @classmethod
    def adapt_observation(
        cls,
        obs: Observation,
        version: str = DEFAULT_VERSION,
        extract_features: bool = True,
    ) -> ModelInputRepresentation:
        """Convert a canonical Observation into a ModelInputRepresentation."""
        raw_text = ""
        features: dict[str, Any] = {}
        sanitized_payload: dict[str, Any] = {}

        if isinstance(obs.payload, dict):
            for k, v in obs.payload.items():
                if isinstance(v, (int, float)):
                    features[k] = float(v)
                elif isinstance(v, str):
                    clean_str, _ = cls.sanitize_content(v)
                    sanitized_payload[k] = clean_str
                    raw_text += f"{k}: {clean_str}\n"
                elif isinstance(v, (list, tuple)) and all(isinstance(x, (int, float)) for x in v):
                    features[k] = [float(x) for x in v]
                else:
                    sanitized_payload[k] = str(v)
        elif isinstance(obs.payload, str):
            clean_str, _ = cls.sanitize_content(obs.payload)
            raw_text = clean_str
            sanitized_payload["raw"] = clean_str

        return ModelInputRepresentation(
            representation_version=version,
            input_type="observation",
            source_reference=f"obs:{obs.id}:{obs.source_id}",
            features=features,
            sanitized_text=raw_text.strip(),
            sanitized_payload=sanitized_payload,
            provenance_reference=obs.id,
            is_trusted=False,
        )

    @classmethod
    def adapt_evidence(
        cls,
        ev: Evidence,
        version: str = DEFAULT_VERSION,
    ) -> ModelInputRepresentation:
        """Convert a canonical Evidence item into a ModelInputRepresentation."""
        features: dict[str, Any] = {
            "confidence": float(ev.confidence),
            "epistemic_weight": float(getattr(ev, "weight", 1.0)),
        }
        if hasattr(ev, "metadata") and isinstance(ev.metadata, dict):
            for k, v in ev.metadata.items():
                if isinstance(v, (int, float)):
                    features[k] = float(v)

        clean_text, _ = cls.sanitize_content(f"Evidence target={ev.target_id} direction={ev.direction}")

        return ModelInputRepresentation(
            representation_version=version,
            input_type="evidence",
            source_reference=f"ev:{ev.id}:{ev.target_id}",
            features=features,
            sanitized_text=clean_text,
            sanitized_payload={"target_id": ev.target_id, "metadata": getattr(ev, "metadata", {})},
            provenance_reference=ev.id,
            is_trusted=True,
        )

    @classmethod
    def adapt_directional_spec(
        cls,
        spec: DirectionalSpecification,
        version: str = DEFAULT_VERSION,
    ) -> ModelInputRepresentation:
        """Convert a DirectionalSpecification into a ModelInputRepresentation."""
        obj_strs = [str(o) for o in getattr(spec, "objectives", ())]
        cons_strs = [str(c) for c in getattr(spec, "constraints", ())]
        crit_strs = [str(s) for s in getattr(spec, "success_criteria", ())]

        clean_obj, _ = cls.sanitize_content("; ".join(obj_strs))
        clean_cons, _ = cls.sanitize_content("; ".join(cons_strs))

        features: dict[str, Any] = {
            "objective_count": len(obj_strs),
            "constraint_count": len(cons_strs),
            "criteria_count": len(crit_strs),
        }

        return ModelInputRepresentation(
            representation_version=version,
            input_type="directional_specification",
            source_reference=f"spec:{spec.id}",
            features=features,
            sanitized_text=f"Objectives: {clean_obj} | Constraints: {clean_cons}",
            sanitized_payload={
                "objectives": obj_strs,
                "constraints": cons_strs,
                "success_criteria": crit_strs,
            },
            provenance_reference=spec.id,
            is_trusted=True,
        )

    @classmethod
    def adapt_raw(
        cls,
        raw_payload: dict[str, Any],
        source_id: str = "raw_input",
        version: str = DEFAULT_VERSION,
    ) -> ModelInputRepresentation:
        """Adapt a general payload into a ModelInputRepresentation with strict sanitization."""
        features: dict[str, Any] = {}
        sanitized_payload: dict[str, Any] = {}
        raw_text_parts: list[str] = []

        for k, v in raw_payload.items():
            if isinstance(v, (int, float)):
                features[k] = float(v)
            elif isinstance(v, str):
                clean_v, _ = cls.sanitize_content(v)
                sanitized_payload[k] = clean_v
                raw_text_parts.append(f"{k}: {clean_v}")
            elif isinstance(v, (list, tuple)) and all(isinstance(x, (int, float)) for x in v):
                features[k] = [float(x) for x in v]
            else:
                sanitized_payload[k] = str(v)

        return ModelInputRepresentation(
            representation_version=version,
            input_type="raw_payload",
            source_reference=source_id,
            features=features,
            sanitized_text="; ".join(raw_text_parts),
            sanitized_payload=sanitized_payload,
            provenance_reference=source_id,
            is_trusted=False,
        )
