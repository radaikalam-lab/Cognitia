# Contract: Capability Contract (SPI)

**Contract Status**: Authoritative  
**Contract Version**: 1.0.0  
**Phase**: Phase 0 Foundation  

---

## 1. Purpose

The **Capability Contract** defines the Service Provider Interface (SPI) for provider-agnostic cognitive functions. It ensures that cognitive capabilities (e.g., decision-making, reasoning, prediction) can be implemented and substituted without coupling Cognitia to any specific model, library, or AI framework.

---

## 2. Core Invariants

1. **Provider Neutrality**:
   No single provider (e.g., Laya, tiny ML, PyTorch, rules) is hardcoded into Cognitia core.
2. **Explicit Capability Descriptors**:
   Every capability provider MUST expose structured metadata: identifier, provider name, semantic version, capability type, input/output schemas, and determinism indicator.
3. **Advisory Decisions**:
   A `DecisionCapability` outputs a `Decision` (a cognitive proposal). It does NOT possess execution authority over physical actuators.

---

## 3. Capability Descriptors & Types

```text
CapabilityType
 ├── DECISION
 ├── REASONING
 ├── PLANNING (Future)
 ├── PREDICTION (Future)
 ├── CLASSIFICATION (Future)
 ├── ANOMALY_DETECTION (Future)
 └── SIMULATION (Future)
```

```text
CapabilityDescriptor
 ├── capability_id: str
 ├── capability_type: CapabilityType
 ├── provider_name: str
 ├── version: str (SemVer)
 ├── input_schema_version: str
 ├── output_schema_version: str
 └── is_deterministic: bool
```

---

## 4. Decision Capability Protocol & Decision Schema (COG-005 Resolved)

```python
class DecisionCapability(Protocol):
    descriptor: CapabilityDescriptor

    def propose_decision(
        self,
        observation: Observation,
        context: dict[str, Any] | None = None
    ) -> Decision: ...
```

### Decision Schema
```text
Decision
 ├── id: UUID
 ├── schema_version: SemVer
 ├── created_at: ISO-8601 UTC timestamp
 ├── proposal_type: str
 ├── proposed_action: Action
 ├── confidence: float ([0.0, 1.0] Provider proposal confidence)
 ├── rationale: Optional[str]
 ├── provenance: ProvenanceRecord (Direct lineage tracing producer, capability, and model)
 └── metadata: dict[str, Any]
```

---

## 5. Capability Registry Interface

```python
class CapabilityRegistry(Protocol):
    def register(self, capability: BaseCapability) -> None: ...
    def get(self, capability_id: str) -> BaseCapability | None: ...
    def list_by_type(self, capability_type: CapabilityType) -> list[BaseCapability]: ...
    def list_all(self) -> list[BaseCapability]: ...
```
