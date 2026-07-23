"""Unsupported-claim evaluator v2 — classify-then-support analysis."""

from __future__ import annotations

import re
from collections.abc import Iterable

from cobra_core.evaluation.citations import extract_citation_keys
from cobra_core.evaluators.unsupported_claims.types import (
    EXCLUDED_FROM_SUPPORT_ANALYSIS,
    ClaimClass,
    ClaimSpanResult,
    SupportState,
    UnsupportedClaimEvaluation,
)

EVALUATOR_VERSION = "2.0.0"

_SENTENCE_SPLIT = re.compile(r"[.!?]+\s+")
_HEADING = re.compile(r"^(#{1,6}\s+|\*\*[^*]+\*\*\s*:?\s*$|[A-Z][A-Za-z /-]{0,40}:\s*$)")
_CITATION_KEY = re.compile(r"\bSRC-[A-Z0-9]+\b|\bS\d+\b|\[S\d+\]|\[SRC-[A-Z0-9]+\]")
_INFERENCE_MARKERS = re.compile(
    r"\b(inference|infer|likely|may|might|possibly|unclear|unknown|"
    r"insufficient|cannot confirm|no direct evidence|not confirmed)\b",
    re.IGNORECASE,
)
_RECOMMENDATION = re.compile(
    r"\b(recommend|should|next step|investigate|verify|request|follow[- ]up)\b",
    re.IGNORECASE,
)
_QUESTION = re.compile(r"\?\s*$")
_CONNECTIVE = re.compile(
    r"^(therefore|however|additionally|in summary|overall|note|thus|also)\b",
    re.IGNORECASE,
)
_INSTRUCTION = re.compile(
    r"\b(you are|supporting sources|cite using|use only the provided|"
    r"answer using exactly|do not invent)\b",
    re.IGNORECASE,
)
_OVERSTATEMENT = re.compile(
    r"\b(definitely|certainly|proven|confirmed|undeniably|without doubt)\b",
    re.IGNORECASE,
)


def _split_spans(text: str) -> list[str]:
    stripped = text.strip()
    if not stripped:
        return []
    parts = [p.strip() for p in _SENTENCE_SPLIT.split(stripped) if p.strip()]
    return parts if parts else [stripped]


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def _token_overlap_supported(sentence: str, source_text: str) -> bool:
    tokens = [t for t in re.findall(r"[a-z0-9]{4,}", source_text.lower())]
    sentence_norm = _normalize(sentence)
    return any(token in sentence_norm for token in tokens[:20])


def _linked_keys(sentence: str, allowed_keys: Iterable[str]) -> list[str]:
    found = extract_citation_keys(sentence)
    # Also accept S1 / [S1] style for prospective standards.
    extras = re.findall(r"\[?(S\d+|SRC-[A-Z0-9]+)\]?", sentence, flags=re.IGNORECASE)
    ordered: list[str] = []
    seen: set[str] = set()
    for key in [*found, *[e.upper() if e.upper().startswith("SRC") else e.upper() for e in extras]]:
        canon = key.upper()
        if canon not in seen:
            seen.add(canon)
            ordered.append(canon)
    allowed_upper = {k.upper() for k in allowed_keys}
    return [k for k in ordered if k in allowed_upper or k.startswith("S")]


def classify_span(text: str, *, allowed_keys: list[str], sources: dict[str, str]) -> ClaimClass:
    stripped = text.strip()
    lower = stripped.lower()
    if not stripped or len(stripped) < 6:
        return ClaimClass.CONNECTIVE_LANGUAGE
    if _HEADING.match(stripped) or lower.startswith(("**supported", "**unsupported", "###", "##")):
        return ClaimClass.HEADING
    if stripped.startswith(("- ", "* ", "1.", "2.", "3.")) and len(stripped) < 24:
        return ClaimClass.STRUCTURAL_TEXT
    if _INSTRUCTION.search(stripped):
        return ClaimClass.INSTRUCTION_REPETITION
    if _QUESTION.search(stripped):
        return ClaimClass.QUESTION
    if _CONNECTIVE.match(stripped) and len(stripped.split()) <= 10:
        return ClaimClass.CONNECTIVE_LANGUAGE
    if (
        _RECOMMENDATION.search(stripped)
        and not _OVERSTATEMENT.search(stripped)
        and ("recommend" in lower or "should" in lower or "next step" in lower)
    ):
        return ClaimClass.RECOMMENDATION
    if any(
        marker in lower for marker in ("open question", "missing information", "unknown whether")
    ):
        return ClaimClass.UNCERTAINTY_STATEMENT
    if _INFERENCE_MARKERS.search(stripped) and (
        "inference" in lower or "may " in lower or "might " in lower or "unclear" in lower
    ):
        return ClaimClass.EXPLICITLY_LABELED_INFERENCE

    cited = _linked_keys(stripped, allowed_keys)
    if cited:
        supports = 0
        for key in cited:
            # Map S1-style to SRC if present in sources by normalized lookup.
            source = sources.get(key) or sources.get(key.replace("S", "SRC-"))
            if source is None:
                # try matching SRC-* values
                for sk, sv in sources.items():
                    if sk.upper() == key or key.endswith(sk.split("-")[-1]):
                        source = sv
                        break
            if source and _token_overlap_supported(stripped, source):
                supports += 1
        if supports >= 1:
            return ClaimClass.EVIDENCE_PARAPHRASE
        return ClaimClass.EVIDENCE_PARAPHRASE  # cited claim: treat as paraphrase, not fabrication

    # Quoted evidence fragments
    for source in sources.values():
        snippet = _normalize(source)[:80]
        if snippet and snippet in _normalize(stripped):
            return ClaimClass.QUOTED_SUPPLIED_EVIDENCE

    if _INFERENCE_MARKERS.search(stripped):
        return ClaimClass.EXPLICITLY_LABELED_INFERENCE

    # Short connective-like lines without digits
    words = stripped.split()
    if len(words) <= 8 and not any(ch.isdigit() for ch in stripped) and not cited:
        return ClaimClass.CONNECTIVE_LANGUAGE

    if any(ch.isdigit() for ch in stripped) or len(words) >= 9:
        return ClaimClass.UNSUPPORTED_CANDIDATE
    return ClaimClass.UNKNOWN


