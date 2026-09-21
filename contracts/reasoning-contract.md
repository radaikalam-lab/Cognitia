# Contract: Reasoning Contract

**Contract Status**: Authoritative  
**Contract Version**: 1.0.0  
**Phase**: Phase 0 Foundation  

---

## 1. Purpose

The **Reasoning Contract** decouples deliberate, multi-step structured reasoning from fast decision inference. It establishes immutable reasoning traces, supported reasoning modes, and capability protocols.

---

## 2. Core Invariants

1. **Separation from Decision Inference**:
   Fast reflex decisions (e.g., lookups, linear policies) and deliberate cognitive reasoning (e.g., multi-step deductions, counterfactual exploration) are distinct.
2. **Immutable Audit Traces**:
   A reasoning derivation generates an immutable `ReasoningTrace`. Correcting a reasoning outcome requires creating a new versioned trace, never overwriting historical traces.
3. **Provider Agnosticism**:
   Reasoning providers can be symbolic theorem provers, causal graph analyzers, rule engines, external solver adapters, or human analysts.

---

## 3. Canonical Reasoning Modes

```text
ReasoningMode
 ├── DEDUCTION        (Deriving necessary conclusions from established premises)
 ├── ABDUCTION        (Inferring the most plausible explanation for observations)
 ├── ANALOGY          (Transferring structural relationships from a source domain)
 ├── COUNTERFACTUAL   (Evaluating outcomes under hypothetical premise interventions)
 └── CAUSAL           (Tracing directed cause-and-effect relationships)
```

---

## 4. Reasoning Trace Schema

```text
ReasoningTrace
 ├── id: UUID
 ├── schema_version: SemVer
 ├── created_at: ISO-8601 UTC timestamp
 ├── mode: ReasoningMode
 ├── premises: list[CognitiveObject]
 ├── steps: list[ReasoningStep]
 ├── conclusion: CognitiveObject
 ├── confidence: float ([0.0, 1.0] Aggregate inferential confidence of the derivation trace)
 ├── provider: str
 └── provenance: ProvenanceRecord
```

Where `ReasoningStep` contains:
* `step_number`: int
* `inference_rule`: str
* `input_references`: list[str]
* `intermediate_claim`: str
* `confidence`: float ($[0.0, 1.0]$ Logical validity or step reliability)

---

## 5. Reasoning Capability Protocol

```python
class ReasoningCapability(Protocol):
    capability_id: str
    provider_name: str
    version: str
    supported_modes: set[ReasoningMode]
    is_deterministic: bool

    def reason(
        self,
        mode: ReasoningMode,
        premises: list[CognitiveObject],
        context: dict[str, Any] | None = None
    ) -> ReasoningTrace: ...
```
