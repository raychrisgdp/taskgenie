# PR Description Command
>
> Maintainer: Raymond Christopher (<raymond.christopher@gdplabs.id>)

Generate or update `PR_DESCRIPTION.md` so it reflects the current diff against the main branch and mirrors `.github/pull_request_template.md` with reviewer-focused guidance tailored for the TaskGenie workspace (`personal-todo`).

For combined work across the backend API, CLI, and data models—call out each surface area's feature set, integration touchpoints, and manual verification steps independently so reviewers understand the scope split.

**IMPORTANT - Title Format**:
- The PR **title** is included as a `# Title` heading at the top of `PR_DESCRIPTION.md` (Conventional Commit format: `type(scope): description`)
- The PR **description** body starts with `## Summary` after the title heading
- When updating GitHub PRs, extract the title from the first line (`# Title`) and use it for the PR `title` field, and use the rest of the content (starting from `## Summary`) for the PR `body` field

**GitHub PR Sync**:
- After generating/updating `PR_DESCRIPTION.md` locally, the command will detect if there's an open PR for the current branch
- If found, it will prompt you to sync the title and description to GitHub
- You can also use `--sync` or `--update-pr` in `$ARGUMENTS` to automatically sync without prompting

---

The user input can be provided directly by the agent or as a command argument – you **MUST** consider it before proceeding (if not empty).

User input:

$ARGUMENTS

## 1. Guardrails: git hygiene first

1. Ensure you are inside the repo root (`git rev-parse --show-toplevel`).
2. Detect in-progress rebases/cherry-picks (look for `$GIT_DIR/rebase-merge`, `$GIT_DIR/rebase-apply`, `$GIT_DIR/CHERRY_PICK_HEAD`). If any exist, STOP and instruct the user to finish the rebase/pick before rerunning.
3. **Determine main branch name**: Check for `.github/pull_request_template.md` and extract the exact branch name from the Author Checklist item that mentions "Synced with latest" (e.g., `main-dev` or `main`). Store it as MAIN_BRANCH. If the template cannot be read or doesn't specify, default to `main`.
4. Identify the remote that owns the main branch (prefer `origin`; otherwise inspect `git remote` + `git ls-remote`). Store it as REMOTE.
5. Run `git fetch $REMOTE $MAIN_BRANCH`.
6. Check the worktree state (`git status --porcelain`). If dirty, warn that the diff may be incomplete, proceed anyway, and later mention this warning in `Additional Notes` while leaving `Self-reviewed` + `All tests pass locally` unchecked.
7. Confirm the current HEAD already contains the fetched tip of the main branch (`git merge-base --is-ancestor $REMOTE/$MAIN_BRANCH HEAD`). If this check fails, STOP and tell the user to `git pull --rebase $REMOTE/$MAIN_BRANCH` (or equivalent) before re-running. Mark the Author Checklist item **Synced with latest `$MAIN_BRANCH` branch** as `[x]` only after this passes, using the exact branch name from the template.
8. Never run `git add` or otherwise alter staging; operate strictly on the working tree the user supplied.

## 2. Gather change context

1. **Analyze the diff comprehensively**: Use `git diff --stat $REMOTE/$MAIN_BRANCH...HEAD` and `git diff --name-only --diff-filter=ACMRTUXB $REMOTE/$MAIN_BRANCH...HEAD` to understand the scope and nature of changes. Focus on:
   - **File-level changes**: What files were added, modified, or deleted?
   - **Change magnitude**: Lines added vs deleted, file types affected
   - **Component areas**: Which parts of the codebase are impacted?

