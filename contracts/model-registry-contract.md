# Contract: Model Registry Contract

**Contract Status**: Authoritative  
**Contract Version**: 1.0.0  
**Phase**: Phase 0 Foundation  

---

## 1. Purpose

The **Model Registry Contract** specifies the interface and data model for registering, tracking, and auditing cognitive models. It guarantees model immutability and provenance across lifecycle evolutions.

---

## 2. Core Invariants

1. **Immutable Model Identity & Content**:
   A registered `(model_id, model_version)` pair is strictly immutable in its parameters, capability type, input/output schemas, provider, calibration checksum, and creation timestamp.
2. **Controlled Lifecycle State**:
   The `status` field (`EXPERIMENTAL`, `ACTIVE`, `DEPRECATED`, `RETIRED`) represents registry governance state. Updating status via `set_status()` modifies lifecycle routing without altering model identity, parameters, or historical provenance.
3. **Evolution via Versioning**:
   Any modification, retrain, or recalibration MUST produce a distinct `model_version` with a new calibration checksum.
4. **No Runtime Weight Mutation**:
   Cognitia runtime processes MAY record operational experiences, residuals, and evidence, but MUST NOT mutate active production model weights at runtime.
5. **Historical Availability**:
   Historical model metadata MUST remain queryable indefinitely to ensure historical decision provenance remains reproducible.

---

## 3. Model Record Schema (COG-006 Resolved)

```text
ModelRecord
 ├── id: UUID
 ├── schema_version: SemVer
 ├── created_at: ISO-8601 UTC timestamp (Time the model artifact was created)
 ├── model_id: str (Globally unique model family name/ID)
 ├── model_version: str (Semantic version string)
 ├── provider: str (Provider or library name, e.g., "deterministic_rules", "laya", "mock")
 ├── capability_type: CapabilityType
 ├── input_schema_version: str
 ├── output_schema_version: str
 ├── calibration_checksum: str (SHA-256 hash of model weights / rule specification)
 ├── is_deterministic: bool
 ├── status: ModelStatus (EXPERIMENTAL, ACTIVE, DEPRECATED, RETIRED)
 ├── registered_at: ISO-8601 UTC timestamp (Time ModelRegistry ingested/committed the record)
 ├── metadata: dict[str, Any]
 └── provenance: ProvenanceRecord
```

---

## 4. Model Registry Interface

```python
class ModelRegistry(Protocol):
    def register(self, record: ModelRecord) -> None: ...
    def get(self, model_id: str, version: str) -> ModelRecord | None: ...
    def list_versions(self, model_id: str) -> list[ModelRecord]: ...
    def get_active(self, model_id: str) -> ModelRecord | None: ...
    def set_status(self, model_id: str, version: str, status: ModelStatus) -> None: ...
```
