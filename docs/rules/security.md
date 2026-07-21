# Security Rules (S001-S004)

Security rules detect patterns that expose credentials, enable injection, or leak sensitive data.

## S001: Shell Injection Risk

**Severity:** Error

Flags shell steps that use `${var}` variable interpolation in commands. Untrusted input can escape the interpolation and execute arbitrary commands.

## S002: Hardcoded Path

**Severity:** Warning

Flags shell steps that contain hardcoded absolute paths (`/usr/...`, `/home/...`, `C:\...`). These are non-portable and may break in containerized or cross-platform environments.

## S003: Untyped Required Input

**Severity:** Error  
**Autofix:** ✅ Yes — adds `type: string`

Flags required workflow inputs that have no `type` constraint. Without a type, invalid input can propagate downstream and cause runtime failures.

## S004: Missing Secret Mask

**Severity:** Warning

Flags steps that reference API keys or tokens in plain text without masking. Secrets should be injected via environment variables or a secrets manager.
