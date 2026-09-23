# Cognitia Standalone Runtime & Provider Gateway

**Version:** 1.0.0  
**Cognitive ABI:** 1.0.0  
**Architecture:** Standalone Epistemic Service (Local-First)  
**Reference Provider:** Lean Thorium Browser Adapter  

---

## 1. Overview

The **Cognitia Standalone Runtime** operationalizes the canonical Cognitia epistemic core as an independent, deterministic, local-first service. Applications connect as **independent providers** through adapter bridges. 

### Core Architectural Invariant
```
Application
    ↓
Application-specific Adapter
    ↓
Canonical Cognitia ABI / Contract (1.0.0)
    ↓
Cognitia Gateway
    ↓
Cognitia Runtime (InMemoryEpistemicService)
```

- **Epistemic Novelty ≠ Production Authority:** Cognitia reasons over observations, tests hypotheses, and emits advisory directional proposals. It possesses **zero** authority to execute commands, control browsers, modify ERP records, or invoke OS utilities.

---

## 2. Quick Start

### Local Execution (Python 3.12+)
```powershell
python E:\Cognitia\runtime\scripts\start_runtime.py --host 127.0.0.1 --port 8000
```

### Docker Execution
```powershell
cd E:\Cognitia\runtime
docker compose up -d
```

### Health Check
```powershell
python E:\Cognitia\runtime\scripts\health_check.py
```
Or query:
```bash
curl http://127.0.0.1:8000/v1/health
```

---

## 3. Directory Layout

```
runtime/
├── Dockerfile                   # Minimal python:3.12-slim container
├── compose.yaml                 # Localhost bound, read-only root, cap_drop ALL
├── README.md                    # This document
├── COGNITIA_RUNTIME_ARCHITECTURE.md
├── COGNITIA_PROVIDER_CONTRACT.md
├── COGNITIA_RUNTIME_SECURITY.md
├── COGNITIA_RUNTIME_PROTOCOL.md
├── COGNITIA_RUNTIME_TEST_REPORT.md
├── config/
│   ├── runtime_config.json      # Binding, size limits, timeouts
│   └── provider_whitelist.json  # Registered providers and capabilities
├── gateway/
│   ├── __init__.py
│   ├── abi_validator.py         # Validates against Cognitive ABI v1.0.0
│   ├── provider_registry.py     # Manages capabilities & authority levels
│   ├── security.py              # Rate limiting, untrusted data isolation
│   ├── epistemic_bridge.py      # Dispatches to InMemoryEpistemicService
│   └── app.py                   # Lightweight HTTP server (127.0.0.1:8000)
├── schemas/
│   ├── provider_contract_v1.json
│   ├── observation_api_v1.json
│   └── directional_api_v1.json
├── scripts/
│   ├── start_runtime.py
│   └── health_check.py
└── tests/
    ├── test_abi_and_registry.py
    ├── test_epistemic_and_directional.py
    ├── test_security_and_resilience.py
    ├── test_thorium_reference.py
    └── test_gateway_e2e.py
```