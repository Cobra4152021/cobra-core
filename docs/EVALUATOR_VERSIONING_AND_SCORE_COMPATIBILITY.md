# Evaluator Versioning and Score Compatibility

## Why evaluator changes alter scores

Parsers, claim classifiers, and coverage definitions change which outputs pass or fail.
A lower unsupported-claim count under v2 does **not** mean the model improved; it usually means the evaluator got less noisy.

## Why old results remain valid

Official CobraBench v0.1 results remain valid under their original evaluator versions
(for example `cobrabench-evaluator-v0.1.0` and unsupported-claims `1.0.0`).
Historical artifacts must keep their version pins.

## When historical outputs may be rescored

Rescoring is allowed for **diagnostics** when:

- inputs are read-only references to frozen outputs,
- outputs are written to new directories,
- reports are labeled as offline diagnostic results,
- the official baseline score is not replaced.

## Why rescoring is diagnostic, not retroactive replacement

Replacing 0.840 with a v2-derived number would erase the measurement contract of Phase 2D.
v2 metrics are comparative diagnostics only.

## How future reports must display versions

Every evaluation result should identify:

- evaluator name
- evaluator version
- implementation / rule-set / parser / scoring versions
- configuration hash when available

## Mixed-version leaderboards

v1 and v2 overall scores are not directly comparable.
Do not rank models across different evaluator major versions without an explicit compatibility waiver.
Prevent mixed-version leaderboards by requiring matching evaluator version pins.
