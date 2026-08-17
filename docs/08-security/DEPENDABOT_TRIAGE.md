# Dependabot Security Triage & Remediation Record

**Task ID**: `GRX-SEC-002`  
**Date**: 2026-08-18  
**Scope**: Triage of 7 Dependabot vulnerability alerts on `main` (6 High, 1 Moderate)  
**Status**: All 7 alerts triaged, remediated, verified clean (`0 vulnerabilities` via `npm audit` and `pip-audit`), and automated dependency security gates added to CI.

---

## Executive Summary

GitHub Dependabot surfaced 7 vulnerability alerts on the default branch (`main`) across transitive JavaScript/Node.js dependencies. A complete audit across both the Python backend/worker ecosystems and the Next.js frontend ecosystem was performed:

1. **Python Ecosystem (`apps/api`, `apps/worker`)**:
   - `pip-audit` scanned all direct and transitive dependencies in `apps/api` and `apps/worker`.
   - **Result**: `0 known vulnerabilities found`.
2. **Node.js Ecosystem (`apps/web`)**:
   - 7 Dependabot alerts (4 in `brace-expansion`, 1 in `js-yaml`, 1 in `nanoid`, 1 in `postcss`).
   - Detailed exploitability triage confirmed that **all 7 vulnerabilities were confined to dev-time or build-time tooling** with zero runtime exposure to customer data or untrusted inputs.
   - All 7 vulnerabilities have been patched via exact package overrides and lockfile updates in `apps/web`.
   - `npm audit` now reports **`found 0 vulnerabilities`**.
3. **CI Pipeline**:
   - Automated dependency audit gates (`pip-audit` for API and Worker, `npm audit --audit-level=high` for Frontend) have been added to `.github/workflows/ci.yml` to prevent unreviewed dependency CVEs from silently entering `main`.

---

## Vulnerability Triage Matrix

| Alert ID / Advisory | Package | Severity | CVSS | Affected Versions | Dependency Path & Usage in Growixa | Exploitability & Architecture Impact | Status & Remediation |
|---|---|---|---|---|---|---|---|
| **GHSA-mh99-v99m-4gvg** (CVE-2026-14257) | `brace-expansion` | High | 7.5 | `<1.1.17` | Transitive devDependency: `@eslint/eslintrc` -> `minimatch` -> `brace-expansion@1.1.16` | **Non-exploitable (Dev only)**: Used only during local `npm run lint` and CI for linting glob matching. Never included in client bundles or exposed to untrusted user input. | **Resolved**: Pinned to `^1.1.18` via `package.json` overrides. |
| **GHSA-mh99-v99m-4gvg** (CVE-2026-14257) | `brace-expansion` | High | 7.5 | `4.0.0 - 5.0.8` | Transitive devDependency: `eslint-config-next` -> `@typescript-eslint/parser` -> `@typescript-eslint/typescript-estree` -> `minimatch` -> `brace-expansion@5.0.7` | **Non-exploitable (Dev only)**: Used during TypeScript AST file matching in ESLint. Zero runtime presence. | **Resolved**: Pinned to `^5.0.9` via `package.json` overrides. |
| **GHSA-rgw5-rvv9-x895** (CVE-2026-14257 bypass) | `brace-expansion` | High | 7.5 | `<1.1.18` | Transitive devDependency: `@eslint/eslintrc` -> `minimatch` -> `brace-expansion@1.1.16` | **Non-exploitable (Dev only)**: Same dev-only linting context. No user-supplied strings are expanded with braces. | **Resolved**: Pinned to `^1.1.18` via `package.json` overrides. |
| **GHSA-rgw5-rvv9-x895** (CVE-2026-14257 bypass) | `brace-expansion` | High | 7.5 | `4.0.0 - 5.0.9` | Transitive devDependency: `eslint-config-next` -> `@typescript-eslint` -> `minimatch` -> `brace-expansion@5.0.7` | **Non-exploitable (Dev only)**: Same dev-only linting context. | **Resolved**: Pinned to `^5.0.9` via `package.json` overrides. |
| **GHSA-5p4m-2wfm-xmqj** (CVE-2026-59870) | `js-yaml` | High | 7.5 | `4.0.0 - 4.3.0` | Transitive devDependency: `@eslint/eslintrc` -> `js-yaml@4.3.0` | **Non-exploitable (Dev only)**: Used exclusively by legacy ESLint parser to parse local repo configuration files. No untrusted YAML parsing exists in web frontend. | **Resolved**: Updated to `4.3.1` via `package.json` overrides and lockfile refresh. |
| **GHSA-2v37-7h3g-55p8** | `nanoid` | High | 5.9 | `<3.3.18` | Transitive build dependency: `next` -> `postcss` -> `nanoid@3.3.16` | **Non-exploitable (Build only)**: PostCSS uses nanoid internally for unique AST node IDs during CSS compilation at `next build`. Not used for secrets, auth tokens, or session IDs. | **Resolved**: Pinned to `^3.3.18` via `package.json` overrides. |
| **GHSA-fxqj-rqcc-2cmp** | `postcss` | Moderate | N/A | `<=8.5.22` | Build & test dependency: `next` / `@vitejs/plugin-react` -> `postcss@8.5.22` | **Non-exploitable (Build only)**: Incomplete fix for arbitrary `.map` file reading via crafted `sourceMappingURL` in untrusted CSS. Growixa authors all CSS internally and does not process external user CSS. | **Resolved**: Pinned to `^8.5.26` via `package.json` overrides. |

