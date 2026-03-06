---
description: Generate daily briefing from research findings
allowed-tools: Read, Glob, Write, Bash
---

# Daily Briefing

Generate a comprehensive briefing from recent research findings.

## Steps

1. **Locate Findings**
   - First, discover available shared folders: `ls /home/developer/shared-in/`
   - Look for a researcher agent folder (contains "researcher" in name)
   - Common paths:
     - `/home/developer/shared-in/research-network-researcher/findings/` (system manifest)
     - `/home/developer/shared-in/researcher/findings/` (individual deployment)
   - If the folder is empty or doesn't exist, report that no research is available yet

2. **Read All Recent Findings**
   - Read `summary.md` if it exists (rolling summary)
   - Read the most recent `YYYY-MM-DD-findings.md` files (up to last 5)

3. **Synthesize Information**
   - Identify the top 3-5 most significant trends
   - Prioritize opportunities by impact potential
   - Note any recurring themes or patterns

4. **Generate Briefing**
   Create a briefing following this format:

```markdown
# Daily Briefing - [TODAY'S DATE]

## Executive Summary
[2-3 sentence overview of the most important findings]

## Top Trends
1. **[Trend Name]**: [Brief explanation and why it matters]
2. **[Trend Name]**: [Brief explanation and why it matters]
3. **[Trend Name]**: [Brief explanation and why it matters]

## Recommended Actions
- [ ] [Specific actionable item]
- [ ] [Specific actionable item]
- [ ] [Specific actionable item]

## Opportunities to Watch

| Opportunity | Potential | Effort | Priority |
|-------------|-----------|--------|----------|
| [Name] | High/Med/Low | High/Med/Low | 1-5 |

## Key Signals
- [Notable development or pattern]
- [Notable development or pattern]

## Data Sources
Based on research from: [dates of findings files used]
```

5. **Output the Briefing**
   - Display the briefing
   - Optionally save to `/home/developer/outputs/briefings/[DATE]-briefing.md`

Generate the briefing now.
