# Laya Reference Learning Provider

## 1. Provider Identity

- **Provider ID**: `laya`
- **Version**: `1.0.0`
- **Role**: Local-first typed-decision learning provider for Cognitia.
- **Capabilities**: Classification, scoring, candidate ranking, confidence calibration, anomaly detection, directional candidate interpretation.
- **Runtime**: Offline, in-process, lightweight, CPU-efficient, zero external cloud dependencies.

## 2. Reference Inference Mode

```json
{
  "task": "classification",
  "decision": "resonance",
  "scores": {
    "resonance": 0.81,
    "harmonic": 0.11,
    "noise": 0.05,
    "measurement_error": 0.02,
    "unknown": 0.01
  },
  "confidence": 0.81,
  "authority": "NONE"
}
```

## 3. Performance Profile

- **Model Initialization**: ~0.036 ms
- **Cold Start Inference**: ~0.169 ms
- **Warm Inference Latency (p50)**: 0.0315 ms (31.5 µs)
- **Warm Inference Latency (p95)**: 0.0367 ms (36.7 µs)
- **Warm Inference Latency (p99)**: 0.0434 ms (43.4 µs)
- **Throughput**: >30,000 inferences/sec
- **Memory Footprint**: <100 KB
