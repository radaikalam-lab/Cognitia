# Cognitia Adaptive Learning AL3: Real Laya Provider Integration & Model Lifecycle Governance

## 1. Executive Summary & Epistemic Boundaries

Cognitia Adaptive Learning AL3 establishes:
1. **Forensic Laya Provider Audit & Explicit Boundary Integration**: Clear separation between `LayaSurrogateProvider` (`provider_type = "surrogate"`) and `RealLayaProvider` (`provider_type = "real"`). Real Laya models operate 100% offline and local-first with mandatory artifact directory inspection, weights/config/tokenizer verification, and SHA256 checksum enforcement. Missing artifacts or invalid environments fail closed with explicit diagnostic codes (`LAYA_MODEL_NOT_INSTALLED`, `LAYA_MODEL_ARTIFACT_MISSING`, `LAYA_CHECKSUM_MISMATCH`, `LAYA_CONFIGURATION_INVALID`) without silent fallback.
2. **Model Lifecycle Governance (AL3-B)**: A formal 9-state model lifecycle spanning `DISCOVERED` through `ARCHIVED`, ensuring strict active model immutability, zero autonomous execution authority (`authority = "NONE"`), auditable rollback proposals, external governance decision capture (`decision_source = "EXTERNAL"`, `cognitia_authority = "NONE"`), and runtime activation observation reconciliation (`record_activation_observation`).

---

## 2. Forensic Laya Integration Audit Summary

The forensic audit performed on the pre-AL3 codebase established the following facts:

```text
Cognitia AdaptiveLearningProvider interface:
    PRESENT and type-checked (src/cognitia/learning/contract.py)

Pre-AL3 Laya implementation:
    Deterministic surrogate/mock provider (LayaProvider)

Actual upstream Laya source repository:
    ABSENT from repository root and dependencies

Actual Laya Python package / wheel:
    ABSENT from virtual environment and pyproject.toml

Actual Laya weights / ONNX / safetensors:
    ABSENT from repository assets

Real Laya inference runtime:
    NOT IMPLEMENTED in prior baseline
```

### Architectural Remediation in AL3

1. **Surrogate Transparency**:
   - The deterministic reference provider is renamed to `LayaSurrogateProvider` with property `provider_type = "surrogate"`.
   - `LayaProvider` is retained solely as a backwards-compatible alias pointing to `LayaSurrogateProvider`.
2. **Real Laya Provider Boundary (`RealLayaProvider`)**:
   - Implemented in `src/cognitia/learning/laya_provider.py` as an `AdaptiveLearningProvider` implementation with `provider_type = "real"`.
   - Supports local-first execution via `LAYA_MODEL_DIR` or explicit paths.
   - Enforces physical existence of model weights (`model.onnx`, `model.safetensors`, `pytorch_model.bin`, `model_weights.bin`), configuration (`config.json`), tokenizer vocabularies (`tokenizer.json`, `vocab.txt`), and optional expected SHA256 hashes.
   - Prohibits runtime downloading or cloud dependency.
   - Fails explicitly on missing assets without falling back silently to surrogate mocks.

---

## 3. Model Lifecycle & Governance Architecture

### 3.1 Nine-State Lifecycle Model

```text
DISCOVERED
    ↓ (registered in domain registry)
REGISTERED
    ↓ (learning update / delta generated)
CANDIDATE
    ↓ (evaluated against test dataset)
EVALUATED
    ↓ (promotion proposed to human/host)
PROPOSED
    ↓ (external authority approval recorded)
APPROVED (runtime_activation_state = NOT_ACTIVE)
    ↓ (external domain host activates model; Cognitia observes activation)
ACTIVE (runtime_activation_state = ACTIVE)
    ↓ (superseded by newly activated model version)
SUPERSEDED
    ↓ (archived for compliance/provenance)
ARCHIVED
```

### 3.2 Active Model Uniqueness and Scope

- Active models are uniquely identified and scoped by `(domain_id, task_type, model_role)` in `ModelRegistry`.
- Multiple model roles (e.g. `primary`, `shadow`, `canary`) can be active concurrently within the same domain and task type without conflict.
- Cognitia **never** overwrites or deletes historical `ModelRecord` entries. When a new model is observed as active, the prior active model transitions to `SUPERSEDED` while retaining full lineage and calibration hashes.

### 3.3 Strict Authority and Activation Invariants

| Action / Artifact | Initiator / Source | Cognitia Authority | Runtime Activation Triggered? |
| :--- | :--- | :--- | :--- |
| `ModelPromotionProposal` | Cognitia Service | `NONE` | No (Advisory only) |
| `ModelPromotionDecision` | External Human / Governance Board | `decision_source = "EXTERNAL"`, `cognitia_authority = "NONE"` | No (Transitions candidate to `APPROVED` only) |
| `ModelRollbackProposal` | Cognitia Service | `NONE` | No (Advisory only) |
| `ModelRollbackDecision` | External Human / Governance Board | `decision_source = "EXTERNAL"`, `cognitia_authority = "NONE"` | No (Transitions target to `APPROVED` only) |
| `ModelActivationObservation` | External Host / Cluster Runtime | `authority = "NONE"` | Yes (Reconciles internal state to match external reality) |
| Autonomous Activation Attempt (`/v1/learning/models/activate`, etc.) | Direct API Call | Rejected (`403 FORBIDDEN`, `ACTIVATION_FORBIDDEN`) | No |

---

## 4. Domain Freeze Modes

Cognitia domains support three freeze states:
1. `NORMAL`: Full inference, outcome observation, feedback ingestion, and candidate generation enabled.
2. `FROZEN`: Inference remains operational; candidate generation and learning events are suspended.
3. `OBSERVATION_ONLY`: Ingestion of outcomes and feedback continues for telemetry and drift tracking, but candidate generation is blocked with `DOMAIN_OBSERVATION_ONLY`.

---

## 5. Model Lineage Reconstruction

The `reconstruct_model_lineage(model_id, model_version, domain_id)` API dynamically traces a model's provenance backwards through:
- Base model parameters and registration timestamps
- Intermediate learning events and feedback IDs
- Promotion and rollback proposals
- External governance decisions
- Activation observations and supersession chains

---

## 6. Verification and Regression Suite

All 1034 tests in the test suite pass with zero warnings (`-W error`):
- `tests/learning/test_laya_provider_contract.py`: Verifies surrogate transparency and active immutability.
- `tests/learning/test_laya_real_model_integration.py`: Verifies real Laya model artifact checking, checksum enforcement, offline execution, and explicit failure codes.
- `tests/learning/test_model_lifecycle.py`: Verifies 9-state lifecycle, scoped active uniqueness, rollback flow, freeze modes, and lineage reconstruction.
- `tests/learning/test_lifecycle_security.py`: Verifies `authority = "NONE"`, external decision source enforcement, and historical model preservation.
- `runtime/tests/test_al3_gateway_endpoints.py`: Verifies HTTP gateway models lifecycle queries, rollback proposals/decisions, activation observations, freeze modes, and 403 Forbidden enforcement on autonomous activation endpoints.
