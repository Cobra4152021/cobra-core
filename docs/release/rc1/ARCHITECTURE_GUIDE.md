# Architecture Guide — RC1

```
Client → /api/v1 (PASF) → ISPF → MOTF-scoped resources
                              ↓
                    Cases / Workflows / Evidence refs
                    ISF / KEF / Plugins / Benchmark / OCP
                              ↓
                         Protocol V1 / CIAL / AIR / RRF
```

Admin/ops surfaces (not public marketplace API): `/operations/*`, `/production/*`, `/security/*`, `/plugins/*`, `/organizations/*`, `/kef/*`.

See ADRs under `docs/` for each framework (AIR, ISF, KEF, RRF, Benchmark, OCP, PEF, ISPF, MOTF, PASF, PRHF).
