# Review Implement Command

Read a validated review report and implement actionable findings, prioritizing Critical and High severity items with clear implementation paths.

---

The user input to you can be provided directly by the agent or as a command argument - you **MUST** consider it before proceeding with the prompt (if not empty).

User input:

$ARGUMENTS

## Goal

After a review has been validated via `/review-validate`, implement the remaining actionable findings from the review report. Focus on Critical and High priority items that have clear implementation paths, and update the review file so it reflects the current state using the same format as `.cursor/commands/review.md`.

**Note**: This command can be used alongside manual fixes. The author may choose to:
- Fix issues manually based on the review file
- Use this command to automate implementation
- Use both approaches (manual fixes + automated implementation)

## Execution Steps

1. **Select Target Review File**
   - If the user supplies a path (e.g., `--review reviews/REVIEW_branch.md`), use it.
   - Otherwise, pick the most recent `reviews/REVIEW_*.md` file.
   - **Hard error**: If no review file found, fail with clear error message.

2. **Parse Review File**
   - Read the review file and extract:
     - Review Summary (baseline, decision, risk)
     - Findings grouped by severity (Critical, High, Medium, Low)
     - Each finding's ID, file:line, description, and change recommendation
     - Metrics Summary (to track progress)
   - Skip findings marked as "None." or empty sections.
   - **Note**: Only implement findings that have clear "Change:" recommendations with actionable code paths.

3. **Filter Actionable Findings**
   - **Include**:
     - Critical and High severity findings with `file:line` references
     - Findings with explicit "Change:" recommendations that include code examples or clear implementation steps
     - Findings that don't require external clarification (no "NEEDS CLARIFICATION" markers)
   - **Re-validate**: If a finding is no longer applicable, remove it from the review file and update the summary/metrics.
   - **Exclude**:
     - Findings marked as "Out of scope" or "Deferred"
     - Findings requiring user input or clarification
     - Findings without clear implementation guidance
     - Low priority findings (unless user explicitly requests via `--include-low`)
   - **User override**: If `$ARGUMENTS` contains specific finding IDs (e.g., `--findings Spec-1,Quality-2`), implement only those.

4. **Prioritize Implementation Order**
   - **Phase 1**: Critical findings (security, correctness, spec compliance)
   - **Phase 2**: High findings (maintainability, performance, quality)
   - **Phase 3**: Medium findings (if `--include-medium` flag provided)
   - **Within each phase**: Order by file dependencies (read files before modifying them)

5. **Implement Each Finding**
   - For each actionable finding:
     - **Read target file**: Load the file referenced in `file:line`
     - **Understand context**: Read surrounding code (at least 10 lines before/after the target line)
     - **Apply change**: Implement the recommendation from the "Change:" section
     - **Validate change**: Run any validation commands specified in the finding's "Validate:" clause
     - **Update review**: Remove the resolved finding from the report and refresh summary/metrics to reflect the new state
   - **Error handling**: If a finding cannot be implemented (file missing, unclear recommendation, validation fails):
     - Log error with finding ID
     - Add note under **Questions for Author** describing why it could not be implemented
     - Continue with next finding

6. **Update Review File**
   - After implementing findings, update the review file in place:
     - Keep the same section order and formatting as `.cursor/commands/review.md`
     - Remove resolved findings and update **Key Recommendations** to match remaining issues
     - Update **Review Summary** and **Metrics Summary** to reflect the current state
     - Use **Questions for Author** for blocked items or missing clarification
     - If no findings remain, set Decision to approve and Key Recommendations to “None”
     - Do not add extra sections beyond the review template

7. **Run Validation**
   - After all implementations:
     - Run spec validation: `uv run python scripts/check_docs.py` (if spec files were modified)
     - Run linting: `uv run ruff check` on modified files (if applicable)
     - Run tests: Execute any test files mentioned in findings' "Validate:" clauses (e.g., `uv run pytest path/to/test.py`)
   - **Report failures**: If validation fails, add notes to review file but don't rollback changes

8. **Generate Summary**
   - Output summary of:
     - Number of findings implemented successfully
     - Number of findings skipped (with reasons)
     - Number of findings that failed implementation
     - Files modified
     - Next steps (if any findings remain)

## Implementation Rules

- **Preserve existing code**: Only modify code as specified in the finding's "Change:" recommendation
- **Follow project conventions**: Use existing code style, import patterns, and naming conventions
- **Add tests**: If a finding requires test coverage, implement tests alongside the fix
- **Atomic commits**: Consider grouping related findings by file, but don't force atomicity if findings are independent
- **Documentation**: Update docstrings/comments if the change affects public APIs
- **No over-engineering**: Implement exactly what the finding recommends, no more

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

```
## Implementation Summary

✅ Implemented: N findings
   - [Spec-1] file.py:42 - Description
   - [Quality-2] file.py:100 - Description

⏭️  Skipped: M findings
   - [Spec-3] - Requires clarification
   - [Quality-4] - Out of scope

❌ Failed: K findings
   - [Spec-5] file.py:200 - Error: file not found

📝 Files Modified:
   - file1.py
   - file2.py

🔍 Validation:
   - Spec validation: ✅ Passed
   - Linting: ✅ Passed
   - Tests: ⚠️  2 failures (see review file notes)
```

## Error Handling

- **File not found**: Log error, skip finding, add note to review file
- **Unclear recommendation**: Log warning, skip finding, add note requesting clarification
- **Validation failure**: Log error, add note to review file, continue with other findings
- **Syntax error**: Rollback the specific change, log error, add note to review file

## Behavior Rules

- **Read-only review updates**: Only update the review file to track progress; don't modify other files unless implementing a finding
- **Respect user intent**: If user specifies specific findings via `$ARGUMENTS`, only implement those
- **Preserve review structure**: Keep the original review format and structure from `.cursor/commands/review.md`
- **Incremental progress**: Remove resolved findings immediately after successful implementation
- **Clear communication**: Provide clear error messages explaining why a finding couldn't be implemented

## Example Usage

```bash
# Implement all actionable findings from most recent review
/review-implement

# Implement findings from specific review file
/review-implement --review reviews/REVIEW_c-spec-overhaul.md

# Implement only specific findings
/review-implement --findings Spec-1,Quality-2,Security-3

# Include medium priority findings
/review-implement --include-medium

# Include low priority findings
/review-implement --include-low
```

## Integration with Review Workflow

This command is used after `/post-review` when author chooses to automate fixes. It can be used alongside manual fixes.

Context: $ARGUMENTS
