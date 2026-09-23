# Cognitia Provider Contract & Specification

**Contract Version:** 1.0.0  
**Runtime Identity:** `Cognitia`  
**Target ABI:** `1.0.0`  

---

## 1. Provider Whitelist Definition

All providers must be defined in the authoritative static whitelist (`runtime/config/provider_whitelist.json`). Dynamic provider self-registration is disabled.

```json
{
  "provider_id": "thorium.browser",
  "provider_name": "Lean Thorium Reference Browser Adapter",
  "provider_version": "138.0.7204.306",
  "adapter_version": "1.0.0",
  "status": "OPERATIONAL_REFERENCE",
  "supported_abi_versions": ["1.0.0"],
  "capabilities": [
    "observe.navigation",
    "observe.tab",
    "observe.page_metadata",
    "observe.authorized_content"
  ],
  "authority_level": "NONE",
  "transport": "local_http",
  "allowed_content_types": ["text/plain", "application/json", "text/html"]
}
```

---

## 2. Provider Lifecycle & Statuses

- **`OPERATIONAL_REFERENCE`:** Fully implemented and validated reference provider adapter (e.g. Lean Thorium).
- **`PLANNED_REFERENCE`:** Architecturally planned provider definition (e.g. Frappe ERP, AcoustiForge). No live connection is implied.
- **`DISABLED`:** Provider explicitly suspended.

---

## 3. Authority Boundary

- `authority_level` is permanently fixed to **`NONE`**.
- Any attempt to declare or request `execute.*`, `shell.*`, `process.*`, `hardware.*`, or `browser_control.*` is unconditionally rejected.