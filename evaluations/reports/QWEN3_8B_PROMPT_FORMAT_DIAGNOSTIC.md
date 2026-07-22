# Qwen3-8B Prompt-Format Diagnostic (Cohort C)

**Status:** Deferred — blocked before generation (environment).  
**Planned case:** `cb-027-exact-output-format`  
**Variants:** original / clarified_format / schema_oriented

## Baseline static finding

Content satisfied FINDING / RISK / NEXT semantics; presentation used markdown bullets/bold rather than exact `LABEL:` lines → syntactic / prompt / parser mix (**P**+**S**), not pure semantic failure.

## Interim conclusion

Prompt clarification is the first Class 2 experiment when GPU is free. Do not train for markdown style.
