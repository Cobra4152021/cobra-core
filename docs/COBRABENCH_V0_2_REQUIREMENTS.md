# CobraBench v0.2 Requirements

**Status:** Binding for v0.2-rc1 construction  
**Date:** 2026-07-22

## Purpose

> CobraBench evaluates whether an AI system can perform evidence-first investigation work accurately, transparently, cautiously, and usefully.

## Priorities

The benchmark must prioritize:

* evidence grounding,
* claim-to-source traceability,
* contradiction handling,
* fact-versus-inference separation,
* uncertainty calibration,
* hallucination resistance,
* missing-information recognition,
* proportional recommendations,
* structured output reliability,
* investigation usefulness.

## Non-goals / anti-rewards

The benchmark must **not** primarily reward:

* verbosity,
* polished prose,
* broad world knowledge,
* unsupported creativity,
* confident guessing,
* stylistic similarity to a reference answer.

## Safety and content constraints

Cases may use only synthetic, public-domain, or permissively licensed fragments.
No private investigations, PII, medical/employment records, or substantial copyrighted text.

## Compatibility

CobraBench v0.1 remains frozen. v0.2 scores are not directly comparable to the official 0.840 interim result.
