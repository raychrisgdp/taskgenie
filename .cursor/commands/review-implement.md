# Review Implement Command (personal-todo)

Read a validated review report and implement actionable findings, prioritizing Critical and High severity items with clear implementation paths.

---

The user input to you can be provided directly by the agent or as a command argument - you **MUST** consider it before proceeding with the prompt (if not empty).

User input:

$ARGUMENTS

## Goal

After a review has been validated via `/review-validate`, implement the remaining actionable findings from the review report. Focus on Critical and High priority items that have clear implementation paths, and update the review file so it reflects the current state using the same format as `.cursor/commands/review.md`.

**Note**: This command can be used alongside manual fixes. The author may choose to fix issues manually or use this command to automate implementation.

## Execution Steps

1. **Select Target Review File**
   - If the user supplies a path, use it.
   - Otherwise, pick the most recent `reviews/REVIEW_*.md` file. **Hard error**: If no review file found, fail with clear error message.

2. **Parse & Filter Findings**
   - Read the review file and extract: Review Summary, Metrics, and Findings grouped by severity.
   - **Include**: Critical and High severity findings with `file:line` references and explicit "Change:" recommendations.
   - **Exclude**: Findings marked as "Out of scope", "Deferred", or requiring external clarification ("NEEDS CLARIFICATION").
   - **User Override**: If `$ARGUMENTS` contains specific finding IDs (e.g., `--findings Spec-1`), implement only those.

3. **Prioritize & Implement**
   - **Order**: Phase 1 (Critical: security, correctness), Phase 2 (High: maintainability, performance), Phase 3 (Medium: if requested).
   - **Execution**: For each actionable finding:
     - Read target file + context (10 lines before/after).
     - Apply change exactly as recommended (No over-engineering).
     - Follow project conventions (FastAPI, SQLAlchemy, Pydantic).
     - Validate using finding's "Validate:" clause.
     - Update review file immediately to track progress.

4. **Run Global Validation**
   - After implementations:
     - Run spec validation: `uv run python scripts/check_docs.py` (if specs touched).
     - Run linting: `uv run ruff check` on modified files.
     - Run tests: Execute relevant `pytest` commands.

5. **Generate Summary**
   - Output summary of implemented findings, skipped findings, and modified files.

## Implementation Directives

**Directive I: Standard Adherence**
- **Follow Conventions**: Use existing code style, absolute imports, and naming conventions.
- **Preserve Behavior**: Only modify code explicitly specified in the "Change:" recommendation.
- **No Over-Engineering**: Implement exactly what is recommended, no more.

**Directive II: Incremental Verification**
- **Atomic Progress**: Remove resolved findings immediately after successful implementation.
- **Verification**: Run all validation commands mentioned in the finding's "Validate:" clause.
- **Documentation**: Update docstrings/comments if the change affects public APIs.

## Finding Format Parsing

Parse findings using the same format as `/review`:

```
[ID][Severity][Tag] file:line – description

**Current Implementation:** (code snippet)

**Problem:** explanation

**Change:** recommendation with code example

**Validate:** test file or command
```

Extract:
- Finding ID (e.g., `Spec-1`, `Quality-2`)
- Severity (Critical, High, Medium, Low)
- File path and line number
- Change recommendation (code example or clear steps)
- Validation command (if provided)

## Output Format

After implementation, display:
```markdown
## Implementation Summary
✅ Implemented: N findings ([Spec-1], [Quality-2])
⏭️  Skipped: M findings (Reason)
❌ Failed: K findings (Error: message)
📝 Files Modified: file1.py, file2.py
🔍 Validation: Spec [Passed], Linting [Passed], Tests [Failed (Notes)]
```

## Integration with Review Workflow

This command is used after `/post-review` when author chooses to automate fixes.

Context: $ARGUMENTS
