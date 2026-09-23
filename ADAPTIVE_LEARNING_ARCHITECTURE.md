# Cognitia Adaptive Learning Layer (AL0) - Architecture

## 1. Overview

The **Adaptive Learning Layer** introduces an auditable, decoupled machine learning provider architecture into Cognitia. It establishes a controlled interface for machine learning models to learn from observations, classify epistemic events, score candidate hypotheses, measure calibration, track learning curves, detect drift, and generate candidate interpretations for Directional Programming.

## 2. Fundamental Architectural Rules

1. **Epistemic Novelty $\neq$ Production Authority**
   - Every adaptive result carries `authority = "NONE"`.
   - Adaptive learning cannot trigger actuators, execute OS commands, mutate databases, or control hardware.
2. **Adaptive Learning $
eq$ Epistemic Truth**
   - Model outputs are advisory `AdaptiveLearningResult` instances, never automatically `Observation`, `Evidence`, or `Claim`.
   - The frozen Epistemic Subsystem (E0.5–E10) evaluates whether any learning result warrants promotion to evidence.
3. **Core Epistemic Semantics Remain Frozen**
   - No modifications to canonical objects (`Observation`, `Evidence`, `ProvenanceRecord`, `EpistemicNode`, `DirectionalProposal`).

## 3. Layer Architecture

```text
                        Cognitia Runtime
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
  HTTP Gateway            Epistemic Core         Adaptive Learning
  (/v1/learning/*)        (Deterministic)               │
                                                        ├── Provider Registry
                                                        ├── Model Registry
                                                        ├── Representation Boundary
                                                        ├── Laya Reference Provider
                                                        ├── Evaluation Engine
                                                        ├── Drift Detection
                                                        └── Learning History
                                                                │
                                                                ▼
                                                       File Persistence P1
```

## 4. Subsystem Components

- **`AdaptiveLearningProvider`**: Provider abstraction enabling pluggable ML backends (Laya reference provider, future TinyML, ONNX, and statistical providers).
- **`RepresentationAdapter`**: Enforces the representation boundary, stripping prompt injection vectors, shell commands, tokens, and credentials (`representation_version = "1.0.0"`).
- **`ModelRegistry`**: Versioned, immutable model catalog tracking model IDs, versions, provider identities, calibration checksums, and determinism.
- **`ModelEvaluationEngine`**: Computes task-specific metrics (accuracy, precision, recall, F1, Brier score), records learning curve points, and conducts multi-model competition without autonomous promotion.
- **`DriftDetector`**: Computes Population Stability Index (PSI) and metric degradation deltas, emitting advisory drift reports.
- **`FilePersistenceService` Integration**: Persists all learning events, predictions, learning curve points, model comparisons, and drift reports to the append-only journal and snapshots.