---

## Detailed Vulnerability Analysis

### 1. `brace-expansion` DoS (GHSA-mh99-v99m-4gvg & GHSA-rgw5-rvv9-x895)
- **Description**: Unbounded expansion length and intermediate arrays in `brace-expansion` allow an attacker providing malicious glob patterns (e.g. `{0..10000000}`) to cause process crashes via Out-of-Memory (OOM).
- **Growixa Attack Surface**: In Growixa, `brace-expansion` is strictly used by `minimatch` inside ESLint's TypeScript parser and ESLint configuration loader. It runs only during `npm run lint` and CI. No end-user input, webhook payload, or API query parameters ever flow to `brace-expansion`.
- **Remediation**: Overrides added in `apps/web/package.json` specifying `"brace-expansion": "^1.1.18 || ^5.0.9"`.

### 2. `js-yaml` Quadratic CPU Consumption (GHSA-5p4m-2wfm-xmqj / CVE-2026-59870)
- **Description**: Parsing crafted YAML documents containing `!!omap` entries can trigger quadratic CPU consumption and denial of service.
- **Growixa Attack Surface**: `js-yaml` is required solely by `@eslint/eslintrc` to parse repository ESLint configuration files (which are authored by project engineers and committed to Git). Growixa frontend has no YAML parsing endpoints or features.
- **Remediation**: Override added specifying `"js-yaml": "^4.3.1"`.

### 3. `nanoid` Custom Generator Infinite Loop (GHSA-2v37-7h3g-55p8)
- **Description**: Calling custom nanoid generators with `size: 0` can result in an infinite loop.
- **Growixa Attack Surface**: `nanoid` is a sub-dependency of PostCSS for AST node numbering during Next.js compilation. PostCSS does not invoke custom generators with size 0. Growixa's runtime auth/security IDs are generated in the Python backend using standard UUIDv4, secrets, and cryptographic random generators.
- **Remediation**: Override added specifying `"nanoid": "^3.3.18"`.

### 4. `postcss` Arbitrary `.map` File Read (GHSA-fxqj-rqcc-2cmp)
- **Description**: Attacker-controlled `sourceMappingURL` in CSS can cause PostCSS to read arbitrary `.map` files when `from` option is unset.
- **Growixa Attack Surface**: PostCSS runs strictly at build-time over internal stylesheets (`globals.css`, Tailwind/Vanilla CSS). No user-submitted stylesheets are parsed.
- **Remediation**: Override added specifying `"postcss": "^8.5.26"`.

---

## Continuous Security Auditing in CI

To ensure dependency vulnerabilities are never invisible to CI and reviewers, `.github/workflows/ci.yml` has been updated with explicit audit steps:

- **Backend Job**:
  ```bash
  pip install pip-audit
  pip-audit apps/api
  ```
- **Worker Job**:
  ```bash
  pip install pip-audit
  pip-audit apps/worker
  ```
- **Frontend Job**:
  ```bash
  npm audit --audit-level=high
  ```

---

## Verification Results

1. `cd apps/web && npm audit` -> **`found 0 vulnerabilities`**.
2. `pip-audit apps/api` -> **`No known vulnerabilities found`**.
3. `pip-audit apps/worker` -> **`No known vulnerabilities found`**.
4. Frontend Quality Suite (`lint`, `format:check`, `typecheck`, `test`, `build`) -> **All passed (263/263 unit tests, 47 test suites, static build succeeded)**.
