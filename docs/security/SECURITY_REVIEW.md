# Security Review — Phase 3G.5

**Type:** Repository audit (static). No cloud resources created. No dependency upgrades.  
**Scope:** Secrets, SSH, temp artifacts, ignore rules, dependency integrity, least privilege.  
**Baseline HEAD reviewed:** `85c94e5c2b1d120c4bcf8d9fe7deb94c628ff0b1`  
**Date:** 2026-07-23

## Executive summary

No committed live API keys, private SSH keys, or `.env` secrets were found. Cloud ops scripts read `RUNPOD_API_KEY` from the environment and avoid printing key material. Ignore rules cover weights, bundles, local pod connection files, and evaluation raw outputs. Residual risks are operational (key handling on workstations, pod ID disclosure in release notes, overly broad future commits of diagnostics) rather than active secret leakage in git.

**Overall security posture for a research lab repo:** Acceptable for current phase, with hardening recommendations below.

---

## 1. Committed secrets

| Check | Result |
| --- | --- |
| `.env` committed | **Pass** — only `.env.example` (placeholders) |
| `BEGIN OPENSSH PRIVATE KEY` / PEM in tree | **Pass** — none found |
| Hardcoded `RUNPOD_API_KEY=…` / `sk-…` / `ghp_…` | **Pass** — none found |
| `credentials*.json` / `secrets/` | **Pass** — gitignored patterns present |

**Finding S1 (Informational):** Release notes and cloud records include **pod IDs** and redacted instance class names. Not credentials, but infrastructure identifiers. Acceptable for evidence; avoid adding account emails or billing IDs.

---

## 2. API keys

| Surface | Handling | Assessment |
| --- | --- | --- |
| `RUNPOD_API_KEY` | Env var in `phase3g_*.py` / Phase 3F scripts | Good |
| Hosted provider keys in `.env.example` | Commented placeholders | Good |
| Logging | Scripts designed not to print secrets | Good — keep this invariant in future scripts |

**Recommendation:** Prefer OS secret store / CI OIDC later; never pass keys on CLI argv (visible in process lists).

---

## 3. SSH handling

| Topic | Assessment |
| --- | --- |
| Public key injection via API `PUBLIC_KEY` | Appropriate for RunPod |
| Default key paths under `~/.runpod/ssh/` | Documented; private keys not in repo |
| SSH options | `PasswordAuthentication=no`, `NumberOfPasswordPrompts=0` | Good |
| Local method files | `.ssh-*.local*` / connection JSON gitignored | Good |

**Finding S2 (Low):** Operators must ensure private keys are filesystem-permission restricted (`600` on Unix). Windows ACL hygiene is operator-owned.

**Finding S3 (Low):** Bootstrap may restart pods when `--restart` is used — availability impact, not confidentiality.

---

## 4. Temporary files and ignored artifacts

| Pattern | Covered? |
| --- | --- |
| `.env`, `*.pem`, `*.key` | Yes |
| Model weights (`*.safetensors`, etc.) | Yes |
| Git bundles under `artifacts/**` | Yes |
| `evaluations/cloud/.pod-*`, `.ssh-*`, `provision-preflight.json` | Yes |
| Most `evaluations/results/**` raw outputs | Yes (with documented allowlists for public reports) |

**Finding S4 (Medium — process):** `evaluations/diagnostics/**` is force-tracked. Future dumps must be reviewed so they never include prompts with private case data or pasted tokens. Phase 3F diagnostics used synthetic prompts — keep that rule.

**Finding S5 (Low):** BOM noted historically on some lock hash strings in candidate JSON (`\ufeff…`). Integrity tooling should normalize encoding; not a secret issue.

---

## 5. Dependency integrity

| Control | Status |
| --- | --- |
| Runtime vs dev split | Present (P1) |
| `torch-pin.json` + cu124 index | Present |
| `container-image-pin.json` digests | Present |
| `dependency-lock.sha256` | Present |
| `phase3g_verify_env.py` | Present |

**Finding S6 (Low):** Host image torch may differ from venv torch; docs correctly require venv override. Supply-chain risk remains on PyPI/torch wheel index — pin versions and prefer hash verification in a future Priority 2.

---

## 6. Least-privilege recommendations

1. **Cloud API key:** Scope to pod lifecycle only; rotate after each major phase; revoke on staff exit.
2. **One pod max:** Enforce via preflight + human checklist.
3. **No public endpoints / Jupyter:** Keep forbidden in authorization.
4. **No weights in object storage with public ACLs.**
5. **Workstation:** Separate account for cloud spend; MFA on provider console.
6. **CI (future):** Read-only tokens for docs/tests; never attach `RUNPOD_API_KEY` to PR forks.
7. **Training directory:** Keep disabled until Phase 5 authorization.
8. **Investigator boundary:** Do not add auth/billing/case vault here.

---

## 7. Findings table

| ID | Severity | Topic | Status |
| --- | --- | --- | --- |
| S1 | Info | Pod IDs in evidence | Accept |
| S2 | Low | SSH private key OS perms | Operator action |
| S3 | Low | Pod restart on bootstrap | Documented |
| S4 | Medium | Diagnostics allowlist discipline | Process control |
| S5 | Low | Lock hash encoding BOM | Tech debt |
| S6 | Low | Supply-chain hash pinning beyond versions | P2 candidate |

**Critical/High committed-secret findings:** **None.**

---

## 8. What this review did not do

- Pen test of RunPod or host kernels
- Dynamic secret scanning SaaS
- Dependency CVE database deep dive
- Production authz review (N/A — no prod endpoints)

---

## 9. Related policy

See also `docs/SECURITY.md` (standing non-negotiables).