2. **Deep dive into key files**: For the most significant files (by line count or functional importance), inspect detailed diffs to understand:
   - **Backend API Changes**: FastAPI endpoints in `backend/main.py`, routes, and API logic
   - **CLI Changes**: CLI command modifications under `backend/cli/main.py` and `backend/cli/`
   - **Data Model Changes**: SQLAlchemy models in `backend/models/` and Pydantic schemas in `backend/schemas/`
   - **Service Layer Changes**: Business logic in `backend/services/` (e.g., `llm_service.py`)
   - **Database Changes**: Schema migrations, database configuration in `backend/database.py`
   - **Configuration Changes**: Settings in `backend/config.py`, `.env.example`
   - **Integration Changes**: External service integrations (Gmail, GitHub, notifications, ChromaDB)
   - **Testing Changes**: Test modifications in `tests/`
   - **Documentation Changes**: Updates in `docs/**` that affect manual verification or agent workflows

   **Determine Testing Approach Based on File Changes**:
   - **Backend API-focused PRs** (primarily `backend/main.py`, API routes): Prioritize API endpoint testing and integration with CLI
   - **CLI-focused PRs** (primarily `backend/cli/`): Prioritize CLI command sequences and TUI interactions
   - **Data Model-focused PRs** (primarily `backend/models/`, `backend/schemas/`): Prioritize data integrity and schema validation
   - **Service Layer PRs** (primarily `backend/services/`): Prioritize business logic validation and integration testing
   - **Combined PRs** (both backend and CLI changes): Provide separate testing sections for API AND CLI workflows
   - **Documentation-only PRs** (primarily `docs/**`): Focus on documentation review and validation steps

3. **Identify high-impact changes**: Pay special attention to:
   - **Breaking changes**: API modifications, contract changes, or behavioral shifts
   - **Deletions/removals**: Especially docs, scripts, migration assets - determine if intentional
   - **New functionality**: Features, endpoints, or capabilities added
   - **Performance/security**: Critical changes affecting system behavior

4. **Assess testing implications**: Determine what manual verification is needed based on changed file types:

   **Backend API Testing** (when API files are modified):
   - **API Endpoint Testing**: Test FastAPI endpoints using curl, httpx, or Swagger UI (`uvicorn backend.main:app --reload`)
   - **Integration Testing**: Verify API works with CLI and data models correctly
   - **Database Testing**: Test database operations and migrations with `aiosqlite`
   - **Service Integration**: Verify external service integrations (OpenAI, ChromaDB, Gmail, GitHub)

   **CLI Testing** (when CLI files are modified):
   - **CLI Command Testing**: Test CLI commands (`uv run tgenie`, `uv run taskgenie`)
   - **Interactive TUI Testing**: Test Textual-based TUI interactions
   - **CLI-to-API Integration**: Verify CLI commands properly interact with backend API
   - **Error Path Testing**: Show how CLI handles errors, edge cases, and recovery scenarios

   **Data Model Testing** (when models/schemas are modified):
   - **Schema Validation**: Verify Pydantic schemas validate input correctly
   - **Database Operations**: Test SQLAlchemy models with `aiosqlite`
   - **Migration Testing**: Verify database schema changes and data integrity
   - **API-to-Model Integration**: Verify API endpoints correctly use data models

   **Combined Testing** (when multiple components are modified):
   - **End-to-End Workflows**: Test complete user journeys from CLI through API to database
   - **Cross-Component Integration**: Verify all components work together correctly
   - **Regression Testing**: Test existing functionality across all affected components
   - **Integration Validation**: Ensure changes across components maintain compatibility

5. **Incorporate user context**: Use $ARGUMENTS for user-provided insights, but also proactively ask for clarification when:
   - **Ambiguous changes**: Diff shows significant modifications but purpose unclear
   - **Testing gaps**: Automated tests don't cover critical paths reviewers should validate
   - **Integration points**: Complex interactions between components need explanation
   - **Business logic**: Changes to core business rules or data flow

6. **Generate clarification requests**: When gaps exist, produce a `Clarification Needed` checklist and exit early. Ask specifically about:
   - **Change rationale**: Why were these specific changes made?
   - **Testing approach**: What manual verification steps are most important?
   - **Integration impacts**: How do these changes affect other components?
   - **Edge cases**: What failure scenarios should reviewers test?
   - **Rollback plan**: How to revert if issues discovered post-deployment?

