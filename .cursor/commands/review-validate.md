# Review Validate Command (personal-todo)

Validate current specs after a review and refresh the existing review report to match the current state.

---

The user input to you can be provided directly by the agent or as a command argument - you **MUST** consider it before proceeding with the prompt (if not empty).

User input:

$ARGUMENTS

## Goal

After a review report exists in `reviews/`, re-check the current state, validate specs, and update that review file using the same format defined in `.cursor/commands/review.md`.

## Execution Steps

1. **Select Target Review File**
   - If the user supplies a path, use it.
   - Otherwise, pick the most recent `reviews/REVIEW_*.md`.
2. **Capture Baseline**
   - **Ensure `main` is up-to-date**: `git fetch origin main:main` (if exists) or `git fetch origin main`.
   - Record `git branch --show-current`, `git rev-parse main`, `git merge-base main HEAD`, and `git diff --stat main...HEAD`.
3. **Validate State**
   - Run `uv run python scripts/check_docs.py` for spec integrity.
   - If validation fails, capture errors as new findings.
4. **Re-evaluate Findings**
   - Compare the current repo state to the review file contents.
   - Remove or downgrade findings that no longer apply.
   - Add new findings based on the current diff/state, using deterministic IDs that continue existing sequences.
5. **Update Review Report**
   - Keep the same template and formatting as `.cursor/commands/review.md`.
   - Update **Executive Summary**, **Findings**, **Strengths**, **Testing Results**, and **Metrics Summary**.
   - If no findings remain, set Decision to approve and Key Recommendations to “None”.
   - Keep deterministic IDs (`[Spec-1]`, `[Quality-2]`, etc.).
6. **Write Changes In-Place**
   - Update the existing `reviews/REVIEW_*.md` file only; do not create a new review report.

## Output Directives (CRITICAL)

**Directive I: Report Integrity**
- **Clean Output**: Never include "[N tools called]" lines or internal implementation details.
- **Actual Commands**: The Testing Results section must show the actual commands run (e.g., `uv run ruff check .`) and their output.
- **Explicit Skips**: List any skipped validations with reasons (e.g., "⏭️ Skipped: [command] - Reason: [reason]").

**Directive II: Structural Stability**
- **Template Compliance**: Do not add extra sections beyond the review template; keep the report layout stable.
- **No Tool Names**: Do not reference any tool names in the report; keep the output consistent with existing review files.

## Integration with Review Workflow

This command runs after `/review` (both initial and re-reviews) to validate findings before posting to GitHub.
