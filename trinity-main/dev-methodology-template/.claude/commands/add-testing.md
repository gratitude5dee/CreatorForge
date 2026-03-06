# Add Testing Section to Feature Flow

Add a Testing section to a feature flow document using the standard template.

## Usage

```
/add-testing {feature-flow-name}
```

Example:
```
/add-testing user-login
```

## What It Does

1. Reads the feature flow document (`docs/memory/feature-flows/{name}.md`)
2. Adds a Testing section before "Related Flows" using the template:
   - Prerequisites checklist
   - Step-by-step test instructions
   - Expected results
   - Verification checklist
   - Edge cases
   - Cleanup steps
   - Status tracking
3. Updates the document

## Template

```markdown
## Testing

**Prerequisites**:
- [ ] [Service/prerequisite 1]
- [ ] [Service/prerequisite 2]

**Test Steps**:

### 1. [Action Name]
**Action**:
- Step 1
- Step 2

**Expected**: What should happen

**Verify**:
- [ ] Check 1
- [ ] Check 2

### 2. [Next Action]
...

**Edge Cases**:
- [ ] Test scenario 1
- [ ] Test scenario 2

**Cleanup**:
- [ ] Cleanup step 1

**Last Tested**: YYYY-MM-DD
**Tested By**: Not yet tested
**Status**: 🚧 Not Tested
**Issues**: None
```

## Notes

- Customize the template based on the specific feature
- Include UI, API, and Database verification where applicable
- Document both happy path and edge cases
- Keep instructions clear and actionable
