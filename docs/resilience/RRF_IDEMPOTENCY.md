# RRF Idempotency

`execution_id = H(skill_id|skill_version|correlation_id|revision|profile)` — never from prompts/evidence bodies.

Same execution id returns the cached successful result without creating duplicate proposals. Revision change → new execution.
