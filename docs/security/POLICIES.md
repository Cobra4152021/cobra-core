# Policies

Policies answer: who may perform which action on which resource under which conditions.

## Decision effects

- `allow`
- `deny`
- `conditional`

## Evaluation order (deterministic)

1. Matching rules sorted by `(priority, policy_id)`
2. Explicit **deny** wins
3. **Conditional** when applicable attributes present (e.g. `owner`)
4. Explicit **allow** (still requires mapped permission)
5. Role permission grant allow
6. **Default deny**

## Built-in examples

| Policy | Result |
|--------|--------|
| Observer → retrieve evidence | Deny |
| Investigator → run workflow | Allow |
| Reviewer → approve findings | Allow |
| Owner close case (supervisor) | Allow when `owner == principal` |
