---
name: validate-pr
description: Validate a pull request against the Trinity development methodology and generate a merge decision report.
allowed-tools: [Bash, Read, Grep]
user-invocable: true
argument-hint: "<pr-number-or-url>"
automation: gated
---

# Validate Pull Request

Validate a pull request against the Trinity development methodology and generate a merge decision report.

## State Dependencies

| Source | Location | Read | Write | Description |
|--------|----------|------|-------|-------------|
| PR Details | GitHub API | ✅ | | PR metadata and diff |
| Changelog | `docs/memory/changelog.md` | ✅ | | Entry check |
| Requirements | `docs/memory/requirements.md` | ✅ | | Req updates |
| Architecture | `docs/memory/architecture.md` | ✅ | | API changes |
| Feature Flows | `docs/memory/feature-flows/` | ✅ | | Flow updates |
| GitHub Issues | `abilityai/trinity` | ✅ | | Issue references |

## Usage

```
/validate-pr <pr-number-or-url>
```

## Process

### Step 1: Fetch PR Information

```bash
# Get PR number from argument (extract from URL if needed)
PR_NUMBER=<extract number from argument>

# Fetch PR details
gh pr view $PR_NUMBER --json title,body,author,baseRefName,headRefName,files,additions,deletions,changedFiles

# Get list of changed files
gh pr diff $PR_NUMBER --name-only

# Get the actual diff for analysis
gh pr diff $PR_NUMBER
```

Store this information for validation:
- PR title and description
- Changed files list
- Base and head branches
- Author

### Step 2: Validate Documentation Updates

#### 2.1 Changelog Entry (REQUIRED)
Check if `docs/memory/changelog.md` is in the changed files list.

**If present**, read the diff and verify:
- [ ] Entry is at the TOP of recent changes (newest first)
- [ ] Has timestamp format: `### YYYY-MM-DD HH:MM:SS`
- [ ] Has emoji prefix (🎉✨🔧🔄📝🔒🚀💾🐳)
- [ ] Includes summary of what changed and why
- [ ] Lists key files modified

**If missing**: Flag as ❌ FAIL - "Changelog not updated"

#### 2.2 GitHub Issues Update (CONDITIONAL)
Check if PR references a GitHub Issue (e.g., "Closes #17", "Fixes #23").

**Required if**:
- PR completes a roadmap item → issue should be closed by PR
- PR discovers new work → new issue created with appropriate labels

**Validation**:
- [ ] PR references related issue(s) in description
- [ ] Issue has correct priority label (priority-p0/p1/p2/p3)
- [ ] Issue has correct type label (type-feature/bug/refactor)

#### 2.3 Requirements Update (CONDITIONAL)
Check if `docs/memory/requirements.md` is in the changed files list.

**Required if**:
- PR adds new functionality
- PR changes feature scope
- PR implements a new requirement

**Validation**:
- [ ] New features have requirement entry
- [ ] Status labels are correct (⏳🚧✅❌)
- [ ] Requirement has description and key features

#### 2.4 Architecture Update (CONDITIONAL)
Check if `docs/memory/architecture.md` is in the changed files list.

**Required if** PR modifies:
- API endpoints (new or changed)
- Database schema
- External integrations
- System components

**Validation**:
- [ ] New endpoints added to API tables
- [ ] Database schema changes documented
- [ ] Component diagrams updated if needed

### Step 3: Validate Feature Flows

#### 3.1 Check for Feature Flow Changes
Look for files matching `docs/memory/feature-flows/*.md` in changed files.

#### 3.2 If Feature Behavior Changed (but no flow updated)
Analyze the code changes to determine if they modify feature behavior:
- Changes to API endpoints
- Changes to frontend components with user interactions
- Changes to database operations
- Changes to business logic

**If behavior changed but no feature flow updated**: Flag as ⚠️ WARNING - "Feature behavior changed, flow may need update"

#### 3.3 Validate Feature Flow Format
For each changed feature flow file, verify structure:

**Required Sections** (check headings exist):
- [ ] `## Overview` - One-line description
- [ ] `## User Story` - As a [user], I want to [action]...
- [ ] `## Entry Points` - UI and API entry points
- [ ] `## Frontend Layer` - Components, State Management, API Calls
- [ ] `## Backend Layer` - Endpoint, Business Logic, Database Operations
- [ ] `## Side Effects` - Events, logs, notifications
- [ ] `## Error Handling` - Error cases table
- [ ] `## Security Considerations` - Auth, validation, rate limiting
- [ ] `## Testing` - Prerequisites, Test Steps, Edge Cases, Status
- [ ] `## Related Flows` - Upstream/downstream connections

**Format Requirements**:
- [ ] File paths include line numbers: `src/file.py:123`
- [ ] Code snippets use proper markdown fencing
- [ ] API calls show request/response examples
- [ ] Testing section has status indicator (✅⚠️❌🚧)

#### 3.4 Feature Flows Index
If new feature flow added, check `docs/memory/feature-flows.md`:
- [ ] New flow listed in appropriate section
- [ ] Entry has correct status, document link, and description

### Step 4: Security Validation

Run security checks on the PR diff:

```bash
# Get the full diff
gh pr diff $PR_NUMBER > /tmp/pr_diff.txt
```

#### 4.1 API Keys and Tokens
```bash
grep -iE '(sk-[a-zA-Z0-9]{20,}|pk-[a-zA-Z0-9]{20,}|ghp_[a-zA-Z0-9]{36}|gho_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9]{22,}|xox[baprs]-[a-zA-Z0-9-]{10,}|ya29\.[a-zA-Z0-9_-]{50,}|AIza[a-zA-Z0-9_-]{35}|AKIA[A-Z0-9]{16})' /tmp/pr_diff.txt
```
- [ ] No API keys or tokens found

#### 4.2 Email Addresses
```bash
grep -oE '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}' /tmp/pr_diff.txt | grep -vE '(example\.com|example\.org|placeholder|test@|user@example|noreply@|anthropic\.com)'
```
- [ ] No real email addresses (only placeholders allowed)

#### 4.3 IP Addresses
```bash
grep -oE '\b([0-9]{1,3}\.){3}[0-9]{1,3}\b' /tmp/pr_diff.txt | grep -vE '^(127\.|0\.0\.0\.0|172\.(1[6-9]|2[0-9]|3[0-1])\.|192\.168\.|10\.)'
```
- [ ] No public IP addresses exposed

#### 4.4 Environment Files
```bash
gh pr diff $PR_NUMBER --name-only | grep -E '^\.env$|/\.env$' | grep -v '\.example'
```
- [ ] No .env files with real values

#### 4.5 Hardcoded Secrets
```bash
grep -iE '(password|secret|token|api_key|apikey|auth_token|access_token|private_key)\s*[=:]\s*["\x27][^"\x27]{8,}["\x27]' /tmp/pr_diff.txt | grep -vE '(process\.env|os\.environ|os\.getenv|\$\{|example|placeholder|your-|changeme|xxx|\\$\\{)'
```
- [ ] No hardcoded secrets

#### 4.6 Credential Files
```bash
gh pr diff $PR_NUMBER --name-only | grep -iE '(credentials\.json|service.?account.*\.json|\.pem$|\.key$|id_rsa|id_ed25519|\.p12$|\.pfx$|htpasswd)'
```
- [ ] No credential files committed

### Step 5: Code Quality Assessment

#### 5.1 Minimal Necessary Changes
Review the diff scope:
- [ ] Changes are focused on the stated purpose
- [ ] No unrelated refactoring
- [ ] No cosmetic changes to unrelated code
- [ ] No unnecessary documentation additions

#### 5.2 Pattern Compliance
Spot-check changed code against existing patterns:
- [ ] Follows existing code style
- [ ] Uses established patterns for similar operations
- [ ] Error handling consistent with codebase