7. **Synthesize reviewer perspective**: Focus analysis on what reviewers need to understand based on the type of changes:

   **For Backend API Changes**:
   - **API Contract**: What API endpoints have changed and how do they affect existing clients?
   - **Error Handling**: How does the API behave under failure conditions and edge cases?
   - **Integration Points**: How do API changes affect CLI, data models, and external services?
   - **Manual Verification**: Which API endpoints should reviewers test via Swagger UI or curl?

   **For CLI Changes**:
   - **CLI User Experience**: How do CLI commands and TUI interactions behave differently?
   - **CLI Error Handling**: How do CLI commands handle errors and provide user feedback?
   - **CLI Integration Points**: How do CLI changes interact with backend API and data models?
   - **Manual Verification**: Which CLI commands should reviewers execute to validate the changes?

   **For Data Model Changes**:
   - **Schema Impact**: How do model/schema changes affect API and CLI?
   - **Data Integrity**: How are database operations and migrations handled?
   - **Validation Rules**: What validation rules are enforced through Pydantic schemas?
   - **Manual Verification**: Which database operations should reviewers test?

   **For Combined Changes**:
   - **End-to-End User Flows**: What complete user journeys should reviewers test?
   - **Cross-Component Integration**: How do changes across components interact?
   - **API-to-CLI Mapping**: How are API changes properly exposed through CLI commands?
   - **Manual Verification**: Which combination of API calls, CLI commands, and database operations should reviewers execute?

## 2.5. Determine Testing Strategy

Based on the file analysis from Step 2, automatically determine which testing approach to emphasize:

1. **Analyze file patterns**:

   ```bash
   # Check for backend API changes (replace $MAIN_BRANCH with actual branch name)
   git diff --name-only origin/$MAIN_BRANCH...HEAD | grep -E "^backend/main\.py$|^backend/(api|routes)/" | wc -l

   # Check for CLI changes
   git diff --name-only origin/$MAIN_BRANCH...HEAD | grep -E "^backend/cli/" | wc -l

   # Check for data model changes
   git diff --name-only origin/$MAIN_BRANCH...HEAD | grep -E "^backend/models/|^backend/schemas/" | wc -l

   # Check for service layer changes
   git diff --name-only origin/$MAIN_BRANCH...HEAD | grep -E "^backend/services/" | wc -l

   # Check for documentation changes
   git diff --name-only origin/$MAIN_BRANCH...HEAD | grep -E "^docs/" | wc -l
   ```

2. **Determine PR type and testing emphasis**:
   - **Backend API-focused PR** (>50% files in API-related files): Prioritize API endpoint testing with Swagger UI or curl
   - **CLI-focused PR** (>50% files in `backend/cli/`): Prioritize CLI command sequences and TUI interactions
   - **Data Model-focused PR** (>50% files in `backend/models/`, `backend/schemas/`): Prioritize schema validation and database operations
   - **Service Layer PR** (>50% files in `backend/services/`): Prioritize business logic validation and integration testing
   - **Combined PR** (significant changes in multiple components): Provide separate testing sections for each component
   - **Documentation PR** (>50% files in `docs/`): Focus on documentation review and validation steps
   - **Mixed PR** (changes across multiple areas): Include testing for all affected components

3. **Select appropriate testing examples**:
   - **For API changes**: Include `curl` commands, Swagger UI testing, or integration test scripts
   - **For CLI changes**: Include `uv run tgenie` command sequences and TUI interaction workflows
   - **For data model changes**: Include database operations and schema validation steps
   - **For combined changes**: Show complete end-to-end workflows spanning API, CLI, and database

4. **Adapt testing guidance based on PR type**:
   - Generate API testing sections when backend files are modified
   - Generate CLI testing sections when CLI files are modified
   - Include cross-component integration testing when multiple components are modified
   - Focus on user experience validation appropriate to the changed components

## 3. Build the PR description structure

1. Load `.github/pull_request_template.md` (if exists) to ensure section ordering, headings, and checklist wording stay identical. If no template exists, use a standard structure.
2. If `PR_DESCRIPTION.md` already exists, parse existing values so that:
   - Checked checkboxes stay checked unless contradicted by new findings.
   - Custom notes under **Additional Notes** are preserved unless clearly obsolete.
   - Previous manual edits provided via $ARGUMENTS are respected.
3. Overwrite (or create) `PR_DESCRIPTION.md` with the following sections, in template order, incorporating any human-provided clarification answers into the relevant sections and removing resolved `Clarification Needed` items.
   - **CRITICAL**: The file should start with `# Title` as a markdown heading, followed by `## Summary`. The title is included as the first line of the file.
   - When updating GitHub PRs, extract the title from the first line (`# Title`) and use it for the PR `title` field, and use the rest of the content (starting from `## Summary`) for the PR `body` field.

