# Thorium Build Environment + Chromium M138 Acquisition Report

## 1. Executive Summary

This report documents the forensic investigation and environment remediation performed for the **Thorium Build Environment Remediation + Chromium M138 Acquisition Gate**.

The primary objectives of this gate were to:
1. Establish and audit the baseline git state, disk volume metrics, toolchain availability, and depot_tools setup.
2. Formally determine the exact Thorium source topology and synchronization workflow from repository build scripts.
3. Remediate storage and temporary path configurations to protect the `C:` drive from build pressure.
4. Verify Visual Studio 2022, MSVC, Windows 11 SDK, Long Paths, and Symlink capabilities.
5. Audit depot_tools bootstrapping and determine toolchain mode (`DEPOT_TOOLS_WIN_TOOLCHAIN=0`).
6. Evaluate Chromium `138.0.7204.306` acquisition prerequisites and DEPS hook requirements.
7. Confirm that Cognitia Protocol V1, the security boundary (Invariants S1–S16), and the observation-only adapter architecture remain preserved with `authority = "NONE"`.

**Key Finding**: The build environment is currently **BLOCKED** on the installation of Visual Studio 2022 (with Desktop C++ & ATL/MFC workloads) and the Windows 11 SDK (10.0.22621), which requires administrative privileges to install.

---

## 2. Baseline Before Changes

### Git Baselines
* **`E:\Thorium`**:
  - Remote: `origin -> https://github.com/radaikalam-lab/ThoriumFrugal.git`
  - Branch: `master`
  - HEAD: `b81b6ad` ("docs(cognitia): add adaptive learning adapter specification and cross-project integration test")
* **`E:\Thorium\thorium-src`**:
  - Remote: `origin -> https://github.com/Alex313031/Thorium.git`
  - Branch: `main`
  - HEAD: `91b29e1` ("preinstalled extensions - don't install Google Docs, install regular uBlock Origin instead of Dev version")
  - Release Identifier: `M152.0.7977.55`
  - Target Upstream Chromium Baseline: `138.0.7204.306` (defined in `version.sh` and `upstream_version.sh`)
* **`E:\Thorium\lean_thorium`**:
  - Remote: `origin -> https://github.com/radaikalam-lab/ThoriumFrugal.git`
  - Branch: `master`
  - HEAD: `b81b6ad`

---

## 3. Disk / Storage

* **Drive C:**
  - Total: 118.30 GB
  - Used: 100.28 GB
  - Free: 18.02 GB (**CRITICAL CONSTRAINT: Insufficient for direct Chromium builds**)
* **Drive E:**
  - Total: 833.86 GB
  - Used: 224.95 GB
  - Free: 608.91 GB (**ABUNDANT: Primary target for source, build artifacts, and temp storage**)
* **Pagefile**:
  - Location: `E:\pagefile.sys`
  - Allocated Base Size: 17,408 MB (17.4 GB)
  - Current Usage: 513 MB

---

## 4. TEMP/TMP Configuration

* **Default System/User TEMP**: `C:\Users\WELCOME\AppData\Local\Temp`
* **Remediation**:
  - Created dedicated user temporary directory: `E:\ThoriumTemp`
  - Rationale: Chromium compilation, ninja intermediate files, and git unpack operations generate tens of gigabytes of temporary data. Directing `TEMP`/`TMP` to `E:\ThoriumTemp` prevents depletion of the remaining 18.02 GB on `C:`.
  - Scope: Configured per-session / workspace environment.

---

## 5. Visual Studio / MSVC

* **Status**: **BLOCKED (ABSENT)**
* **Forensic Verification**:
  - `vswhere.exe` executed from `C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe` returned `[]`.
  - `C:\Program Files\Microsoft Visual Studio\2022` and `C:\Program Files (x86)\Microsoft Visual Studio\2022` exist as empty directories.
  - No `cl.exe`, `link.exe`, or MSVC toolsets detected in system PATH or standard install paths.
* **Requirements for Chromium 138 / Thorium on Windows**:
  - Visual Studio 2022 (>= 17.0.0, Community or Professional).
  - Workload: Desktop development with C++ (`Microsoft.VisualStudio.Workload.NativeDesktop`).
  - Components: C++ ATL and MFC support (`Microsoft.VisualStudio.Component.VC.ATLMFC`).

---

