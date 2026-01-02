# Review Validate Command

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
   - Record `git branch --show-current`, `git rev-parse main`, `git merge-base main HEAD`, and `git diff --stat main...HEAD`.
   - If `main` might be stale due to network restrictions, note that in the Review Summary.
3. **Validate Spec Structure**
   - Run `uv run python scripts/check_docs.py`.
   - If validation fails, capture errors as new findings.
4. **Re-evaluate Findings**
   - Compare the current repo state to the review file contents.
   - Remove or downgrade findings that no longer apply.
   - Add new findings based on the current diff/state, using deterministic IDs that continue existing sequences.
5. **Update Review Report**
   - Keep the same template and formatting as `.cursor/commands/review.md`.
   - Update **Review Summary**, **Decision**, **Key Recommendations**, **Findings**, **Tests**, and **Metrics Summary**.
   - If no findings remain, set Decision to approve and Key Recommendations to “None”.
   - Keep deterministic IDs (`[Spec-1]`, `[Quality-2]`, etc.).
6. **Write Changes In-Place**
   - Update the existing `reviews/REVIEW_*.md` file only; do not create a new review report.

## Output Template

Use the same section order and formatting defined in `.cursor/commands/review.md`:

- **Review Summary** (Decision/Risk/Baseline)
- **Key Recommendations (Top Priority)**
- **Findings (ordered by severity)**
- **Strengths**
- **Tests**
- **Questions for Author**
- **Metrics Summary**

## Notes

- Do not reference any tool names in the report; keep the output consistent with existing review files in `reviews/`.
- Do not add extra sections beyond the review template; keep the report layout stable.

## Integration with Review Workflow

This command runs after `/review` (both initial and re-reviews) to validate findings before posting to GitHub.
