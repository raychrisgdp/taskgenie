# Review Command

Perform a concise but thorough code review on a specified branch or the current working tree, delivering prioritized, actionable feedback.

---

The user input to you can be provided directly by the agent or as a command argument - you **MUST** consider it before proceeding with the prompt (if not empty).

User input:

$ARGUMENTS

## Goal

Provide clear, high-impact review findings that keep the implementation simple, aligned with the spec, and grounded in the `main` baseline (minimum necessary deltas).

## Execution Steps

1. **Parse Arguments**
   - Expected format: `--<branch_name> [notes]`. If no branch is provided, review the working tree against `main`.

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
   - **ALWAYS compare against `main` branch**: This is the baseline for all comparisons; record the baseline hash via `git rev-parse main` before diffing
   - **If target branch specified**:
     - Use `git diff main..<target_branch>` to see all changes between main and target branch
     - Use `git diff main...<target_branch>` (three dots) to see changes since the merge base (recommended for feature branches)
     - Identify changed files: `git diff --name-only main..<target_branch>` or `git diff --name-only main...<target_branch>`
     - Get change statistics: `git diff --stat main..<target_branch>` or `git diff --stat main...<target_branch>`
     - Get commit list: `git log main..<target_branch>` to see commits in target branch not in main
   - **If no branch specified** (reviewing working directory):
     - Check current branch: `git branch --show-current`
     - Analyze current working directory changes against `main`: `git diff main`
     - Include staged changes: `git diff --cached main`
     - Identify changed files: `git diff --name-only main` and `git diff --name-only --cached main`
     - Get change statistics: `git diff --stat main` and `git diff --stat --cached main`
   - **Verify comparison baseline**: Always confirm you're comparing against the correct `main` branch commit (`git rev-parse main`)
   - Categorize changes by type (new features, bug fixes, refactoring, documentation, etc.)

4. **File Analysis**
   - **List changed non-test files**: For each, note its responsibility/why it exists, approximate number of core logic blocks/functions, and any trim/simplify opportunities to minimize delta from main.
   - **Read changed files**: Focus on files with significant changes (use `git diff --stat` to identify)
   - **Analyze file types**: Apply language-specific review rules
   - **Check file structure**: Ensure proper organization and naming conventions
   - **Review imports/dependencies**: Check for unused imports, circular dependencies, proper versioning

5. **Code Quality Analysis**

   **Overengineering & Simplification Review** (CRITICAL FOCUS):
   - **Cleanest path check**: Given the current spec/objective, is this implementation the simplest/cleanest way to achieve it? If not, recommend the smallest change-set that reduces complexity while preserving behavior and spec compliance.
   - **Minimum viable implementation**: Does the code implement the spec requirements with the least complexity? Could simpler code satisfy the same requirements?
   - **Excessive helper function fragmentation**: Count helper functions per file; identify single-use wrappers that add no value
   - **Single-consumer helpers**: Inline or delete helper modules/functions used by a single caller unless they are intended to be shared
   - **Unnecessary abstraction layers**: Look for intermediate dataclasses/classes that don't add clarity
   - **Overly complex logic**: Identify areas where simple operations are broken into too many steps
   - **Code duplication**: Find duplicated logic between CLI and slash commands, or across modules
   - **Unused code**: Identify functions/classes that are defined but never called
   - **Premature optimization**: Look for complex solutions to simple problems
   - **Helper function consolidation opportunities**: Group related formatting/utility functions into classes or consolidate inline
   - **Beyond spec requirements**: Flag any implementation that exceeds spec requirements without documented justification (e.g., "future-proofing", "extensibility")

   **General Code Quality**:
   - Code readability and maintainability
   - Consistent naming conventions
   - Proper error handling
   - Documentation (docstrings, comments)
   - Code duplication
   - Clean-code quick check: readable, simple, expressive naming, minimal/DRY, and testable structure

   **Security Review**:
   - Input validation and sanitization
   - Authentication/authorization checks
   - Secure handling of sensitive data
   - Dependency vulnerabilities
   - SQL injection prevention
   - XSS prevention

   **Performance Considerations**:
   - Algorithm complexity analysis
   - Database query optimization
   - Memory usage patterns
   - Resource cleanup and leak prevention (file handles, network clients, event hooks)
   - Caching opportunities

   **Testing Coverage**:
   - Unit test coverage
   - Integration test coverage
   - Edge case handling
   - Error condition testing
   - **Test helpers**: Keep only helpers shared across multiple tests; inline single-use helpers and remove unused ones

