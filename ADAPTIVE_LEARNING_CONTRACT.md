# Cognitia Adaptive Learning - Provider Contract

## 1. AdaptiveLearningProvider Protocol

```python
class AdaptiveLearningProvider(Protocol):
    @property
    def provider_id(self) -> str: ...
    @property
    def provider_version(self) -> str: ...
    @property
    def supported_tasks(self) -> list[TaskType]: ...
    @property
    def is_deterministic(self) -> bool: ...

    def load_model(self, record: ModelRecord, model_artifact: Any = None) -> None: ...
    def infer(self, request: AdaptiveInferenceRequest) -> AdaptiveLearningResult: ...
    def evaluate(self, model_id: str, dataset: list[dict[str, Any]]) -> dict[str, float]: ...
```

## 2. Canonical Task Types

- `classification`: Discrete classification with probability distributions across candidate classes.
- `regression`: Continuous value prediction.
- `scoring`: Hypothesis scoring and relative probability assessment.
- `ranking`: Ordered sorting and relative weighting of candidate options.
- `confidence_estimation`: Calibrated certainty and uncertainty estimation.
- `anomaly_detection`: Outlier detection against baseline distributions.
- `interpretation`: Candidate heuristic interpretation of Directional Specifications.

## 3. Canonical Data Schemas

### AdaptiveLearningResult
```json
{
  "id": "uuid4",
  "schema_version": "1.0.0",
  "model_id": "laya_acoustic_v1",
  "model_version": "1.0.0",
  "provider_id": "laya",
  "provider_version": "1.0.0",
  "input_reference": "obs:001",
  "representation_version": "1.0.0",
  "task": "classification",
  "output": {
    "decision": "resonance",
    "scores": {
      "resonance": 0.81,
      "noise": 0.11,
      "measurement_error": 0.06,
      "unknown": 0.02
    }
  },
  "confidence": 0.81,
  "is_deterministic": true,
  "epistemic_status": "UNRESOLVED",
  "authority": "NONE"
}
```
