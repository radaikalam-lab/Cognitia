# Cognitia Adaptive Learning - Provenance & Auditability

## 1. End-to-End Lineage Chain

Every adaptive learning result produces a complete, deterministic provenance chain:

```text
Model Record (calibration checksum, version, provider)
       ↓
Input Representation (version 1.0.0, sanitized reference)
       ↓
Inference Execution (parameters, random seed)
       ↓
AdaptiveLearningResult (epistemic status = UNRESOLVED, authority = NONE)
       ↓
Event Journal (JournalRecord with SHA-256 hash chaining)
```

## 2. Reproducibility & Determinism

- When configured with `is_deterministic = True` and a fixed random seed, identical inputs yield bit-for-bit identical decision outputs and confidence scores.
- Non-deterministic inference modes are explicitly flagged with `is_deterministic = False` in the `ProvenanceRecord`.
- Model records preserve calibration checksums (`SHA-256`) to ensure weights and configurations are verifiable.
