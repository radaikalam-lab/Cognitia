# Cognitia Runtime Security Architecture

**Document Version:** 1.0.0  
**Security Level:** Minimal Privilege / Local-First Sandbox  

---

## 1. Threat Model & Principles

1. **Local-Only Boundary:** The runtime only binds to `127.0.0.1`. No public exposure (`0.0.0.0`) is permitted.
2. **Untrusted Data Isolation:** All data originating from external applications (such as web content parsed by Thorium) is tagged with `is_untrusted_external_content: true`.
3. **No Execution Channel:** The gateway strictly prohibits execution directives (`command`, `exec`, `execute`, `shell`).
4. **Non-Root Execution:** The Docker container runs as UID `10001` (`cognitia`).
5. **Read-Only Root Filesystem:** Container runs with `read_only: true` with a tmpfs mounted at `/tmp`.
6. **Capability Drop:** All Linux capabilities (`cap_drop: ALL`) and `no-new-privileges: true` are enforced.
7. **Zero Host Mounts:** No host filesystem roots (`C:\`), no Docker socket (`/var/run/docker.sock`), and no browser profile/credential directories are accessible.
8. **Credential Sanitization:** Observation payloads are scanned to reject accidental password, token, or cookie leakage.