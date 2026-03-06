---
description: Run a research cycle on trending topics
allowed-tools: WebSearch, WebFetch, Write, Read, Glob
---

# Research Cycle

Execute a research cycle to discover and document interesting trends.

## Steps

1. **Ensure Output Directory**
   - Create `/home/developer/shared-out/findings/` if it doesn't exist

2. **Discover Trends**
   Search for trending topics in:
   - AI and machine learning developments
   - Startup ecosystem news
   - Developer tools and productivity
   - Technology industry trends

3. **Analyze Findings**
   For each interesting discovery:
   - Summarize the key points
   - Assess potential opportunity or impact
   - Rate complexity/effort to pursue

4. **Document Results**
   Write findings to `/home/developer/shared-out/findings/`:
   - Create `[YYYY-MM-DD]-findings.md` with today's date
   - Update `summary.md` with cumulative insights (keep last 5 research cycles)

5. **Report Summary**
   Output a brief summary of what was found:
   - Number of trends identified
   - Top 3 most interesting findings
   - Any high-priority items

## Output Format

The findings file should follow this structure:

```markdown
# Research Findings - [DATE]

## Key Trends
- Trend 1: [description]
- Trend 2: [description]

## Opportunities Identified
1. **[Opportunity Name]**
   - Description: ...
   - Why interesting: ...
   - Complexity: Low/Medium/High

## Notable Signals
- [Signal 1]
- [Signal 2]

## Sources
- [Source 1]
- [Source 2]
```

Execute the research cycle now.