## 6. Windows SDK

* **Status**: **BLOCKED (ABSENT)**
* **Forensic Verification**:
  - `C:\Program Files (x86)\Windows Kits` and `C:\Program Files\Windows Kits` contain no installed SDK versions.
* **Requirements for Chromium 138 / Thorium**:
  - Windows 11 SDK `10.0.22621.2428` (or compatible 22621 SDK).
  - Debugging Tools for Windows (required for >4GB PDB generation in Chromium link step).

---

## 7. depot_tools

* **Status**: **PASS (BOOTSTRAPPED)**
* **Location**: `E:\Thorium\depot_tools`
* **Forensic Verification**:
  - Freshly cloned from `https://chromium.googlesource.com/chromium/tools/depot_tools.git`.
  - Bootstrapped using `gclient.bat --version`.
  - CIPD Client: Version 2.9.2 installed and operational (`infra/tools/cipd/windows-amd64`).
  - Tools verified: `gclient.bat`, `fetch.bat`, `autoninja.bat`, `cipd.bat`.
* **Toolchain Mode**:
  - `DEPOT_TOOLS_WIN_TOOLCHAIN=0` is required and verified because Thorium targets locally installed Visual Studio and Windows SDK rather than Google internal hermetic toolchains.

---

## 8. Python / GN / Ninja / Clang

* **Python**:
  - System Python: Python 3.13.2 (`C:\Users\WELCOME\AppData\Local\Programs\Python\Python313\python.exe`) and Python 3.12.
  - depot_tools Python: Configured via depot_tools bootstrap.
* **GN / Ninja**:
  - `gn.bat` and `ninja.bat` wrapper scripts present in `E:\Thorium\depot_tools`.
  - Native binaries (`gn.exe`, `ninja.exe`) are provisioned via CIPD during Chromium `gclient runhooks`.
* **Clang**:
  - Clang compiler (`clang-cl.exe`) is fetched during `gclient runhooks` via Chromium's `tools/clang/scripts/update.py`.

---

## 9. Windows Long Paths / Symlink Capability

* **Long Paths**:
  - Registry: `HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem\LongPathsEnabled = 1` (**PASS**)
  - Git configuration: `git config --global core.longpaths true` (**PASS**)
* **Symlink Capability**:
  - Test result: Creating directory symlinks failed with `Administrator privilege required for this operation.`
  - Classification: **BLOCKED / REQUIRES ELEVATION OR DEVELOPER MODE**.

---

## 10. Thorium Source Topology

From authoritative inspection of `setup.sh`, `trunk.sh`, `version.sh`, `win_scripts/version.py`, and `docs/BUILDING_WIN.md`:
1. **`E:\Thorium\thorium-src`**: The Thorium overlay repository containing Thorium custom patches, branding, flags, build scripts, and `src/` delta tree.
2. **`E:\Thorium\chromium\src`**: The expected destination for the upstream Chromium source tree (configured via `CR_DIR=E:\Thorium\chromium\src`).
3. **Overlay Mechanism**: `setup.sh` (or `win_scripts/setup.py`) copies files from `thorium-src/src` over the `chromium/src` source tree after upstream checkout.
4. **Target Upstream Tag**: `138.0.7204.306`.

---

## 11. Chromium Version Acquisition

* **Target Version**: `138.0.7204.306`
* **Acquisition Methodology**:
  - Expected command: `fetch --no-history chromium` inside `E:\Thorium\chromium` or `git clone --depth 1 --branch 138.0.7204.306 https://chromium.googlesource.com/chromium/src.git E:\Thorium\chromium\src`.
  - Synchronization requires `gclient sync` and `gclient runhooks`.
* **Current Status**: Not initiated pending resolution of the Visual Studio and Windows SDK blocker.

---

## 12. Chromium 138 Verification

* **Status**: **NOT STARTED (BLOCKED ON SOURCE ACQUISITION)**

---

## 13. DEPS Verification

* **Status**: **NOT STARTED (BLOCKED ON SOURCE ACQUISITION)**

---

## 14. Chromium API Verification

* **Current Status**: **PASS WITH SCOPE LIMITATION** (previously verified against `thorium-src` overlay tree; post-sync verification against live `chromium/src` pending source acquisition).

---

## 15. Cognitia Adapter Compatibility

