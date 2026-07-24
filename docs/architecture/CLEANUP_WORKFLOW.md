# Cleanup workflow

Mandatory after every cloud qualification or aborted attempt. Goal: **zero remaining billable Phase resources**.

## Steps

1. Export all diagnostics / candidate / cost notes to the workstation (or confirm already committed).
2. From the operator workstation (with `RUNPOD_API_KEY` set):

   ```bash
   python scripts/phase3g_cleanup_verify.py --pod-id <POD_ID> --terminate
   ```

3. Confirm API reports pod terminated / absent.
4. Confirm no second Phase pod remains (script remaining-resource audit).
5. Delete local gitignored connection files if present:
   - `evaluations/cloud/.pod-connection.local.json`
   - `evaluations/cloud/.ssh-*.local*`
   - `evaluations/cloud/provision-preflight.json`
6. Record cleanup in `cleanup-verification.json` style evidence when freezing a release.

## Safety

| Rule | Rationale |
| --- | --- |
| Require explicit `--pod-id` | Prevents accidental mass terminate |
| Do not embed API keys in scripts | Secrets via environment only |
| Prefer terminate over stop-only | Stopped pods may still bill storage/idle depending on provider |
| Verify after terminate | Detect orphaned volumes/endpoints |

## Failure modes

| Symptom | Action |
| --- | --- |
| Terminate API error | Retry; check key scope; manual console terminate; re-run verify |
| Pod gone but volume remains | Delete volume if Phase-owned; document in cost record |
| SSH files left locally | Delete gitignored locals; never commit |

## Phase 3F reference

Pod `txw75nv9hn96hu` terminated after Outcome A; estimated spend ~$1.38; cleanup verification included in `docs/releases/phase-3f/cloud/cleanup-verification.json`.
