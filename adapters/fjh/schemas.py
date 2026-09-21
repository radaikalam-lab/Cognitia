"""Flash Joule Heating (FJH) Schema Validation.

Provides deterministic validation for FJH experiment parameters,
measurements, and derived metrics without external dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


FJH_SCHEMA_VERSION: str = "1.0.0"


@dataclass(frozen=True)
class FJHRequestSchema:
    """Validation schema for REQUESTED stage parameters."""

    required_fields: tuple[str, ...] = (
        "voltage_V",
        "capacitance_uF",
        "precursor_type",
        "sample_mass_g",
    )
    optional_fields: tuple[str, ...] = (
        "chamber_id",
        "electrode_material",
        "atmosphere",
        "pressure_torr",
        "notes",
    )

    @classmethod
    def validate(cls, payload: dict[str, Any]) -> dict[str, Any]:
        """Validate request payload and return normalized form."""
        errors: list[str] = []
        for field_name in cls.required_fields:
            if field_name not in payload:
                errors.append(f"Missing required field: {field_name}")

        if errors:
            raise ValueError(f"FJH request validation failed: {'; '.join(errors)}")

        normalized = dict(payload)
        normalized["schema_version"] = FJH_SCHEMA_VERSION
        normalized["validation_status"] = "valid"
        return normalized


@dataclass(frozen=True)
class FJHMeasurementSchema:
    """Validation schema for MEASURED stage sensor data."""

    required_fields: tuple[str, ...] = (
        "voltage_waveform",
        "current_waveform",
    )
    optional_fields: tuple[str, ...] = (
        "temperature_estimate_K",
        "optical_emission_spectrum",
        "duration_us",
        "peak_power_W",
        "chamber_pressure_torr",
        "video_frame_indices",
    )

    @classmethod
    def validate(cls, payload: dict[str, Any]) -> dict[str, Any]:
        """Validate measurement payload and return normalized form."""
        errors: list[str] = []
        for field_name in cls.required_fields:
            if field_name not in payload:
                errors.append(f"Missing required field: {field_name}")

        if errors:
            raise ValueError(f"FJH measurement validation failed: {'; '.join(errors)}")

        normalized = dict(payload)
        normalized["schema_version"] = FJH_SCHEMA_VERSION
        normalized["validation_status"] = "valid"
        return normalized


@dataclass(frozen=True)
class FJHDerivedMetricSchema:
    """Validation schema for DERIVED stage computed metrics."""

    required_fields: tuple[str, ...] = (
        "resistivity_ohm_cm",
        "heating_rate_K_per_s",
    )
    optional_fields: tuple[str, ...] = (
        "cooling_rate_K_per_s",
        "conversion_efficiency",
        "yield_percent",
        "graphene_quality_score",
        "specific_surface_area_m2_per_g",
    )

    @classmethod
    def validate(cls, payload: dict[str, Any]) -> dict[str, Any]:
        """Validate derived metric payload and return normalized form."""
        errors: list[str] = []
        for field_name in cls.required_fields:
            if field_name not in payload:
                errors.append(f"Missing required field: {field_name}")

        if errors:
            raise ValueError(f"FJH derived metric validation failed: {'; '.join(errors)}")

        normalized = dict(payload)
        normalized["schema_version"] = FJH_SCHEMA_VERSION
        normalized["validation_status"] = "valid"
        return normalized