6. **Language-Specific Reviews**:

    **Python** (for personal-todo):
    - Type hints usage (Python 3.11+)
    - PEP 8 compliance (via ruff, 120-char line limit)
    - Absolute imports preferred over relative
    - Exception handling patterns
    - CLI command structure (Typer)
    - Example script validation
    - Async/await patterns (SQLAlchemy/FastAPI)

   **JavaScript/TypeScript**:
   - ESLint compliance
   - React best practices (if applicable)
   - Async/await patterns
   - Component structure

   **Configuration Files**:
   - Proper formatting
   - Environment variable handling
   - Build configuration validation

7. **Spec Compliance Review** (CRITICAL FOCUS):
    - **Identify relevant spec files**:
      - Look for `.md` files in `docs/02-implementation/pr-specs/` that relate to the changes
      - Check if spec files are in the diff (`git diff main --name-only | grep -E 'docs/02-implementation/pr-specs/.*\.md'`)
      - **If no spec found in diff or codebase**: Ask the user to provide the spec document or clarify the requirements before proceeding with review
      - Search for spec references in code comments or commit messages
   - **Read the spec**: Understand what was required vs what was implemented
   - **Prune scope**: When spec deprecates architecture/components, flag code tied to removed architecture as out-of-scope rather than requesting changes
   - **Check for spec compliance gaps**: Identify features mentioned in spec but not implemented
   - **Check for over-implementation**: Identify features implemented that aren't in the spec
   - **Verify MVP scope**: Ensure Phase 2 features aren't implemented in MVP
   - **Minimum code changes principle**: Verify implementation uses the simplest approach that satisfies spec requirements
   - **YAGNI (You Aren't Gonna Need It)**: Flag any code that goes beyond spec requirements without clear justification
   - **Cross-reference with implementation**: Compare spec requirements line-by-line with code

8. **Architecture Review**:
   - Design pattern usage
   - Separation of concerns
   - Coupling and cohesion analysis
   - Scalability considerations
   - Maintainability assessment
   - SOLID alignment where applicable (single responsibility, interface boundaries, inversion)
   - **Simplification opportunities**: Can complex modules be split or simplified?
   - **Prune obsolete components**: Flag obsolete components/tests tied to removed architecture as out-of-scope rather than requesting changes
   - **Abstraction levels**: Are there too many layers of indirection?

9. **Integration Points**:
   - API contract changes
   - Database schema modifications
   - External service dependencies
   - Backward compatibility

10. **Environment & Configuration Review**:

- Scan the diff for new or modified environment variables; verify `.env`/`.env.example` (or equivalent) are updated with clear required/optional notes
- Keep code and config aligned: variable names must match exactly between code and deployment manifests
- Ensure deployment artifacts (compose files, CI/CD envs, Helm/infra configs if present) include any new variables
- No plaintext secrets: sensitive values should reside in secret stores, not committed configs
- Check consistency across environments when variables apply beyond local development

11. **Documentation Review**:

- README updates
- API documentation
- Code comments
- Change log entries

12. **Spec Template Compliance Review** (for new/modified spec files):

- **Check spec file structure**: Verify spec follows `docs/specs/templates/spec-template.md` structure
- **Required sections**: Title with synopsis (who this serves + which surfaces change), Status, Problem Statement (Goals/Gaps/Constraints/Non-Goals), Expectations, Design
- **Optional sections**: Use Cases, Backward Compatibility & Migration, Tracker, Open Questions, Success Criteria, References (should only be included if applicable)
- **Synopsis quality**: Must include "who this serves" (persona) and "which surfaces change" (CLI/slash palette/SDK/backend)
- **Section order**: Verify sections appear in template order; avoid extra top-level sections
- **Formatting compliance**:
  - Use fenced code blocks (```bash,```python) for examples, not indented blocks
  - Design section should organize by **SDK**, **CLI**, **Slash palette / UI** subsections when applicable
  - Keep language declarative (no TBDs); use `[NEEDS CLARIFICATION: …]` if unknown
- **Content quality**:
  - Problem Statement must have Goals/Gaps/Constraints/Non-Goals
  - Expectations should include user-facing examples with fenced blocks
  - Design should specify requirements per surface (SDK/CLI/UI)
  - Implementation Details should include testing enumeration
- **Template violations**: Flag missing required sections, incorrect order, formatting issues, or placeholder text

13. **Output Report**
    **STRICTLY READ-ONLY**: This review command analyzes code and generates a report file. It does NOT modify any code files, only writes the review report to `reviews/REVIEW_<target>.md`.

    **Token Efficiency**: Limit findings to maximum 25 items. If more issues are found, prioritize by severity and aggregate remaining items in a summary statement.
    - Keep each finding concise (this will be posted as an inline PR comment; long multi-paragraph findings are hard to read and may hit comment limits).

    **Per-Finding Validation Required**: Each finding must include a `**Validate:**` line with the exact commands or checks needed to verify the fix. Keep it short and scoped to that finding; use `n/a` only when validation is not applicable (e.g., doc-only notes).

    **Deterministic IDs**: Assign stable IDs to each finding using format `[Tag-N]` where Tag is a descriptive category prefix and N is a sequential number within that category. Use descriptive category names:
    - `[Config-N]` for configuration issues
    - `[DB-N]` for database issues
    - `[CLI-N]` for CLI issues
    - `[Security-N]` for security issues
    - `[Perf-N]` for performance issues
    - `[Test-N]` for testing issues
    - `[Docs-N]` for documentation issues
    - `[Arch-N]` for architecture issues
    - `[Spec-N]` for spec compliance issues
    - `[Quality-N]` for code quality issues
    - `[Env-N]` for environment/config issues

    Examples: `[Config-1]`, `[DB-2]`, `[Security-3]`, `[CLI-1]`.

- Use the core template below. Add the optional appendix only if the change set is large or the user asked for detailed tables.
- Save/overwrite the report in `reviews/` as `REVIEW_<target>.md` (use the branch name; if detached, `REVIEW_HEAD.md`; if branch missing, `REVIEW_main.md`).
- Deliver one consolidated Findings list sorted by severity/impact (combine security, spec, perf, quality, etc.); add details links if more context is needed.

### Core Report Template

## Executive Summary

**Overall Assessment:** ✅ **Approve with recommendations** / ⚠️ **Needs work** / ❌ **Block**

Brief summary paragraph describing the PR's status, key accomplishments, and overall quality. Keep concise; expand when the PR is complex (a short paragraph is fine when many issues exist).

**Simplicity / MVP Fit:** Pass / Needs simplification (1–2 sentences; call out the biggest simplification lever if applicable)

**Key Strengths:**
- Bullet 1: Major positive aspect
- Bullet 2: Another strength
- Bullet 3: Third strength (3–5 bullets total)

**Risk Level:** Low/Medium/High/Critical (brief explanation in parentheses)

**Stats:** X files changed, +Y/-Z lines, N tests passing (or test status if applicable)

**Baseline:** `main <short-hash>, target <branch|working tree> <short-hash>, merge base <short-hash>, compare <method>`

---

**Key Recommendations (Top Priority)**

- 3–5 bullets; highest-impact items first (if none, state "None")

---

## Detailed Findings

**Finding Format Guidelines:**

- **For Low Priority Findings:** Use concise format (single bullet with **Change:** and **Validate:**)
- **For Medium+ Priority Findings:** Use one bullet per finding, and use indented multiline fields for context and code examples (see format below).
- Use exactly **one** markdown list item per finding (single bullet), but feel free to add indented multiline details under that bullet (including code blocks).
- Use file:line or file:line-range without backticks on the finding's first line (parser is tolerant, but don't rely on it).
- Use an en dash `–` between file:line and the description (parser accepts `-` too).

