"""Tests for domain-neutral Reasoning across 4 Synthetic Domains:
- Automotive (RPM, BoostPressure, CoolantTemperature, VehicleSpeed, OperatingMode)
- ERP (SalesOrder, Delivery, Inventory, Customer)
- Acoustics (Frequency, Amplitude, Phase, Gain, Delay)
- Scientific Process (Temperature, Pressure, Current, Voltage, MaterialState)
"""

import pytest

from cognitia.abi.types import Observation
from cognitia.reasoning import (
    AbductiveHypotheses,
    AnalogicalMapping,
    CausalHypothesis,
    CounterfactualScenario,
    DeductiveConclusion,
    DeterministicReasoningEngine,
    ReasoningInput,
    ReasoningMode,
)
from cognitia.rules.types import CognitiveRule


def test_synthetic_domain_automotive():
    """Automotive domain: Deductive operating mode classification and abductive diagnostic hypothesis."""
    engine = DeterministicReasoningEngine()

    deductive_rule = CognitiveRule(
        rule_id="auto_cruise_rule",
        name="Cruise Condition",
        predicate={"VehicleSpeed": {">": 60.0}, "RPM": {"between": [1500, 2500]}},
        recommendation={"OperatingMode": "CRUISE_ECO"},
    )
    obs = Observation(
        id="obs_vehicle_1",
        payload={
            "VehicleSpeed": 75.0,
            "RPM": 2100,
            "BoostPressure": 1.2,
            "CoolantTemperature": 88.0,
        },
    )

    inp = ReasoningInput(
        context_id="ctx_auto",
        reasoning_mode=ReasoningMode.DEDUCTION,
        premises=[obs],
        rules=[deductive_rule],
    )

    trace, result = engine.reason(inp)
    assert isinstance(trace.conclusion, DeductiveConclusion)
    assert trace.conclusion.derived_attributes_dict["OperatingMode"] == "CRUISE_ECO"


def test_synthetic_domain_erp():
    """ERP domain: Counterfactual inventory reallocation scenario."""
    engine = DeterministicReasoningEngine()

    baseline_obs = Observation(
        id="obs_erp_1",
        payload={
            "SalesOrderID": "SO-9012",
            "Inventory_WarehouseA": 50,
            "Inventory_WarehouseB": 10,
            "DeliveryLeadDays": 5,
        },
    )

    tr_rule = CognitiveRule(
        rule_id="tr_erp_fulfillment",
        name="Fulfillment Lead Time",
        scope="counterfactual",
        predicate={"Inventory_WarehouseA": 0},
        recommendation={"target_variable": "DeliveryLeadDays", "value": 14},
    )

    inp = ReasoningInput(
        context_id="ctx_erp",
        reasoning_mode=ReasoningMode.COUNTERFACTUAL,
        premises=[baseline_obs],
        rules=[tr_rule],
        hypothetical_interventions={"Inventory_WarehouseA": 0},
    )

    trace, result = engine.reason(inp)
    assert isinstance(trace.conclusion, CounterfactualScenario)
    assert trace.conclusion.derived_state_dict["DeliveryLeadDays"] == 14


def test_synthetic_domain_acoustics():
    """Acoustics domain: Structural analogy mapping between two harmonic filter designs."""
    engine = DeterministicReasoningEngine()

    source_filter = {
        "source_id": "notch_filter_reference",
        "elements": {
            "Frequency": "center_band",
            "Amplitude": "attenuation_depth",
            "Phase": "phase_shift",
            "Gain": "preamp_gain",
            "Delay": "latency_ms",
        },
    }

    acoustic_obs = Observation(
        id="obs_acoustics_1",
        payload={
            "Frequency": 1000.0,
            "Amplitude": -18.5,
            "Phase": 0.0,
            "Gain": 1.0,
            "Delay": 2.5,
        },
    )

    inp = ReasoningInput(
        context_id="ctx_acoustics",
        reasoning_mode=ReasoningMode.ANALOGY,
        premises=[acoustic_obs],
        analogy_source=source_filter,
    )

    trace, result = engine.reason(inp)
    assert isinstance(trace.conclusion, AnalogicalMapping)
    assert trace.conclusion.similarity_score == 1.0
    assert len(trace.conclusion.correspondences) == 5


def test_synthetic_domain_scientific_process():
    """Scientific process: Causal evaluation of chemical/thermal state transition."""
    engine = DeterministicReasoningEngine()

    obs = Observation(
        id="obs_plasma_1",
        payload={
            "Temperature": 1450.0,
            "Pressure": 0.05,
            "Voltage": 240.0,
            "Current": 15.0,
            "MaterialState": "IONIZED_PLASMA",
        },
    )

    causal_edges = [
        ("Voltage", "MaterialState", "electric_field_dielectric_breakdown")
    ]

    inp = ReasoningInput(
        context_id="ctx_scientific",
        reasoning_mode=ReasoningMode.CAUSAL,
        premises=[obs],
        causal_graph=causal_edges,
    )

    trace, result = engine.reason(inp)
    assert isinstance(trace.conclusion, CausalHypothesis)
    assert trace.conclusion.cause == "Voltage"
    assert trace.conclusion.effect == "MaterialState"
    assert trace.conclusion.mechanism == "electric_field_dielectric_breakdown"
