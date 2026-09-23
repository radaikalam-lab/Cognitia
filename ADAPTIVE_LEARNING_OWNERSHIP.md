# Cognitia Adaptive Learning - Subsystem Ownership & Architectural Boundary

## 1. Executive Summary

Cognitia is the **sole authoritative owner** of the Adaptive Learning subsystem, ML provider abstractions, model registry, evaluation engine, learning curves, drift detection, learning history, and persistence integration.

Host applications (Lean Thorium, Frappe, AcoustiForge, AstraForge, FJH applications, and robotic control systems) are **consumers** that interact exclusively through the Cognitia HTTP Gateway and Canonical Cognitive ABI. Host applications must never implement, duplicate, or alter Cognitia learning semantics.

---

## 2. Global Architecture & Ownership Diagram

```text
                                     COGNITIA
                                        │
        ┌───────────────────────────────┼───────────────────────────────┐
        │                               │                               │
   Epistemic Core                Adaptive Learning                   Runtime
    (E0.5 – E10)                    Layer (AL0)                      Gateway
   Deterministic                        │                        /v1/learning/*
        │                        ┌──────┴──────┐                        │
        │                      Laya        future ML                    │
        │                    Provider      Providers                    │
        │                                                               │
        └───────────────────────────────┬───────────────────────────────┘
                                        │
                                   Persistence
                               (FilePersistence P1)
                                        │
                                        ▼
                                 Cognitia ABI/API
                                        ▲
                                        │ (HTTP / Named Pipe / JSONL)
                                 Thorium Adapter
                                        │
                                        ▼
                                   Lean Thorium
```

---

## 3. Ownership Invariants

| Component / Subsystem | Authoritative Owner | Consumer / Role | Authority Model |
|---|---|---|---|
| **AdaptiveLearningProvider Contract** | Cognitia | None (Frozen Contract) | `NONE` |
| **Model Registry & Metadata** | Cognitia | Host Applications (Query only) | `NONE` |
| **Representation Boundary** | Cognitia | Host Applications (Data source) | `NONE` |
| **Laya Reference Provider** | Cognitia (`learning.laya_provider`) | Host Applications (Advisory consumer) | `NONE` |
| **Model Evaluation Engine** | Cognitia | Domain human reviewer | `NONE` |
| **Drift Monitoring** | Cognitia | Domain human reviewer | `NONE` |
| **Learning Curves & History** | Cognitia | Host Applications (Advisory telemetry) | `NONE` |
| **Durable Learning Persistence** | Cognitia (`FilePersistenceService`) | Host Applications (Zero local learning storage) | `NONE` |
| **Browser Observations** | Lean Thorium | Cognitia (Ingestion target) | `NONE` |
| **Content Filtering & Privacy** | Lean Thorium | Host local enforcement | Host-local |

---

## 4. Fundamental Rules

1. **Epistemic Novelty $
eq$ Production Authority**: All adaptive learning results carry `authority = "NONE"`. Host applications cannot execute system commands or alter operational states merely because a learning model suggested a candidate.
2. **Adaptive Learning $
eq$ Epistemic Truth**: Model predictions are advisory `AdaptiveLearningResult` instances. The Epistemic Core evaluates whether any result warrants promotion to `Evidence`.
3. **No Direct Host-to-Provider Bypasses**: Host applications must never communicate directly with `Laya` or ML runtimes. All interactions flow through the canonical `Cognitia Gateway` -> `RepresentationAdapter` -> `AdaptiveLearningService` -> `Provider`.
4. **No Heavyweight ML Stacks in Host Applications**: Host applications remain lightweight and free of PyTorch, TensorFlow, ONNX, or model weight files.
5. **Durable Auditable Persistence**: All learning events, predictions, learning curve trajectories, model comparisons, and drift reports are stored in Cognitia's append-only journal (`FilePersistenceService`) and survive restarts.