**Concise Format (Low Priority):**
- `[ID][Severity][Tag]` file:line – Description.
  **Change:** Recommendation.
  **Validate:** How to test (use `n/a` when not applicable).

**Comprehensive Format (Medium+ Priority):**
- **[Tag-N][Severity][Tag]** file.py:42-50 – Issue title / short summary.
  **Issue:** Detailed explanation of the problem, why it matters, and potential impact.
  **Example:**
  ```python
  # Problematic code showing the issue
  def problematic_function() -> None:
      ...
  ```
  **Change:** Specific actionable recommendation (include code snippet if helpful).
  **Validate:** Command(s) + pass criteria (required for all severities; use `n/a` if not applicable).

### 🔴 Critical Issues

**None.** (if no findings)

OR

- **[Tag-N][Critical][Tag]** file:line – Brief description.
  **Change:** Recommendation.
  **Validate:** How to test.

### 🟠 High Priority Issues

**None.** (if no findings)

OR

- **[Tag-N][High][Tag]** file:line – Brief description.
  **Change:** Recommendation.
  **Validate:** How to test.

### 🟡 Medium Priority Issues

**None.** (if no findings)

OR

- **[Tag-N][Medium][Tag]** file:line – Brief description.
  **Change:** Recommendation.
  **Validate:** How to test (use `n/a` if not applicable).

