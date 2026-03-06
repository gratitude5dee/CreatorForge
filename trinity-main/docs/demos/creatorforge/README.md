# CreatorForge Trinity Deployment Guide

This guide deploys the CreatorForge hierarchy using existing Trinity system-manifest APIs (no backend modifications).

## Artifacts

- Templates: `config/agent-templates/cf-*`
- Manifest: `config/manifests/creatorforge-economy.yaml`

## Required environment

- `TRINITY_MCP_API_KEY`
- `MINDRA_BASE_URL`
- `MINDRA_WORKFLOW_SLUG_CREATIVE`
- `MINDRA_WORKFLOW_SLUG_PROCUREMENT`
- `MINDRA_API_KEY`
- `NVM_API_KEY`
- `NVM_PLAN_ID`
- `NVM_AGENT_ID`
- `ZEROCLICK_API_URL`
- `ZEROCLICK_API_KEY`

## Deploy

```bash
MANIFEST=$(cat config/manifests/creatorforge-economy.yaml)

curl -s -X POST "http://localhost:8000/api/systems/deploy" \
  -H "Authorization: Bearer $TRINITY_MCP_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$(jq -n --arg m "$MANIFEST" '{manifest: $m, dry_run: false}')"
```

## Validate

1. List systems:
```bash
curl -s "http://localhost:8000/api/systems" \
  -H "Authorization: Bearer $TRINITY_MCP_API_KEY"
```

2. Confirm hierarchy and schedules:
```bash
curl -s "http://localhost:8000/api/systems/creatorforge" \
  -H "Authorization: Bearer $TRINITY_MCP_API_KEY"
```

3. Export deployed manifest snapshot:
```bash
curl -s "http://localhost:8000/api/systems/creatorforge/manifest" \
  -H "Authorization: Bearer $TRINITY_MCP_API_KEY"
```

## Required topology

- L0: `creatorforge-ceo`
- L1: `creatorforge-creative-director`, `creatorforge-procurement-director`
- L2: `creatorforge-copywriter`, `creatorforge-designer`, `creatorforge-brand-strategist`, `creatorforge-market-scout`, `creatorforge-quality-auditor`, `creatorforge-ad-revenue`

## Required schedules

- CEO campaign sweep: every 2 hours
- Market Scout vendor re-score: every 4 hours
- Quality Auditor compliance drift audit: every 6 hours

## Notes

- Permissions are explicit hierarchy (not full mesh).
- Default tags include `creatorforge` and `production`.
- Use Trinity dashboards/logs plus CreatorForge SQLite audit events as evidence for judging.
- Verify Mindra workflow slugs are configured before deploy; the CEO and Procurement Director depend on workflow-run plus SSE streaming, not the deprecated orchestrate endpoint.
- Capture evidence for first paid transaction, repeat buyer discount, vendor switch, and one full ad attribution chain.
