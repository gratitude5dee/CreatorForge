# Feature Flow Analysis

Create or update a feature flow document for end-to-end understanding.

## Arguments

- `$ARGUMENTS` - Feature name (e.g., "user-login", "payment-processing")

## Instructions

1. If no feature name provided, ask:
   ```
   Which feature would you like to analyze?

   Provide a feature name like:
   - user-login
   - checkout-flow
   - data-export
   - file-upload
   ```

2. Trace the feature execution path:

   **Frontend (UI → State → API)**
   - Find UI entry point (component, button/action)
   - Trace to state management (store/context)
   - Document API call made

   **Backend (Endpoint → Logic → Data)**
   - Find API endpoint handler
   - Trace business logic
   - Document database operations or external calls

   **Side Effects (if applicable)**
   - Background jobs
   - Notifications
   - External integrations

3. Document side effects:
   - Event broadcasts
   - Log events
   - State changes

4. Document error handling:
   - What can fail?
   - HTTP status codes returned
   - Error messages shown to user

5. Save flow document:
   - Path: `docs/memory/feature-flows/{feature-name}.md`
   - Use template from feature-flows.md

6. Update index:
   - Add entry to `docs/memory/feature-flows.md`
   - Mark as documented with components list

## Output Format

Use the feature flow template:

```markdown
# Feature: {Feature Name}

## Overview
Brief description.

## User Story
As a [user], I want to [action] so that [benefit].

## Entry Points
- **UI**: `path/to/Component` - Action trigger
- **API**: `METHOD /api/endpoint`

## Frontend Layer
### Components
- `Component:line` - handler()

### State Management
- `stores/store` - actionName

### API Calls
await api.method(`/api/endpoint`)

## Backend Layer
### Endpoints
- `src/backend/routes:line` - handler()

### Business Logic
1. Step one
2. Step two

## Data Layer
### Database Operations
- Query: description
- Update: description

## Side Effects
- Events: `{type, data}`
- Logs: event logged

## Error Handling
- Case → HTTP status

## Security Considerations
- Auth checks
- Input validation

## Related Flows
- Upstream: flow
- Downstream: flow
```

## Principle

Information density over completeness. Think debugging notes, not comprehensive docs.
