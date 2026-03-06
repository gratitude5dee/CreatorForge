---
name: read-docs
description: Load all project documentation into context for this session.
allowed-tools: [Read, Bash]
user-invocable: true
automation: manual
---

# Read Project Documentation

Load all project documentation into context for this session.

## State Dependencies

| Source | Location | Read | Write | Description |
|--------|----------|------|-------|-------------|
| Requirements | `docs/memory/requirements.md` | ✅ | | Feature requirements |
| Architecture | `docs/memory/architecture.md` | ✅ | | System design |
| Feature Flows | `docs/memory/feature-flows.md` | ✅ | | Flow index |
| Deployment | `docs/DEPLOYMENT.md` | ✅ | | Deploy guide |
| Testing | `docs/TESTING_GUIDE.md` | ✅ | | Test standards |
| GitHub Issues | `abilityai/trinity` | ✅ | | Roadmap |
| Changelog | `docs/memory/changelog.md` | ✅ | | Recent changes |

## Process

### Step 1: Read Core Documentation

Read these files in full (no summaries until all are loaded):
- `docs/memory/requirements.md` - Feature requirements (SINGLE SOURCE OF TRUTH)
- `docs/memory/architecture.md` - Current system design
- `docs/memory/feature-flows.md` - Feature flow index
- `docs/DEPLOYMENT.md` - Production deployment guide
- `docs/TESTING_GUIDE.md` - Testing approach and standards

### Step 2: Query GitHub Issues

```bash
gh issue list --repo abilityai/trinity --label "priority-p0" --state open --json number,title,labels
gh issue list --repo abilityai/trinity --label "priority-p1" --state open --json number,title,labels
```

### Step 3: Read Recent Changelog

Read changelog using Bash (file is 1200+ lines, only need recent entries):
```bash
head -150 docs/memory/changelog.md
```

Note: `CLAUDE.md` is loaded automatically at session start - no need to read it again.

### Step 4: Understand Project State

- What features are implemented?
- What's currently in progress?
- What are the current priorities from GitHub Issues?

### Step 5: Report Completion

```
Documentation loaded. Ready to work on Trinity.

Top P0: [first P0 issue from GitHub]
Top P1: [first P1 issue from GitHub]
Recent Change: [most recent changelog entry]
```

## When to Use

- At the start of a new session
- When you need to understand the current project state
- Before starting work on a new task
- When switching between different areas of the codebase

## Principle

Load context first, then act. Never modify code without understanding the current state.

## Completion Checklist

- [ ] Requirements.md read
- [ ] Architecture.md read
- [ ] Feature-flows.md read
- [ ] Deployment guide read
- [ ] Testing guide read
- [ ] GitHub Issues queried
- [ ] Recent changelog reviewed
- [ ] Summary reported