### 🟢 Low Priority Issues

**None.** (if no findings)

OR

- `[Tag-N][Low][Tag]` file:line – Description.
  **Change:** Recommendation.
  **Validate:** How to test (use `n/a` if not applicable).

**Review Completion Message** (when `Total Findings | 0`)

```markdown
Congratulations @<author>, you are good to go!
```

**Note on Empty Categories**: When a severity category has no findings, explicitly state "**None.**" for clarity.

**Tags**: `[Spec] [Security] [Perf] [Quality] [Test] [Docs] [Env] [Arch]`

**Note**: Use deterministic IDs `[Tag-N]` format with descriptive category names (e.g., `[Config-1]`, `[DB-2]`, `[Security-3]`). Limit to 25 findings max; aggregate remaining in summary if more issues found. For **all findings**, include a `Validate:` clause with test file path/command and pass criterion (or `n/a`). For **Medium+** findings, use comprehensive format with inline code examples when the issue benefits from code demonstration.

---

## Strengths

- 3–4 bullets max; avoid repetition; call out material wins

---

## Testing Results

```
pytest -q --timeout=20 tests/test_database.py -k "init_db"
✅ 3 passed, 14 deselected

pytest -q --timeout=20 tests/cli/test_db.py -k "upgrade or downgrade"
❌ 3 failed, 2 passed, 18 deselected (pytest-timeout inside Alembic env asyncio.run/aiosqlite path)
```

OR (if all tests pass):

```
✅ N tests passed in X.XXs
✅ Ruff linting passed
✅ No critical or high-severity issues
```

Keep format simple: show actual test command output with pass/fail status. Include test breakdown only if helpful for context.

---

## Optional Sections (Include only if relevant)

**Note:** The following sections are optional and should only be included when they add meaningful value. Most reviews will not need these sections.

### Security Considerations

(Include only if security-related findings exist or security review is relevant)

1. ✅ **SQL Injection**: Using parameterized queries
2. ⚠️ **Path Traversal**: CLI accepts arbitrary paths (low risk for local tool)
3. ✅ **Secret Management**: Config supports env vars (no hardcoded secrets)
4. ✅ **Input Validation**: Proper validation on all inputs

### Performance Considerations

(Include only if performance-related findings exist or performance review is relevant)

1. ✅ **Indexed Queries**: Proper indexes on key tables
2. ✅ **Connection Pooling**: Using async engine
3. ⚠️ **Migration Threading**: Slight overhead from thread spawning (negligible)
4. ✅ **Lazy Directory Creation**: Directories created only when needed

### Compatibility

(Include only if compatibility concerns exist)

- ✅ **Python**: >=3.11 (as specified in pyproject.toml)
- ✅ **Cross-Platform**: Path expansion handles Windows/Unix
- ⚠️ **Database**: SQLite-only (as designed, not a bug)

### Questions for Author

(Include only if clarification is needed)

- Add as many as needed; concise clarifications/spec asks
- Include recommendations when appropriate (e.g., "Should auth-derived headers merge with `config["headers"]` or override them? What is the expected precedence? **Change:** Merge with auth headers taking precedence for conflicts")

