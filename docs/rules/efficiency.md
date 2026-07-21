# Efficiency Rules (E001-E004)

Efficiency rules detect patterns that waste tokens, time, or compute.

## E001: Parallelizable Sequential Steps

**Severity:** Info

Flags adjacent LLM steps with no data dependency between them. These can often be run in parallel to reduce wall-clock time.

## E002: Unnecessary Checkpoint

**Severity:** Info

Flags checkpoint steps in short workflows (fewer than 5 steps). The checkpoint overhead may exceed the recovery benefit.

## E003: Duplicate Step

**Severity:** Warning

Flags steps that appear to be exact duplicates of an earlier step. Often indicates copy-paste errors.

## E004: Fan-out Without max_concurrent

**Severity:** Warning  
**Autofix:** ✅ Yes — adds `max_concurrent: 4`

Flags `fan_out` steps that lack a `max_concurrent` limit. Without a limit, the workflow may attempt to spawn more parallel branches than the infrastructure can handle.
