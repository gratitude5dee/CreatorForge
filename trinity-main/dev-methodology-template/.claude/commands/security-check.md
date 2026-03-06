# Pre-Commit Security Check

Validate that staged changes don't contain sensitive information before committing.

## Instructions

Run these checks on staged files (or all modified files if nothing staged):

### 1. Get files to check

```bash
# Check if there are staged files
STAGED=$(git diff --cached --name-only 2>/dev/null)

if [ -n "$STAGED" ]; then
  echo "Checking staged files..."
  FILES="$STAGED"
else
  # Fall back to all modified files
  echo "No staged files. Checking all modified files..."
  FILES=$(git diff --name-only HEAD 2>/dev/null)
fi

echo "$FILES"
```

### 2. Check for API keys and tokens

Search for common API key patterns in the changed files:

```bash
# Common API key patterns
git diff --cached -U0 | grep -iE '(sk-[a-zA-Z0-9]{20,}|pk-[a-zA-Z0-9]{20,}|ghp_[a-zA-Z0-9]{36}|gho_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9]{22,}|xox[baprs]-[a-zA-Z0-9-]{10,}|ya29\.[a-zA-Z0-9_-]{50,}|AIza[a-zA-Z0-9_-]{35}|AKIA[A-Z0-9]{16})'
```

**Patterns checked:**
- `sk-...` — Anthropic/OpenAI secret keys
- `pk-...` — Public keys
- `ghp_...`, `gho_...`, `github_pat_...` — GitHub tokens
- `xox...` — Slack tokens
- `ya29....` — Google OAuth tokens
- `AIza...` — Google API keys
- `AKIA...` — AWS access keys

### 3. Check for email addresses

```bash
# Find emails that aren't example/placeholder
git diff --cached -U0 | grep -oE '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}' | grep -vE '(example\.com|example\.org|placeholder|test@|user@example|noreply@)'
```

**Allowed patterns:**
- `@example.com`, `@example.org`
- `test@`, `user@example`
- `noreply@`

### 4. Check for IP addresses

```bash
# Find IP addresses (excluding localhost patterns)
git diff --cached -U0 | grep -oE '\b([0-9]{1,3}\.){3}[0-9]{1,3}\b' | grep -vE '^(127\.|0\.0\.0\.0|localhost)'
```

**Note:** Internal IPs (10.x, 192.168.x, 172.16-31.x) and public IPs should be flagged.

### 5. Check for .env files with values

```bash
# Check if any .env files are staged (not .env.example)
git diff --cached --name-only | grep -E '^\.env$|/\.env$' | grep -v '\.example'
```

**Rule:** Never commit `.env` files. Only `.env.example` with placeholder values.

### 6. Check for hardcoded secrets in code

```bash
# Look for common secret variable patterns with values
git diff --cached -U0 | grep -iE '(password|secret|token|api_key|apikey|auth_token|access_token|private_key)\s*[=:]\s*["\x27][^"\x27]{8,}["\x27]' | grep -vE '(process\.env|os\.environ|os\.getenv|\$\{|example|placeholder|your-|changeme|xxx)'
```

### 7. Check for internal URLs/domains

```bash
# Look for internal-looking URLs (customize based on your org)
git diff --cached -U0 | grep -iE '(internal\.|\.internal|\.local|\.corp|\.lan|staging\.|dev\..*\.com)' | grep -vE '(localhost|127\.0\.0\.1|example)'
```

### 8. Check for credential files

```bash
# Check for credential/key files being committed
git diff --cached --name-only | grep -iE '(credentials\.json|service.?account.*\.json|\.pem$|\.key$|id_rsa|id_ed25519|\.p12$|\.pfx$|htpasswd)'
```

## Report Format

After running all checks, report:

```markdown
## Security Check Results

### Summary
| Check | Status | Findings |
|-------|--------|----------|
| API Keys | ✅/❌ | count |
| Email Addresses | ✅/❌ | count |
| IP Addresses | ✅/❌ | count |
| .env Files | ✅/❌ | count |
| Hardcoded Secrets | ✅/❌ | count |
| Internal URLs | ✅/❌ | count |
| Credential Files | ✅/❌ | count |

### Issues Found (if any)

#### [Category]
- File: `path/to/file`
- Line: `suspicious content here...`
- Risk: [Why this is a problem]
- Fix: [How to remediate]

### Recommendations

1. [Action items if issues found]
2. [Or "Safe to commit" if clean]
```

## Severity Levels

| Level | Action | Examples |
|-------|--------|----------|
| **CRITICAL** | Do NOT commit | API keys, tokens, passwords |
| **HIGH** | Remove before commit | Real emails, internal IPs |
| **MEDIUM** | Review carefully | .env files, credential paths |
| **LOW** | Verify intentional | Internal URLs, domain names |

## Quick Fixes

### Remove sensitive data from staged files

```bash
# Unstage a specific file
git reset HEAD path/to/file

# Remove sensitive line and re-stage
# (edit file manually, then)
git add path/to/file
```

### If already committed (not pushed)

```bash
# Amend the last commit after fixing
git add -A
git commit --amend --no-edit
```

### If already pushed

**CRITICAL**: Rotate any exposed credentials immediately, then:
```bash
# Use git-filter-repo or BFG to remove from history
# (credentials are already compromised - focus on rotation)
```

## When to Use

- **Before every commit** — Run `/security-check` as habit
- **Before PRs** — Mandatory check before opening PR
- **Code review** — Reviewer should run on PR branch
- **CI/CD** — Automate as pre-commit hook or CI step

## False Positives

Some patterns may trigger false positives:

| Pattern | Likely False Positive |
|---------|----------------------|
| `sk-` | Variable names like `skip`, `sketch` |
| IP addresses | Version numbers (1.2.3.4), test data |
| Emails | Documentation examples |

Review each finding in context before deciding.

## Automation

To run automatically on every commit, add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
# Run security check - block commit if critical issues found
# (Requires manual implementation of checks above)
echo "Running security check..."
# Add automated checks here
```

## Related

- `CLAUDE.md` — Security guidelines for this repository
- `.gitignore` — Files excluded from commits
- `docs/DEVELOPMENT_WORKFLOW.md` — Development process