### Conclusion

(Include only if summary beyond Executive Summary is needed)

This PR is **ready to merge** / **needs work** / **blocked**. Brief summary of why, including key tradeoffs or considerations.

**Recommended Action:** ✅ **Approve and merge** / ⚠️ **Approve with recommendations** / ❌ **Request changes**

The branch successfully implements all acceptance criteria from PR-XXX:
- ✅ Criterion 1
- ✅ Criterion 2
- ⚠️ Criterion 3 (partial, if applicable)

### Detailed Analysis (Optional - include when comparing against baseline PR or for complex changes)

This section is optional and intended for richer human-readable context (tables, multi-paragraph analysis, and code snippets). Tools that auto-post findings may ignore this section.

### Appendix: Detailed Finding Format (Optional)

Use this format only in the optional appendix (not in the main "Findings" list):

- **[ID][Severity][Tag]** file:line – Short title.

  **Current Implementation:**

  ```python
  # snippet
  ```

  **Problem:** Why it matters.

  **Change:** Exact edits to make.

  **Validate:** Command(s) + pass criteria.

### Comparison with Baseline PR (if applicable)

**Improvements Over Baseline:**

1. ✅ **Feature X fixed** - Description
2. ✅ **Feature Y documented** - Description

**Regressions/New Issues:**

1. ❌ **Issue A** - Description
2. ❌ **Issue B** - Description

### Recommendations Summary

**Must Fix Before Merge:**

1. Fix issue X (`file.py:line`): Description and test coverage requirements
2. Fix issue Y (`file.py:line`): Description and test coverage requirements

**Should Fix (Low Priority):**
3. Fix issue Z (`file.py:line`): Description

### Metrics Summary (Optional - include only if helpful for complex reviews)

| Metric | Count |
|--------|-------|
| Total Findings | N |
| Critical | N |
| High | N |
| Medium | N |
| Low | N |
| Files Changed | N |
| Lines Added | +N |
| Lines Removed | -N |
| Tests Passing | N |
| Test Failures | N |
| Spec Compliance Issues | N |

### Optional Appendix (use only when needed for large change sets)

- Use when the change set is large or the user requests detail; add a `Details` column with `[details](#detail-1)` anchors if deeper context is needed, and create matching `### Detail 1` sections below.

**Overengineering & Simplification Opportunities**

| Category | Severity | File:Line | Description | Recommendation |
|----------|----------|----------|-------------|----------------|
| Beyond Spec | High | file.py:42 | Feature implemented but not in spec | Remove or document rationale |
| Helper Fragmentation | High | file.py:42 | 37 helper functions, many single-use | Consolidate into formatter class or inline |
| Over-abstraction | Medium | file.py:15 | Unnecessary intermediate dataclass | Use direct data structures |
| Complex Path Resolution | High | cache.py:200 | 50+ lines for simple path lookup | Verify if spec requires this complexity |
| Duplicate Logic | Medium | file.py:100 | Timestamp formatting duplicated 3x | Centralize in utility module |
| Over-implementation | Medium | file.py:50 | More complex than spec requires | Simplify to minimum viable implementation |

**Spec Compliance Gaps**

| Category | Severity | File:Line | Description | Recommendation |
|----------|----------|----------|-------------|----------------|
| Missing Feature | High | session.py:400 | Filters not implemented per spec | Implement or document as Phase 2 |
| Over-implementation | High | file.py:50 | Feature not in spec | Remove or document rationale |
| Spec Not Found | Critical | N/A | No spec file found for this feature | Request spec from author before review |
| Beyond MVP | Medium | file.py:100 | Phase 2 feature in MVP implementation | Move to Phase 2 or document exception |

**Spec Template Compliance Issues**

| Category | Severity | File:Line | Description | Recommendation |
|----------|----------|----------|-------------|----------------|
| Missing Synopsis | High | specs/cli/feature.md:1 | Synopsis missing "who this serves" | Add persona and surface information |
| Wrong Section Order | Medium | specs/cli/feature.md:20 | Use Cases before Expectations | Reorder sections per template |
| Missing Required Section | High | specs/cli/feature.md:30 | Design section missing CLI/UI subsections | Organize Design by SDK/CLI/UI |
| Formatting Issue | Medium | specs/cli/feature.md:25 | Using indented code blocks instead of fenced | Convert to ```bash or```python blocks |
| Placeholder Text | Medium | specs/cli/feature.md:50 | Contains TBD or placeholder text | Replace with declarative language or [NEEDS CLARIFICATION] |
| Extra Sections | Low | specs/cli/feature.md:60 | Extra top-level section not in template | Remove or move to appropriate section |