### Title

- **IMPORTANT**: The title is included as a `# Title` markdown heading at the top of `PR_DESCRIPTION.md`.
- Provide a Conventional Commit-style title (`type(scope): description`) following the [Conventional Commits v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/) specification. Derive the subject from the current diff and `.github/pull_request_template.md`, not from any previously generated `PR_DESCRIPTION.md`.
- **Analyze the diff to determine the primary change type**: Use the file changes and modifications to identify if this is a `feat`, `fix`, `refactor`, `test`, `docs`, etc.
- **Scope identification**: Look at which components were most heavily modified to determine the scope (e.g., `api`, `cli`, `models`, `services`, `docs`).
- **Description synthesis**: Based on the actual changes observed in the diff, create a concise description that captures the essence of what was modified.
- **User clarification**: If the primary purpose isn't clear from the diff analysis, ask the user to clarify the main objective of these changes.
- **Format**: Write the title as `# type(scope): description` at the very beginning of `PR_DESCRIPTION.md`, followed by a blank line, then `## Summary`.

### Summary

- Start with an **Issues & Goals** bullet block (2-4 bullets) that captures the user-facing problems or features this PR targets before detailing implementation work.
- Follow with an **Implementation Highlights** bullet list (3-6 bullets) prioritizing reviewer-relevant items. Call out intentional deletions or removals explicitly so reviewers can verify them. Reference critical files with backtick paths, e.g., ``backend/main.py``, ``backend/cli/main.py``, ``backend/models/task.py``.
- **Automatically determine PR type based on file changes**:
  - **Backend API-focused**: When changes are primarily in API endpoints and routes - emphasize API contract changes and endpoint testing
  - **CLI-focused**: When changes are primarily in `backend/cli/` - emphasize CLI command sequences and TUI interactions
  - **Data Model-focused**: When changes are primarily in `backend/models/`, `backend/schemas/` - emphasize schema validation and database operations
  - **Service Layer**: When changes are primarily in `backend/services/` - emphasize business logic and service integration
  - **Combined**: When changes span multiple components - provide separate testing sections for each component
  - **Documentation-only**: When changes are primarily in `docs/**` - focus on documentation review and validation
- Highlight documentation or tooling updates (e.g., `docs/**`, `scripts/**`) only when they materially affect reviewer actions; keep the focus on executable code and tests.
- When diff touches multiple surfaces (API, CLI, models, services), include separate bullets detailing each area's feature deltas, architectural shifts, and integration touchpoints reviewers must inspect.

### How to Test

**Automatically determine testing approach based on changed files:**

- **Backend API Changes** (files in `backend/main.py`, API routes): Include API endpoint testing using Swagger UI or curl commands.
- **CLI Changes** (files in `backend/cli/`): Focus on CLI command sequences and TUI interaction workflows.
- **Data Model Changes** (files in `backend/models/`, `backend/schemas/`): Focus on schema validation and database operations.
- **Service Layer Changes** (files in `backend/services/`): Focus on business logic validation and integration testing.
- **Combined Changes**: Provide separate testing sections for each affected component.

**Backend API Testing** (when API files are modified):

- **Start the API server**: `uvicorn backend.main:app --reload` (or `make dev` if available)
- **Swagger UI Testing**: Access `http://localhost:8000/docs` and test the changed endpoints
- **Endpoint Testing**: Use `curl` or `httpx` to test specific API endpoints
- **Expected API Behavior**: Document what each endpoint should return and how it demonstrates the new features

**CLI and TUI Workflows** (when CLI files are modified):

- **CLI Command Testing**: `uv run tgenie --help` and specific command sequences
- **Interactive TUI Testing**: Detail Textual-based TUI interactions and user flows
- **CLI-to-API Integration**: Verify CLI commands properly interact with backend API
- **Error Path Testing**: Show how CLI commands handle errors, edge cases, and recovery scenarios
- **Cross-Platform Testing**: Validate CLI behavior across different terminal environments

**Data Model and Database Testing** (when model/schema files are modified):

