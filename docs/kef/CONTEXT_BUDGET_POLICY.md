# Context Budget Policy

Before model execution KEF enforces:

- max chunks / chars per item
- max total evidence characters
- max estimated evidence tokens

Required evidence that cannot fit → `evidence_context_budget_exceeded` (never silently omitted).