**Critical Issues**

| Category | Severity | File:Line | Description | Recommendation |
|----------|----------|----------|-------------|----------------|
| Security | Critical | file.py:42 | SQL injection vulnerability | Use parameterized queries |

**Quality Issues**

| Category | Severity | File:Line | Description | Recommendation |
|----------|----------|----------|-------------|----------------|
| Code Style | Medium | file.py:15 | Inconsistent naming | Follow PEP 8 conventions |

**Performance Concerns**

| Category | Severity | File:Line | Description | Recommendation |
|----------|----------|----------|-------------|----------------|

**Testing Gaps**

| Category | Severity | File:Line | Description | Recommendation |
|----------|----------|----------|-------------|----------------|

**Security Findings**

| Category | Severity | File:Line | Description | Recommendation |
|----------|----------|----------|-------------|----------------|

**Recommendations Summary**

**Critical Priority:**

- [ ] **If no spec found**: Request spec document from author before proceeding
- [ ] Remove features not in spec (or document justification)

**High Priority:**

- [ ] **Spec template compliance**: Fix missing required sections, incorrect order, or formatting issues in spec files
- [ ] Verify implementation matches spec requirements exactly (no more, no less)
- [ ] Simplify to minimum viable implementation if code exceeds spec
- [ ] Consolidate formatting helpers (X functions → Y formatter class) - only if not shared across modules
- [ ] Verify path resolution complexity is required by spec

**Medium Priority:**

- [ ] Remove unused helpers
- [ ] Extract shared rendering logic (only if duplication exists)
- [ ] Document Phase 2 vs MVP features clearly

**Low Priority:**

- [ ] Consider if orphan reconciliation needed for MVP (verify against spec)

## Behavior Rules

- Compare against `main`; record baseline hash; include staged + unstaged when reviewing working tree; use three-dot for branches by default.
- Require a spec for feature work; if absent, ask for it before deep review. When specs change, check template compliance.
- Keep the implementation minimal (YAGNI); flag over-engineering and beyond-spec scope.
- Findings must cite file:line, be ordered by impact, and include specific recommendations.
- Use multiline findings: keep the issue on the first line and put **Change** / **Validate** on their own indented lines to avoid long run-on bullets.
- Use severity consistently: **Critical** (release/security/data risk), **High** (likely correctness/maintainability/perf issue), **Medium** (quality gaps or minor bugs), **Low** (polish/best-practice).
- Avoid false positives; verify before raising. Recognize strengths where notable.
- **Use Evidence**: Base findings on actual code analysis, not assumptions
- **Respect Context**: Consider project size, team, and timeline constraints
- **Avoid Nitpicking**: Focus on substantive issues that affect functionality, maintainability, or security
- **Provide Examples**: When suggesting improvements, include code examples where helpful
- **Validate each finding** before listing: (1) confirm the requirement is still in scope per spec/user direction; (2) cite exact code evidence (file:line); (3) if behavior is an intentional deviation from spec, skip the finding or mark it as "intentional deviation" rather than a defect
- **Prefer minimal deltas**: When suggesting fixes, prefer the smallest viable change relative to main that meets the requirements/spec.

## Context-Aware Review

- Use $ARGUMENTS for focus cues; consider project purpose (Personal Todo Manager) and conventions.
- Apply domain knowledge (Python/FastAPI/SQLAlchemy patterns) and match existing codebase style.
- Locate and read the relevant spec first (in `docs/02-implementation/pr-specs/`); if missing, ask for it before deep review; check template compliance only when specs change.
- Continuously ask: "Can this be simpler?" and "Does this satisfy the spec with minimum code?"

## Automated Checks (run when available)

- Lint, targeted tests, and security/static checks relevant to the touched stack.

Context: $ARGUMENTS