def _support_state_for(
    claim_class: ClaimClass,
    text: str,
    cited: list[str],
    sources: dict[str, str],
) -> tuple[SupportState, list[str], list[str], float]:
    rules: list[str] = []
    if claim_class in EXCLUDED_FROM_SUPPORT_ANALYSIS:
        return SupportState.NOT_APPLICABLE, cited, [], 0.9

    if claim_class == ClaimClass.EXPLICITLY_LABELED_INFERENCE:
        return SupportState.REASONABLE_LABELED_INFERENCE, cited, cited, 0.8

    if claim_class == ClaimClass.UNCERTAINTY_STATEMENT:
        return SupportState.NOT_APPLICABLE, cited, [], 0.85

    if claim_class == ClaimClass.EVIDENCE_PARAPHRASE:
        linked = []
        for key in cited:
            source = sources.get(key, "")
            if source and _token_overlap_supported(text, source):
                linked.append(key)
        if len(linked) >= 2:
            return SupportState.SUPPORTED_BY_MULTIPLE, cited, linked, 0.75
        if linked:
            return SupportState.DIRECTLY_SUPPORTED, cited, linked, 0.8
        if cited:
            return SupportState.PARTIALLY_SUPPORTED, cited, cited, 0.55
        return SupportState.CANNOT_DETERMINE, cited, [], 0.4

    if claim_class == ClaimClass.UNSUPPORTED_CANDIDATE:
        rules.append("rule:uncited_material_factual_candidate")
        if _OVERSTATEMENT.search(text):
            return SupportState.OVERSTATES_EVIDENCE, cited, [], 0.55
        if not cited:
            # Still uncertain without semantic entailment.
            return SupportState.CANNOT_DETERMINE, cited, [], 0.45
        return SupportState.UNSUPPORTED, cited, [], 0.5

    return SupportState.CANNOT_DETERMINE, cited, [], 0.35


def evaluate_unsupported_claims_v2(
    response: str,
    allowed_keys: list[str],
    supporting_source_texts: dict[str, str] | None = None,
) -> UnsupportedClaimEvaluation:
    """
    Classify spans, then analyze support only for appropriate claim classes.

    Deterministic offline framework — uncertain cases are marked cannot_determine.
    Does not claim full semantic truth determination.
    """
    sources = supporting_source_texts or {}
    spans: list[ClaimSpanResult] = []
    unsupported = 0
    analyzed = 0
    uncertain = 0

    for idx, text in enumerate(_split_spans(response), start=1):
        claim_class = classify_span(text, allowed_keys=allowed_keys, sources=sources)
        cited = _linked_keys(text, allowed_keys)
        enters = claim_class not in EXCLUDED_FROM_SUPPORT_ANALYSIS and claim_class not in {
            ClaimClass.UNCERTAINTY_STATEMENT,
            ClaimClass.UNKNOWN,
        }
        if claim_class in {
            ClaimClass.FACTUAL_CLAIM,
            ClaimClass.UNSUPPORTED_CANDIDATE,
            ClaimClass.EVIDENCE_PARAPHRASE,
            ClaimClass.EXPLICITLY_LABELED_INFERENCE,
        }:
            analyzed += 1
            enters = True

        support, cited_out, linked, confidence = _support_state_for(
            claim_class, text, cited, sources
        )
        flagged = support in {SupportState.UNSUPPORTED, SupportState.OVERSTATES_EVIDENCE}
        # Only flag when classification is unsupported_candidate AND unsupported/overstates
        if claim_class != ClaimClass.UNSUPPORTED_CANDIDATE:
            flagged = False
        if (
            support == SupportState.CANNOT_DETERMINE
            and claim_class == ClaimClass.UNSUPPORTED_CANDIDATE
        ):
            # Conservative: do not emit unsupported flag without stronger evidence.
            flagged = False
            uncertain += 1
        if flagged:
            unsupported += 1

        rationale = (
            f"class={claim_class.value}; support={support.value}; "
            f"cited={','.join(cited_out) or 'none'}"
        )
        spans.append(
            ClaimSpanResult(
                span_id=f"span-{idx:03d}",
                text=text,
                claim_class=claim_class,
                support_state=support,
                cited_keys=cited_out,
                linked_evidence_ids=linked,
                enters_support_analysis=enters,
                flagged_as_unsupported=flagged,
                confidence=confidence,
                rationale=rationale,
                rule_ids=["classify_span_v2", "support_state_v2"],
            )
        )

    return UnsupportedClaimEvaluation(
        evaluator_version=EVALUATOR_VERSION,
        spans=spans,
        unsupported_flag_count=unsupported,
        analyzed_claim_count=analyzed,
        uncertain_count=uncertain,
        notes=(
            "Offline deterministic framework. "
            "cannot_determine does not mean fabricated. "
            "Does not fully determine semantic truth."
        ),
    )
