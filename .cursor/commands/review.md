# Review Command (personal-todo)

Perform a concise but thorough code review on a specified branch or the current working tree, delivering prioritized, actionable feedback.

---

The user input to you can be provided directly by the agent or as a command argument - you **MUST** consider it before proceeding with the prompt (if not empty).

User input:

$ARGUMENTS

## Goal

Provide clear, high-impact review findings that keep the implementation simple, aligned with the spec, and grounded in the `main` baseline (minimum necessary deltas).

## Execution Steps

1. **Parse Arguments**
   - Supported formats: `PR <number>`, `--pr <number>`, `--<branch_name>`, or no arguments (working tree).
   - Fetch branch from GitHub if PR is provided.

2. **Git Hygiene Check**
   - Confirm repo root: `git rev-parse --show-toplevel`
   - Ensure no in-progress rebase/cherry-pick: `git status`
   - Identify the remote that owns the target branch (prefer `origin`; otherwise inspect `git remote` + `git ls-remote`)
   - **Ensure `main` branch is up-to-date**:
     - Check if `main` exists locally: `git show-ref --verify --quiet refs/heads/main`
     - If `main` exists locally: `git fetch <remote> main:main` to update it
     - If `main` doesn't exist locally: `git fetch <remote> main` and create tracking branch: `git branch --track main <remote>/main` (if needed)
     - Verify `main` branch is accessible: `git rev-parse --verify main`
   - Run `git fetch <remote>` to get latest changes for all branches
   - If target branch specified: Confirm the target branch exists and is accessible (locally or remotely)
   - Get the merge base between `main` and target branch: `git merge-base main <target_branch>` (if target branch specified)

3. **Determine Scope (compare to `main`)**
   - **ALWAYS compare against `main`**: record the baseline hash.
   - Use `git diff main...<target_branch>` (three dots) for feature branches.
   - Identify changed files and statistics (`git diff --stat`).

4. **File Analysis**
   - List changed non-test files; note responsibility and trim opportunities.
   - **Ignore `PR_DESCRIPTION.md`**: This file is for PR authoring and should not be reviewed. Do not flag issues in this file.
   - Apply language-specific review rules (Python 3.11+, FastAPI).

## Analysis Directives (CRITICAL FOCUS)

**Directive I: Spec Compliance & MVP Fit (YAGNI)**
- **Identify relevant spec files**: Look for `.md` files in `docs/02-implementation/pr-specs/`.
- **Read the spec**: Understand what was required vs what was implemented.
- **Check for gaps/over-implementation**: Identify features mentioned in spec but not implemented, or implemented but not in spec.
- **Verify MVP scope**: Ensure Phase 2 features aren't implemented in MVP. Flag code that goes beyond spec requirements.
- **Prune scope**: Flag code tied to removed architecture as out-of-scope.

**Directive II: Overengineering & Simplification**
- **Cleanest Path**: Recommend smallest change-set that reduces complexity.
- **Fragmentation**: Count helper functions per file; inline single-use modules/functions.
- **Abstractions**: Identify unnecessary intermediate dataclasses/classes or layers of indirection.
- **Logic**: Simplify areas where simple operations are broken into too many steps. Consolidate duplicated logic.

**Directive III: Quality & Security Standards**
- **General Code Quality**: Readability, maintainability, consistent naming, appropriate error handling.
- **Python-specific (personal-todo)**: Enforce 120-char line limit (Ruff), Google-style docstrings, absolute imports preferred, FastAPI patterns, Pydantic v2 validation, and async/await patterns.
- **Security**: Input validation/sanitization, secure handling of sensitive data (env-only), SQL injection prevention (parameterized queries).
- **Performance**: Algorithm complexity analysis, database query optimization, resource cleanup.
- **Testing**: Ensure adequate, isolated, and meaningful test coverage (pytest).

**Directive IV: Spec & Integration**
- **Integration**: Database schema modifications, external service dependencies, backward compatibility.
- **Environment**: Scan diff for new env vars; verify `.env.example` is updated. No plaintext secrets.
- **Spec Template**: Verify new specs follow `docs/specs/templates/spec-template.md` structure.

## Output Report Rules

1. **STRICTLY READ-ONLY**: This review command analyzes code and generates a report file. It does NOT modify any code files, only writes the review report to `reviews/REVIEW_<target>.md`.
2. **Token Efficiency**: Limit findings to maximum 25 items. If more issues are found, prioritize by severity.
3. **Concise Findings**: Keep each finding concise (it will be posted as an inline PR comment).
4. **Per-Finding Validation Required**: Each finding must include a `**Validate:**` line with the exact commands or checks needed to verify the fix.
5. **Deterministic IDs**: Assign stable IDs using format `[Tag-N]` (e.g., `[Spec-1]`, `[Quality-2]`).
   - Tags: `[Config] [DB] [CLI] [Security] [Perf] [Test] [Docs] [Arch] [Spec] [Quality] [Env]`.
6. **Save Location**: Save/overwrite the report in `reviews/` as `REVIEW_<target>.md` (use branch name or `HEAD`).

---

## Core Report Template (`reviews/REVIEW_<target>.md`)

