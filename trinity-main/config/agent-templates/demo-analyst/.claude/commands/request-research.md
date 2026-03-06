---
description: Ask the researcher to investigate a specific topic
allowed-tools: Read, Bash, Glob, mcp__trinity__list_agents, mcp__trinity__chat_with_agent
---

# Request Research

Ask the researcher agent to investigate a specific topic.

## Context

The user will provide a topic after this command, like:
- `/request-research AI agents for content creation`
- `/request-research competitor analysis for [company]`
- `/request-research emerging trends in [industry]`

## Steps

1. **Parse the Request**
   - Extract the topic from the user's input
   - Formulate a clear research request

2. **Find the Researcher Agent**
   - List available agents: `mcp__trinity__list_agents()`
   - Look for an agent with "researcher" in the name
   - Common names: `research-network-researcher` (system manifest) or `researcher` (individual)

3. **Check Current Findings (Optional)**
   - List shared-in folder: `ls /home/developer/shared-in/`
   - Quickly scan existing findings to avoid duplicate research
   - Mention if related research already exists

4. **Call the Researcher**
   Use the Trinity MCP tool to request research:

   ```
   mcp__trinity__chat_with_agent(
       agent_name="[RESEARCHER_AGENT_NAME]",  # Use actual name from step 2
       message="/research [TOPIC]"
   )
   ```

5. **Report Status**
   - Confirm the research request was sent
   - Explain that findings will appear in the shared folder
   - Suggest checking back or running `/briefing` after research completes

## Output Format

```markdown
## Research Request Submitted

**Topic**: [requested topic]
**Sent to**: [researcher agent name]
**Status**: Request delivered

### What Happens Next
1. The researcher agent will investigate the topic
2. Findings will be saved to the shared folder
3. Run `/briefing` to see synthesized results

### Related Existing Research
[If any relevant findings already exist, mention them]
```

Process the research request now.
