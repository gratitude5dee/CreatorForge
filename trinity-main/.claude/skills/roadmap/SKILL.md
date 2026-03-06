---
name: roadmap
description: Query GitHub Issues for roadmap priorities and status
allowed-tools: [Bash, Read, Write]
user-invocable: true
automation: manual
---

# Roadmap

Query GitHub Issues to check current priorities, blockers, and work status.

## Purpose

Provides quick access to roadmap priorities stored in GitHub Issues. Replaces manual roadmap.md lookup with live issue queries.

## State Dependencies

| Source | Location | Read | Write |
|--------|----------|------|-------|
| GitHub Issues | `abilityai/trinity` | Yes | No |
| GitHub Labels | priority-p0/p1/p2/p3, type-*, status-* | Yes | No |

## Process

### Step 1: Parse Command Arguments

Check what the user is asking for:
- `/roadmap` or `/roadmap status` → Show P0/P1 priorities
- `/roadmap all` → Show all open issues by priority
- `/roadmap blockers` or `/roadmap blocked` → Show blocked items
- `/roadmap in-progress` → Show items being worked on
- `/roadmap create <title>` → Create a new issue (prompts for details)

### Step 2: Query GitHub Issues

**For status (default):**
```bash
# P0 issues (blocking/urgent)
gh issue list --repo abilityai/trinity --label "priority-p0" --state open --json number,title,labels,assignees

# P1 issues (critical path)
gh issue list --repo abilityai/trinity --label "priority-p1" --state open --json number,title,labels,assignees
```

**For all:**
```bash
gh issue list --repo abilityai/trinity --state open --json number,title,labels,assignees --limit 50
```

**For blockers:**
```bash
gh issue list --repo abilityai/trinity --label "status-blocked" --state open --json number,title,labels,assignees
```

**For in-progress:**
```bash
gh issue list --repo abilityai/trinity --label "status-in-progress" --state open --json number,title,labels,assignees
```

### Step 3: Format Output

Present results in a clear table format:

```
## Roadmap Status

### P0 - Blocking/Urgent
| # | Title | Type | Status |
|---|-------|------|--------|
| 1 | Fix auth bug | bug | in-progress |

### P1 - Critical Path
| # | Title | Type | Status |
|---|-------|------|--------|
| 2 | Add user roles | feature | ready |

---
View on GitHub: https://github.com/abilityai/trinity/issues
```

### Step 4: Create Issue (if requested)

If user runs `/roadmap create <title>`:

1. Ask for:
   - Priority: p0, p1, p2, p3
   - Type: feature, bug, refactor, docs
   - Description (optional)

2. Create issue:
```bash
gh issue create --repo abilityai/trinity \
  --title "Title here" \
  --label "priority-p1,type-feature" \
  --body "Description"
```

3. Return the issue URL

## Outputs

- Formatted table of issues matching query
- Issue URL when creating new issues
- Link to GitHub Issues page for full view

## Quick Commands

| Command | Description |
|---------|-------------|
| `/roadmap` | Show P0/P1 priorities |
| `/roadmap all` | All open issues |
| `/roadmap blocked` | Blocked items |
| `/roadmap in-progress` | Work in progress |
| `/roadmap create <title>` | Create new issue |

## Completion Checklist

- [ ] Command arguments parsed correctly
- [ ] GitHub Issues queried successfully
- [ ] Results formatted as table
- [ ] GitHub link provided for full view
