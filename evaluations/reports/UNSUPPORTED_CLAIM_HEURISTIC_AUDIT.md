# Unsupported-Claim Heuristic Audit

**Run ID:** `20260722T200000Z-8bba5e01`  
**Generated:** 2026-07-22T21:41:51.595571+00:00  
**Method:** Re-extracted sentence-level flags using `citation_metrics` heuristics; conservative manual-style labeling by comparing claim-like sentences to source text.

## Aggregate baseline metric

- Reported aggregate `unsupported_claim_count`: **172**
- Re-extracted candidate flags (all cases): **145**
- Labeled audit sample size: **50** (target ≥ 50)

## Precision estimate

- Labels classified as true unsupported: **0** / 50
- **Precision (conservative): 0.0%**
- **False-positive rate (supported/harmless labels): 100.0%**

## Label distribution (sample)

- `harmless_connective`: 11
- `inference_clearly_labeled`: 2
- `supported_paraphrase`: 37

## Errors by category (sample)

### citation_correctness
- `harmless_connective`: 6
- `inference_clearly_labeled`: 1
- `supported_paraphrase`: 9

### contradiction_detection
- `harmless_connective`: 1
- `supported_paraphrase`: 7

### evidence_grounding
- `harmless_connective`: 2
- `supported_paraphrase`: 10

### investigation_reasoning
- `harmless_connective`: 2
- `inference_clearly_labeled`: 1
- `supported_paraphrase`: 9

### long_document_analysis
- `supported_paraphrase`: 2

## Interpretation

The automated layer flags many sentences that human review rated H0. Most sample flags are supported paraphrases, structural formatting, or sentences where citation keys are present but token-overlap matching is too strict.

**Do not treat the aggregate count of 172 as a model-quality finding** without heuristic revision and rescoring under a new version.

## Sample flags (first 15)

- `cb-003-citation-unsupported-claim-detection` [harmless_connective]: **Supported Findings:**

1
- `cb-003-citation-unsupported-claim-detection` [supported_paraphrase]: Deletion of retention-covered logs requires dual approval from the data steward and the project lead
- `cb-003-citation-unsupported-claim-detection` [harmless_connective]: **Unsupported Claims:**

1
- `cb-003-citation-unsupported-claim-detection` [supported_paraphrase]: **Alleged March Deletion Event:**  
   There is no direct evidence or confirmation of a deletion event in [SRC-P2]
- `cb-003-citation-unsupported-claim-detection` [supported_paraphrase]: While the ticket mentions an issue with dashboard widgets showing empty panels for dates before 2024-03-01, it does not …
- `cb-003-citation-unsupported-claim-detection` [supported_paraphrase]: The ticket status is "investigating," and no confirmation of deletion is recorded
- `cb-003-citation-unsupported-claim-detection` [harmless_connective]: Therefore, any claim about a March deletion event is **UNSUPPORTED**.
- `cb-015-citation-key-discipline` [harmless_connective]: (SRC-B)
- `cb-016-misattributed-quote-detection` [harmless_connective]: Memo B does not confirm budget approval
- `cb-016-misattributed-quote-detection` [supported_paraphrase]: It states that "Finance notes BR-10 requires vendor quotes before approval." This indicates that the budget request BR-1…
- `cb-016-misattributed-quote-detection` [supported_paraphrase]: Source: [SRC-B]
- `cb-017-citation-for-inference` [supported_paraphrase]: The sources do not provide direct evidence that server S-9 was rebooted
- `cb-017-citation-for-inference` [inference_clearly_labeled]: Therefore, any conclusion about a reboot would be an inference based on the absence of explicit information
- `cb-017-citation-for-inference` [harmless_connective]: **Inference:** The lack of mention of a reboot in the monitoring alert does not confirm or deny a reboot occurred
- `cb-017-citation-for-inference` [supported_paraphrase]: It is possible that the server was rebooted, but this cannot be confirmed from the given information