### Executive Summary

**Overall Assessment:** ✅ **Approve with recommendations** / ⚠️ **Needs work** / ❌ **Block**

Brief summary paragraph describing the PR's status, key accomplishments, and overall quality. Keep concise; expand when the PR is complex.

**Simplicity / MVP Fit:** Pass / Needs simplification (1–2 sentences; call out the biggest simplification lever).

**Key Strengths:**
- Bullet 1: Major positive aspect
- Bullet 2: Another strength (3–5 bullets total)

**Risk Level:** Low/Medium/High/Critical (brief explanation in parentheses)

**Stats:** X files changed, +Y/-Z lines, N tests passing (or test status)

**Baseline:** `main <short-hash>, target <branch|working tree> <short-hash>, merge base <short-hash>, compare <method>`

---

**Key Recommendations (Top Priority)**

- 3–5 bullets; highest-impact items first (if none, state "None")

---

## Detailed Findings

**Finding Format Guidelines:**
- **For Low Priority Findings:** Use concise format (single bullet with **Change:** and **Validate:**).
- **For Medium+ Priority Findings:** Use one bullet per finding, and use indented multiline fields for context and code examples.
- Use exactly **one** markdown list item per finding (single bullet), with indented multiline details under it.
- Use `file:line` or `file:line-range` without backticks on the first line.
- Use an en dash `–` between file:line and description.

**Comprehensive Format (Medium+ Priority):**
- **[Tag-N][Severity][Tag]** file.py:42-50 – Issue title / short summary.
  **Issue:** Detailed explanation of the problem, why it matters, and potential impact.
  **Example:**
  ```python
  # Problematic code showing the issue
  ```
  **Change:** Specific actionable recommendation (include code snippet if helpful).
  **Validate:** Exact command(s) + pass criteria (e.g., `uv run pytest path/to/test.py`). Use `n/a` if not applicable.

### 📜 Spec Compliance
**None.** (if no findings)
- Findings following format above.

### 🔴 Critical Issues / 🟠 High Priority / 🟡 Medium Priority / 🟢 Low Priority
**None.** (if no findings in a category)
- Findings following format above.

**Review Completion Message (when zero findings remain):**
```markdown
Congratulations @<author>, you are good to go!
```

---

## Strengths
- 3–4 bullets max; avoid repetition; call out material wins.

---

## Testing Results

**CRITICAL:** Show actual commands run, not summaries. Never include "[N tools called]" lines.

```
uv run python scripts/check_docs.py
OK: 49 markdown files checked

uv run ruff check .
✅ All checks passed

pytest -q --timeout=20 tests/test_database.py
✅ 3 passed
```

---

## Optional Sections (Include only if relevant)

### Security Considerations
1. ✅ **SQL Injection**: Using parameterized queries
2. ⚠️ **Path Traversal**: CLI accepts arbitrary paths (low risk for local tool)
3. ✅ **Secret Management**: Config supports env vars (no hardcoded secrets)
4. ✅ **Input Validation**: Proper validation on all inputs

### Performance Considerations
1. ✅ **Indexed Queries**: Proper indexes on key tables
2. ✅ **Connection Pooling**: Using async engine
3. ⚠️ **Migration Threading**: Slight overhead from thread spawning (negligible)
4. ✅ **Lazy Directory Creation**: Directories created only when needed

### Compatibility
- ✅ **Python**: >=3.11 (as specified in pyproject.toml)
- ✅ **Cross-Platform**: Path expansion handles Windows/Unix
- ⚠️ **Database**: SQLite-only (as designed)

### Questions for Author
- Add as many as needed; concise clarifications or spec asks.

### Detailed Analysis (Optional)
This section is optional and intended for richer human-readable context.

### Appendix: Detailed Finding Format (Optional)
Use this format only in the optional appendix if needed for large change sets.
- **[ID][Severity][Tag]** file:line – Short title.
  **Current Implementation:** (Snippet)
  **Problem:** Why it matters.
  **Change:** Exact edits.
  **Validate:** Command(s) + pass criteria.

### Comparison with Baseline PR (if applicable)
**Improvements Over Baseline:**
1. ✅ **Feature X fixed** - Description

**Regressions/New Issues:**
1. ❌ **Issue A** - Description

### Metrics Summary
| Metric | Count |
|--------|-------|
| Total Findings | N |
| Critical | N |
| High | N |
| Medium | N |
| Low | N |
| Files Changed | N |
| Spec Compliance Issues | N |

---

## Behavior Rules
- Compare against `main`; record baseline hash; use three-dot for branches.
- Require a spec for feature work; if absent, ask for it.
- Keep implementation minimal (YAGNI); flag over-engineering.
- Findings must cite file:line, be ordered by impact, and include specific recommendations.
- **Use Evidence**: Base findings on actual code analysis.
- **Avoid Nitpicking**: Focus on substantive issues.
- **Prefer minimal deltas**: Smallest viable change relative to main.
- **Ignore PR_DESCRIPTION.md**: Do not review or flag issues in `PR_DESCRIPTION.md`; it is for PR authoring purposes only.

Context: $ARGUMENTS