### Step 6: Requirements Traceability

#### 6.1 Link to Requirements
Check PR description and changed files:
- [ ] PR references a requirement ID or describes the feature
- [ ] Changes align with documented requirements
- [ ] If new feature: requirement was added to requirements.md

### Step 7: Generate Validation Report

Create the report in this format:

---

## PR Validation Report

**PR**: #[number] - [title]
**Author**: [author]
**Branch**: [head] → [base]
**Files Changed**: [count] (+[additions]/-[deletions])

### Summary

| Category | Status | Notes |
|----------|--------|-------|
| Changelog | ✅/❌ | [details] |
| Roadmap | ✅/❌/➖ | [details or N/A] |
| Requirements | ✅/❌/➖ | [details or N/A] |
| Architecture | ✅/❌/➖ | [details or N/A] |
| Feature Flows | ✅/❌/⚠️ | [details] |
| Feature Flow Format | ✅/❌/➖ | [details or N/A] |
| Security Check | ✅/❌ | [details] |
| Code Quality | ✅/⚠️ | [details] |
| Requirements Trace | ✅/⚠️ | [details] |

### Documentation Checklist

- [x/] Changelog entry with timestamp and emoji
- [x/] Roadmap updated (if applicable)
- [x/] Requirements updated (if applicable)
- [x/] Architecture updated (if applicable)
- [x/] Feature flow created/updated (if applicable)
- [x/] Feature flows index updated (if new flow)

### Security Checklist

- [x/] No API keys or tokens
- [x/] No real email addresses
- [x/] No IP addresses
- [x/] No .env files
- [x/] No hardcoded secrets
- [x/] No credential files

### Issues Found

#### Critical (Block Merge)
- [List any critical issues that must be fixed]

#### Warnings (Review Required)
- [List any warnings that need human review]

#### Suggestions (Optional)
- [List any non-blocking suggestions]

### Recommendation

**[APPROVE / REQUEST CHANGES / NEEDS DISCUSSION]**

[Brief justification for the recommendation]

**If REQUEST CHANGES, comment template:**
```
This PR requires the following changes before merge:

- [ ] [Required change 1]
- [ ] [Required change 2]
...

Please address these items and request re-review.
```

---

## Status Legend

| Icon | Meaning |
|------|---------|
| ✅ | Passed - meets requirements |
| ❌ | Failed - must be fixed before merge |
| ⚠️ | Warning - needs human review |
| ➖ | Not applicable to this PR |

## Quick Reference: When Documentation is Required

| Change Type | Changelog | Roadmap | Requirements | Architecture | Feature Flow |
|-------------|-----------|---------|--------------|--------------|--------------|
| Bug fix | ✅ | ➖ | ➖ | ➖ | ⚠️ if behavior changes |
| New feature | ✅ | ✅ | ✅ | ⚠️ if API/schema | ✅ |
| Refactor | ✅ | ➖ | ➖ | ⚠️ if structure | ⚠️ if flow changes |
| API change | ✅ | ➖ | ⚠️ if scope | ✅ | ✅ |
| Schema change | ✅ | ➖ | ➖ | ✅ | ⚠️ |
| Config change | ✅ | ➖ | ➖ | ⚠️ | ➖ |
| Docs only | ✅ | ➖ | ➖ | ➖ | ➖ |

## Related

- `docs/DEVELOPMENT_WORKFLOW.md` - Development cycle
- `docs/memory/feature-flows.md` - Feature flow index
- `.claude/agents/feature-flow-analyzer.md` - Flow format specification
- `/security-check` - Security validation details

## Completion Checklist

- [ ] PR information fetched
- [ ] Changelog validated
- [ ] GitHub Issues checked
- [ ] Requirements checked
- [ ] Architecture checked
- [ ] Feature flows validated
- [ ] Security checks passed
- [ ] Code quality assessed
- [ ] Requirements traced
- [ ] Report generated
- [ ] Recommendation provided
