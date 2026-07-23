# CobraBench v0.2-rc2 Diversity Review

**Phase:** 2I

## Observations

* Shared system prompt across cases (intentional).
* Source-count distribution: {1: 21, 2: 17, 3: 8}
* Top dates: [('2026-01-01', 6), ('2026-04-18', 5), ('2026-05-01', 5), ('2026-03-03', 3), ('2026-04-01', 3)]
* Repeated prompt openings: 0

## Exploitability

A model could learn the shared system prompt and S1/S2 citation style, but case-specific evidence still differs.
Date clustering and template regularity are **diversity limitations**, not contamination.

## Conclusion

No release-blocking leakage. Diversity warnings remain documentation-level (D1/D2).
