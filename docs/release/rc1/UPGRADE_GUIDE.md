# Upgrade Guide — RC1

## From 0.9.0rc1 / KC-032 tip

1. Take PRHF backup (`BACKUP.create()`).
2. Deploy `v1.0.0-rc1` build to staging.
3. Run migrations dry-run; apply pending framework migrations if approved.
4. Verify OpenAPI checksum against freeze manifest.
5. Re-run security review + load suite (100→5000).
6. Restore drill (dry-run then apply) in a non-prod clone.

## Compatibility

- `/api/v1` is frozen — breaking changes require `/api/v2`.
- Plugin manifests remain schema v1 under allow-listed entry prefixes.
- Cross-org access remains denied by default.
