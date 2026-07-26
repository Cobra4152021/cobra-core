# RRF Failure Taxonomy

Each `FailureCategory` declares: `retryable`, `fallback_eligible`, `circuit_breaker_relevant`, `operator_action_required`, `safe_public_message`.

Retryable examples: `provider_timeout`, `connection_failure`, `provider_unavailable`, `provider_overloaded`, `rate_limited`.

Never retried: `authentication_failure`, `authorization_failure`, `capability_unavailable`, `policy_blocked`, `budget_exceeded`, `cancelled`, human-governance / evidence / skill errors (handled before RRF).