- **Schema Validation**: Test Pydantic schemas with various input scenarios
- **Database Operations**: Test SQLAlchemy models and database operations with `aiosqlite`
- **Migration Testing**: Verify database schema changes and data integrity
- **API-to-Model Integration**: Verify API endpoints correctly use data models

**Service Layer Testing** (when service files are modified):

- **Business Logic Validation**: Test service methods and business rules
- **External Service Integration**: Verify integrations with OpenAI, ChromaDB, Gmail, GitHub
- **Error Handling**: Test service-level error handling and recovery scenarios

**Combined Testing** (when multiple components are modified):

- **End-to-End Workflows**: Test complete user journeys from CLI through API to database
- **Cross-Component Integration**: Verify all components work together correctly
- **Regression Testing**: Test existing functionality across all affected components
- **Integration Validation**: Ensure changes across components maintain compatibility

**General Testing Guidelines**:

- **Setup Instructions**: Include environment setup, database initialization, and configuration steps
- **Prerequisite Commands**: List any commands that need to be run before testing
- **Expected Behavior**: Document what reviewers should see at each step - prompts, outputs, error messages, and interactive behaviors
- **Before/After Comparisons**: When changes affect user-facing behavior, provide comparisons of expected experience improvements
- **Error Recovery Testing**: Show how the system handles errors, edge cases, and recovery scenarios

### Related Issues

- Carry over existing issue links.
- Append or update items based on commit messages (`Closes #123`) or $ARGUMENTS. Use `-` bullets; no duplicates.

### Author Checklist

- Mirror the template ordering exactly, including the exact branch name from the template (e.g., `main-dev` vs `main`).
- Pre-check items you have verified automatically:
  - [x] Synced with latest `$MAIN_BRANCH` branch **only when Step 1.6 succeeded**, using the exact branch name from the template.
  - Re-confirm any previously checked items still hold after the latest commits; uncheck them if unsure.
  - Leave other items as-is from prior runs; default to `[ ]` if absent.
- If the worktree was dirty in Step 1.5, leave `Self-reviewed` and `All tests pass locally` unchecked and mention the warning in Additional Notes.

### Additional Notes

- Add two subsections when applicable:
  - `### Key Implementation Areas for Review`: bullet list mapping key files/components to reasoning (e.g., "`backend/main.py`: added new API endpoint for task management, verify error handling").
  - `### Testing Notes`: call out manual setup quirks, data migrations, feature flags, or known gaps.
- For combined changes across multiple components, organize Key Implementation Areas into logical sections (e.g., "Backend API", "CLI Changes", "Data Models") with clear separation.
- Preserve any prior custom content by appending below these subsections, separated by `---`.
- Reference implementation sources and docs rather than enumerating which unit tests changed; reviewers can already inspect test diffs directly.
- Skip CI/coverage metrics; stick to guidance a reviewer can validate manually.
- If the user explicitly overrides missing clarifications, add a `### Clarification Needed` subsection listing unanswered items before other custom notes.
- If nothing to note, include `- None`.

## 4. Deterministic rewrite & idempotence

1. Ensure the output is deterministic: the same inputs should yield the same `PR_DESCRIPTION.md` (no timestamps, random phrasing, or unordered lists).
2. When rerun after new commits:
   - Recompute summaries/Key Changes based on the updated diff.
   - Merge new review areas/testing steps with existing ones, de-duplicating while keeping stable ordering (stable = by file path).
   - Retain any user-edited checklist states unless contradicted by automated checks.
3. Save the file at the repository root: `$REPO_ROOT/PR_DESCRIPTION.md`.
   - **File format**: The file should start with `# Title` as a markdown heading, followed by a blank line, then `## Summary`.
   - **GitHub PR updates**: When updating GitHub PRs via API, use:
     - `title`: Extract the title from the first line of `PR_DESCRIPTION.md` by removing the `# ` prefix (e.g., if file starts with `# docs: restructure documentation`, use `docs: restructure documentation`)
     - `body`: The full content from `PR_DESCRIPTION.md` starting from `## Summary` (do NOT include the title heading)
4. Print (or log) a short status summary for the user including: title string, number of files changed, and whether the checklist sync item is checked.