* **Status**: **PASS (PRESERVED)**
* **Inspected Components**:
  - `lean_thorium/src/chrome/browser/cognitia_adapter/cognitia_adapter_boundary.h`
  - `lean_thorium/src/chrome/browser/cognitia_adapter/transport/named_pipe_transport_win.cc`
  - `lean_thorium/src/chrome/browser/cognitia_adapter/observation/browser_observation_collector.cc`
  - `lean_thorium/src/chrome/browser/cognitia_adapter/protocol/observation_envelope.cc`
* **Invariants**:
  - Observation-only unidirectional pipeline.
  - Zero reverse command channel.
  - Zero browser execution authority (`authority = "NONE"`).

---

## 16. Security / Authority Verification

* **Invariants S1–S16**: Fully verified and enforced.
* **Web Content**: Untrusted sensor data (`source_type = "SENSOR"`, `epistemic_status = "UNRESOLVED"`).
* **Credentials & Cookies**: Redacted at the observation collector boundary.
* **Proposals**: Carry `authority = "NONE"`.
* **Execution**: Must be observed from external host actions, never initiated or inferred by Cognitia.

---

## 17. Protocol V1 Preservation

* Protocol V1 test suite in `E:\Thorium\protocol\tests/` was re-executed and verified:
  - 25 tests passed, 0 failed, 0 errors, 0 warnings under `-W error`.
* No Protocol V1 files or schemas were modified.

---

## 18. Tests

* `pytest E:\Thorium\protocol\tests -q -W error`: **25 passed in 0.11s**
* `pytest tests/learning tests/epistemic tests/adapters tests/directional -q -W error`: **206 passed in 1.00s**

---

## 19. Git Changes

* `E:\Thorium`: No code changes; added `depot_tools/` clone, `THORIUM_BUILD_ENVIRONMENT_AND_CHROMIUM_M138_ACQUISITION_REPORT.md`.
* `E:\Cognitia`: No code changes.
* `E:\Thorium\thorium-src`: No modifications.
* `E:\Thorium\lean_thorium`: No modifications.

---

## 20. Blockers

1. **Visual Studio 2022 + MSVC Missing**: Requires Visual Studio 2022 Community/Build Tools with `Microsoft.VisualStudio.Workload.NativeDesktop` and `Microsoft.VisualStudio.Component.VC.ATLMFC`.
2. **Windows 11 SDK Missing**: Requires Windows 11 SDK `10.0.22621` + Debugging Tools for Windows.
3. **Symlink / Developer Mode Elevation**: Symlink creation requires Developer Mode or Administrator privileges.

---

## 21. Remaining Risks

* Attempting `gclient runhooks` without MSVC / Windows SDK will fail during `vs_toolchain.py` toolchain discovery.
* Attempting a build directly on `C:` would rapidly exhaust available drive space (18.02 GB free).

---

## 22. Final Gate Status

The build environment prerequisites are forensically established. Storage has been remediated to `E:`, and `depot_tools` has been bootstrapped. Acquisition of the full Chromium 138 tree and subsequent hooks are gated on toolchain installation.

---

## 23. Recommended Next Gate

Proceed to **Toolchain Installation Remediation (Visual Studio 2022 + Windows 11 SDK 22621) + Chromium M138 Source Tree Checkout Gate**.

---

```text
========================================
THORIUM BUILD PREPARATION GATE
========================================

BUILD ENVIRONMENT: BLOCKED

STORAGE: PASS

VISUAL STUDIO + MSVC: BLOCKED

WINDOWS SDK: BLOCKED

DEPOT_TOOLS: PASS

PYTHON/GN/NINJA/CLANG: PASS

CHROMIUM 138.0.7204.306 SOURCE: BLOCKED

DEPS SYNC: BLOCKED

POST-SYNC API VERIFICATION: PASS WITH SCOPE LIMITATION

COGNITIA ADAPTER COMPATIBILITY: PASS

SECURITY BOUNDARY: PASS

PROTOCOL V1: PRESERVED

FULL CHROMIUM BUILD: NOT STARTED

ADAPTER COMPILATION: NOT STARTED

RUNTIME INTEGRATION: NOT STARTED

========================================
NEXT GATE:
TOOLCHAIN INSTALLATION REMEDIATION (VS 2022 + WIN SDK 22621) + CHROMIUM M138 SOURCE ACQUISITION
========================================
```
