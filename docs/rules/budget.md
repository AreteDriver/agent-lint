# Budget Rules (B001-B004)

Budget rules detect cost risks in agent workflows.

## B001: Missing Workflow Token Budget

**Severity:** Warning  
**Autofix:** ✅ Yes — adds `token_budget: 50000`

Flags workflows that have no top-level `token_budget` declared. Without a budget cap, a runaway loop or oversized prompt can generate unlimited API costs.

## B002: Step Exceeds 50% of Budget

**Severity:** Warning

Flags individual steps whose `estimated_tokens` exceeds 50% of the workflow's total `token_budget`. This indicates a single step is disproportionately expensive.

## B003: Missing Step Token Estimate

**Severity:** Info

Flags LLM steps that lack an `estimated_tokens` field. Cost estimation requires either a declared value or a fallback archetype.

## B004: Budget Archetype Fallback

**Severity:** Info

Informational finding when a step's token estimate falls back to a role-based or step-type archetype because no explicit value was provided.
