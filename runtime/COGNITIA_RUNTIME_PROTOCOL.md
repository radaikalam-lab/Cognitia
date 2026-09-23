# Cognitia Runtime Protocol Specification

**Protocol Version:** 1.0.0  
**Cognitive ABI Version:** 1.0.0  
**Transport:** HTTP/1.1 (JSON) over `127.0.0.1`  
**Identity:** `Cognitia`  

---

## 1. REST Endpoints

| Method | Path | Description | Access / Headers |
|---|---|---|---|
| `GET` | `/v1/health` | System health, ABI version & subsystem status | Public (Local) |
| `GET` | `/v1/capabilities` | List registered capabilities | Public (Local) |
| `GET` | `/v1/providers` | List registered providers | Public (Local) |
| `POST` | `/v1/providers/register` | Dynamic registration (Disabled: 403) | Disabled in 1.0 |
| `POST` | `/v1/observations` | Ingest Canonical Observation | Registered Provider |
| `POST` | `/v1/evidence` | Ingest Canonical Evidence | Registered Provider |
| `POST` | `/v1/directional-specifications` | Evaluate Directional Specification | Registered Provider |

---

## 2. Request Headers

- `Content-Type: application/json`
- `X-Cognitia-Provider-Id: <provider_id>` (e.g. `thorium.browser`, `acoustiforge.adapter`)
- `X-Cognitia-Capability: <capability_id>` (e.g. `observe.navigation`, `observe.authorized_content`)
- `X-Cognitia-ABI-Version: 1.0.0`
- `X-Cognitia-Protocol-Version: 1.0.0`

---

## 3. Response Structure

### Success Response
```json
{
  "status": "success",
  "correlation_id": "85bfc3f6-5835-435e-bc32-f98d5909caa3",
  "provider_id": "thorium.browser",
  "capability": "observe.navigation",
  "processing_duration_ms": 0.085,
  "ingest_result": {
    "status": "ingested",
    "entity_type": "observation",
    "node_id": "85bfc3f6-5835-435e-bc32-f98d5909caa3",
    "entity_id": "85bfc3f6-5835-435e-bc32-f98d5909caa3",
    "epistemic_status": "observed",
    "provenance_id": "5fa93d13-ebc2-4982-860f-7df63400c9b7"
  }
}
```

### Safe Error Response (No stack trace or filesystem leakage)
```json
{
  "status": "error",
  "error_type": "UnauthorizedCapability",
  "message": "Provider 'thorium.browser' is not authorized for capability 'execute.command'",
  "correlation_id": "d46af436-b225-4b80-a8ad-f3cc81de8579",
  "timestamp": 1727100000.0
}
```