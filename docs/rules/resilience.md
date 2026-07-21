# Resilience Rules (R001-R005)

Resilience rules detect failure-handling gaps that can cause workflows to hang, retry forever, or crash without recovery.

## R001: Missing on_failure Handler

**Severity:** Warning

Flags LLM steps that have no `on_failure` strategy. If the LLM call fails (rate limit, timeout, invalid response), the workflow will abort with no recovery.

## R002: Abort with No Fallback

**Severity:** Warning

Flags steps that use `on_failure: abort` without a fallback step. This is intentional halting, but dangerous if there is no downstream cleanup.

## R003: Retry Without max_retries

**Severity:** Warning  
**Autofix:** ✅ Yes — adds `max_retries: 3`

Flags steps with `on_failure: retry` but no `max_retries` limit. This can create an infinite retry loop.

## R004: Shell Step Without Timeout

**Severity:** Warning  
**Autofix:** ✅ Yes — adds `timeout_seconds: 300`

Flags shell steps that lack a `timeout_seconds`. A hanging subprocess will block the workflow indefinitely.

## R005: Missing Checkpoint

**Severity:** Info

Flags long-running workflows (more than 5 steps) that have no checkpoint step. Checkpoints allow partial recovery on failure.
