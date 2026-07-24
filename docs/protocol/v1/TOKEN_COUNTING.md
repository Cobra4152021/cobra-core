# Protocol V1 — Token counting

| Mode | Prompt / completion tokens |
| --- | --- |
| `mock` / `echo` / `test` | Deterministic `ceil(chars/4)` over joined prompt text and completion text |
| `local` / `qwen-local` | Tokenizer counts from `QwenLocalAdapter` (`input_token_count` / `output_token_count`) when present; otherwise falls back to approx |

`total_tokens` is always `prompt_tokens + completion_tokens` on successful responses.

Context truncation uses the same approx (`ceil(chars/4)`) for deterministic pre-generation checks in all modes (frozen fixture behavior).