5. **GitHub PR Sync (Optional)**:
   - **Detect open PR**: After generating/updating `PR_DESCRIPTION.md`, check if there's an open PR for the current branch:
     - Get the current branch name: `git rev-parse --abbrev-ref HEAD`
     - Get the repository owner and name from `git remote get-url origin` (extract from URL like `github.com/owner/repo.git`)
     - List open PRs for the repository using GitHub MCP `list_pull_requests` tool
     - Find a PR where the head branch matches the current branch (check `head.ref` field)
   - **Prompt user**: If an open PR is found, ask the user: "Found open PR #X for branch 'Y'. Would you like to update the PR title and description on GitHub with the generated content? (yes/no)"
   - **Update PR if confirmed**: If the user confirms "yes" (or if `$ARGUMENTS` contains `--sync` or `--update-pr`):
     - **Extract title**: Read the first line of `PR_DESCRIPTION.md` (should be `# type(scope): description`) and remove the `# ` prefix to get the title
     - **Extract description**: Read the full content from `PR_DESCRIPTION.md` starting from `## Summary` (skip the title heading and blank line)
     - **Update PR**: Use GitHub MCP `update_pull_request` tool with:
       - `owner`: Repository owner
       - `repo`: Repository name  
       - `pullNumber`: The PR number found
       - `title`: The Conventional Commit-style title extracted from the first line (without the `# ` markdown heading prefix)
       - `body`: The full content from `PR_DESCRIPTION.md` starting from `## Summary` (do NOT include the title heading)
     - **Print confirmation**: "✓ Updated PR #X on GitHub: title and description synced"
   - **Skip if no PR found**: If no open PR is found, print: "No open PR found for current branch. PR description saved locally in `PR_DESCRIPTION.md`. You can create a PR or update manually later."
   - **Skip if user declines**: If user declines or answers "no", print: "PR description saved locally in `PR_DESCRIPTION.md`. You can update the PR manually when ready."
   - **Error handling**: If GitHub API calls fail, print an error message but don't fail the entire command - the local file is still valid.

## 6. Exit criteria

- **Guardrail failures**: Stop with a clear error message if any guardrail fails (rebase in progress, branch behind main branch, or missing template file). When branch sync fails, specify the exact branch name from the template in the error message.
- **Clarification needed**: If gaps exist that require human judgment, produce a `Clarification Needed` checklist and exit early WITHOUT editing `PR_DESCRIPTION.md`. The user can then provide answers and rerun the command.
- **Diff-driven completion**: When sufficient context exists from diff analysis, generate the PR description and leave the workspace ready for reviewers.
- **Interactive refinement**: The process should be iterative - if initial analysis reveals ambiguities, prefer asking the user over making assumptions.

## Content Guidelines (Quick Reference)

- **Diff-driven analysis**: Base content on actual file changes and modifications observed, not commit messages.
- **Automatic testing approach determination**: Analyze file patterns to determine whether to emphasize API testing, CLI workflows, data model validation, service layer testing, or combined approaches based on changed files.
- **Component-based testing**: For combined changes, provide separate testing sections for API endpoints, CLI commands, data models, and services, clearly distinguishing between each approach.
- **API-focused testing**: When API files are modified, include Swagger UI testing or curl commands and focus on API contract validation.
- **CLI-focused testing**: When CLI files are modified, include CLI command sequences and TUI interaction workflows with step-by-step user journey documentation.
- **Data Model-focused testing**: When model/schema files are modified, include schema validation and database operation testing.
- **Service Layer testing**: When service files are modified, include business logic validation and external service integration testing.
- **User-centric clarification**: When diff analysis reveals ambiguities, ask the user for context rather than guessing.
- **Reviewer-focused verification**: Include only content that reviewers can manually review or test (code inspection, manual command execution, API calls).
- **Implementation over test enumeration**: Do not list which unit tests changed; concentrate on implementation files and behavior that reviewers should examine.
- **Practical testing guidance**: Highlight integration tests and examples that reviewers should manually try, with specific commands and expected outcomes.
- **Error handling emphasis**: Focus on how the code behaves under failure conditions and edge cases that reviewers should validate.
- **Component integration**: For multi-component changes, explain integration points and what reviewers should verify across component boundaries.
- **End-to-end validation**: For combined changes, include complete user workflows spanning all affected components.
