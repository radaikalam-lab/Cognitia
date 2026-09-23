# Cognitia Runtime Protocol Specification

**Protocol Version:** 1.0.0  
**ABI Version:** 1.0.0  
**Transport:** HTTP/1.1 (JSON) over `127.0.0.1:8000`  

---

## 1. Endpoints Summary

| Method | Path | Description | Access |
|---|---|---|---|
| `GET` | `/v1/health` | Subsystem health & ABI compatibility | Public (Local) |
| `GET` | `/v1/capabilities` | List registered capabilities | Public (Local) |
| `GET` | `/v1/providers` | List registered providers | Public (Local) |
| `POST` | `/v1/providers/register` | Register new provider | Local Authority |
| `POST` | `/v1/observations` | Ingest Canonical Observation | Authenticated Provider |
| `POST` | `/v1/evidence` | Ingest Canonical Evidence | Authenticated Provider |
| `POST` | `/v1/directional-specifications` | Evaluate Directional Spec | Authenticated Provider |

---

## 2. Request Headers

- `Content-Type: application/json`
- `X-Cognitia-Provider-Id: <provider_id>` (e.g. `thorium.browser`)
- `X-Cognitia-Capability: <capability_id>` (e.g. `observe.navigation`)
- `X-Cognitia-ABI-Version: 1.0.0`