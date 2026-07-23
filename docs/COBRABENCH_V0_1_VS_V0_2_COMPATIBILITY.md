# CobraBench v0.1 versus v0.2 Compatibility

## Summary

Historical **0.840** remains valid only under CobraBench **v0.1** and its original evaluator versions.
A v0.2-rc1 or v0.2-rc2 score must **not** be presented as direct improvement or decline versus 0.840 without qualification.

## Phase 2H independent-review findings

* Outcome **B**: rc1 not finalized; **rc2** created with targeted corrections.
* Category **definitions** unchanged.
* Category **weights** unchanged between rc1 and rc2.
* Evaluator **versions** unchanged (still 2.0.0 / telemetry 1.0.0).
* Evaluator **assignments** changed for some cases (refusal citation pins removed; contradiction pins added; JSON template reassigned).
* Objective checks and human dimensions strengthened in rc2.
* Some titles, one source title, and some difficulty levels changed in rc2.

## Why scores are not interchangeable

| Dimension | v0.1 | v0.2-rc1 | v0.2-rc2 |
| --- | --- | --- | --- |
| Categories | 9 | 10 | 10 (same) |
| Weights | v0.1 table | v0.2 table | same as rc1 |
| Unsupported-claim evaluator | v1 | v2 | v2 |
| Citation metrics | basic | v2 coverage suite | v2 (assignment differs on refusal) |
| Contradiction | collapsed | 10 submetrics | 10 submetrics (+pins on selected grounding/long-doc) |
| Evidence keys | SRC-* | S# | S# |
| Format scoring | mixed | semantic vs exact | semantic vs exact |
| Case prompts / titles | n/a | rc1 text | some metadata/prompt-visible titles revised |

## rc1 → rc2 differences (score impact)

Material compatibility breaks:

* Refusal cases no longer require citation evaluator success for a correct refusal.
* cb2-027 source title no longer cues timezone (`UTC log` removed).
* Stronger objective checks change automated pass/fail surface.
* Difficulty labels revised (metadata; may affect stratified reporting).

Do **not** compare rc1 and rc2 overall scores as a pure model delta.

## No conversion formula

No statistically supported conversion among v0.1, v0.2-rc1, and v0.2-rc2 overall scores is provided.
Do not invent one.

## Reporting rules

* Always display benchmark release ID and evaluator versions.
* Keep v0.1 leaderboards separate from v0.2-rc* diagnostics.
* Official Phase 2D baseline artifacts must not be overwritten by v0.2 runs.
* Final v0.2 does not yet exist (Phase 2H).
