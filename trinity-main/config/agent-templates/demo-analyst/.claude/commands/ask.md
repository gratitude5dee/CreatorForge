---
description: Answer a strategic question using accumulated research
allowed-tools: Read, Glob, Bash
---

# Answer Strategic Question

Use accumulated research findings to answer the user's question.

## Context

The user will provide a question after this command, like:
- `/ask What opportunities exist in AI agents?`
- `/ask What are the main risks we should watch?`
- `/ask Should we pursue [specific opportunity]?`

## Steps

1. **Understand the Question**
   - Parse the user's question
   - Identify key topics and themes to search for

2. **Search Research Findings**
   - First, discover the researcher's shared folder: `ls /home/developer/shared-in/`
   - Look for a folder containing "researcher" in the name
   - Read all available findings from that folder's `findings/` subdirectory
   - Look for relevant information matching the question topics
   - Note supporting evidence and sources

3. **Synthesize Answer**
   - Compile relevant findings
   - Draw connections between data points
   - Form a coherent answer

4. **Provide Response**

```markdown
## Question
[Restate the question]

## Answer
[Clear, direct answer based on research]

## Supporting Evidence
1. **[Finding 1]** (from [date])
   - [Relevant detail]

2. **[Finding 2]** (from [date])
   - [Relevant detail]

## Confidence Level
[High/Medium/Low] - based on [amount of supporting data]

## Caveats
- [Any limitations or gaps in the research]

## Suggested Follow-up
- [Additional research that could help]
```

5. **Handle Missing Data**
   If insufficient research exists:
   - State what information is missing
   - Suggest running `/request-research [topic]` to gather more data

Answer the question now.
