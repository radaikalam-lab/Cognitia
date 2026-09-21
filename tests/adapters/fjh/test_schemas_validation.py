"""Tests for FJH Schema Validation."""

from __future__ import annotations

import pytest

from adapters.fjh.schemas import (
    FJHDerivedMetricSchema,
    FJHMeasurementSchema,
    FJHRequestSchema,
)


class TestFJHRequestSchema:
    """Validate REQUESTED stage parameter schemas."""

    def test_valid_request_passes(self) -> None:
        payload = {
            "voltage_V": 120.0,
            "capacitance_uF": 1000.0,
            "precursor_type": "graphite",
            "sample_mass_g": 0.05,
        }
        result = FJHRequestSchema.validate(payload)
        assert result["validation_status"] == "valid"
        assert result["schema_version"] == "1.0.0"
        assert result["voltage_V"] == 120.0

    def test_missing_voltage_raises(self) -> None:
        with pytest.raises(ValueError, match="Missing required field: voltage_V"):
            FJHRequestSchema.validate({"capacitance_uF": 1000.0, "precursor_type": "graphite"})

    def test_missing_capacitance_raises(self) -> None:
        with pytest.raises(ValueError, match="Missing required field: capacitance_uF"):
            FJHRequestSchema.validate({"voltage_V": 120.0, "precursor_type": "graphite"})

    def test_missing_precursor_type_raises(self) -> None:
        with pytest.raises(ValueError, match="Missing required field: precursor_type"):
            FJHRequestSchema.validate({"voltage_V": 120.0, "capacitance_uF": 1000.0})

    def test_missing_sample_mass_raises(self) -> None:
        with pytest.raises(ValueError, match="Missing required field: sample_mass_g"):
            FJHRequestSchema.validate(
                {"voltage_V": 120.0, "capacitance_uF": 1000.0, "precursor_type": "graphite"}
            )

    def test_optional_fields_preserved(self) -> None:
        payload = {
            "voltage_V": 120.0,
            "capacitance_uF": 1000.0,
            "precursor_type": "graphite",
            "sample_mass_g": 0.05,
            "electrode_material": "copper",
            "atmosphere": "argon",
            "notes": "high_quality_run",
        }
        result = FJHRequestSchema.validate(payload)
        assert result["electrode_material"] == "copper"
        assert result["atmosphere"] == "argon"
        assert result["notes"] == "high_quality_run"


class TestFJHMeasurementSchema:
    """Validate MEASURED stage sensor data schemas."""

    def test_valid_measurement_passes(self) -> None:
        payload = {
            "voltage_waveform": [0.0, 110.0, 120.0, 0.0],
            "current_waveform": [0.0, 700.0, 850.0, 0.0],
        }
        result = FJHMeasurementSchema.validate(payload)
        assert result["validation_status"] == "valid"
        assert result["schema_version"] == "1.0.0"

    def test_missing_voltage_waveform_raises(self) -> None:
        with pytest.raises(ValueError, match="Missing required field: voltage_waveform"):
            FJHMeasurementSchema.validate({"current_waveform": [0.0, 700.0]})

    def test_missing_current_waveform_raises(self) -> None:
        with pytest.raises(ValueError, match="Missing required field: current_waveform"):
            FJHMeasurementSchema.validate({"voltage_waveform": [0.0, 110.0]})

    def test_optional_fields_preserved(self) -> None:
        payload = {
            "voltage_waveform": [0.0, 110.0],
            "current_waveform": [0.0, 700.0],
            "temperature_estimate_K": 2800.0,
            "optical_emission_spectrum": {"532nm": 1200.0},
            "duration_us": 450.0,
        }
        result = FJHMeasurementSchema.validate(payload)
        assert result["temperature_estimate_K"] == 2800.0
        assert result["duration_us"] == 450.0
        assert result["optical_emission_spectrum"]["532nm"] == 1200.0


class TestFJHDerivedMetricSchema:
    """Validate DERIVED stage computed metric schemas."""

    def test_valid_derived_metric_passes(self) -> None:
        payload = {
            "resistivity_ohm_cm": 0.00035,
            "heating_rate_K_per_s": 5.6e6,
        }
        result = FJHDerivedMetricSchema.validate(payload)
        assert result["validation_status"] == "valid"
        assert result["schema_version"] == "1.0.0"

    def test_missing_resistivity_raises(self) -> None:
        with pytest.raises(ValueError, match="Missing required field: resistivity_ohm_cm"):
            FJHDerivedMetricSchema.validate({"heating_rate_K_per_s": 5.6e6})

    def test_missing_heating_rate_raises(self) -> None:
        with pytest.raises(ValueError, match="Missing required field: heating_rate_K_per_s"):
            FJHDerivedMetricSchema.validate({"resistivity_ohm_cm": 0.00035})

    def test_optional_fields_preserved(self) -> None:
        payload = {
            "resistivity_ohm_cm": 0.00035,
            "heating_rate_K_per_s": 5.6e6,
            "cooling_rate_K_per_s": 1.2e6,
            "conversion_efficiency": 0.85,
            "yield_percent": 92.0,
            "graphene_quality_score": 8.5,
        }
        result = FJHDerivedMetricSchema.validate(payload)
        assert result["cooling_rate_K_per_s"] == 1.2e6
        assert result["conversion_efficiency"] == pytest.approx(0.85)
        assert result["yield_percent"] == pytest.approx(92.0)
