# Test Acceptance Criteria Command

Test all acceptance criteria for a PR specification and generate/update a test results document.

---

The user input can be provided directly by the agent or as a command argument – you **MUST** consider it before proceeding (if not empty).

User input:

$ARGUMENTS

## Goal

Run automated and manual tests against the acceptance criteria defined in a PR specification file, then generate or update a comprehensive test results document in `docs/02-implementation/test-results/`.

## Output Format (v2)

Generate the test results document in a review-friendly format:

- Include a top-level **Metadata** table (spec path, branch, commit SHA, environment, timestamps)
- Use stable per-AC anchors (e.g., `#ac1`) and link Evidence in the summary table to anchors
- Use `<details>` blocks to collapse long output (pytest output, long manual command output, coverage tables)
- Keep evidence deterministic (commands, test node ids, and/or short outputs), avoid prose-only “it passed”

## Execution Steps

1. **Parse Arguments**:
   - Extract PR spec file path from `$ARGUMENTS` (format: `--spec <path>` or `--pr-spec <path>`)
   - Extract PR number/identifier (format: `--pr <number>` or `--pr-id <identifier>`)
   - If PR number provided but no spec path, infer spec path: `docs/02-implementation/pr-specs/PR-<number>-*.md`
   - If spec path provided but no PR number, extract from filename (e.g., `PR-001-db-config.md` → `PR-001`)
   - **Required**: Either spec path or PR number must be provided; fail if both missing

2. **Load PR Specification**:
   - Read the PR spec file (e.g., `docs/02-implementation/pr-specs/PR-001-db-config.md`)
   - Parse the "Acceptance Criteria" section to extract:
     - AC number/identifier (e.g., AC1, AC2)
     - Success criteria checkboxes
     - "How to Test" sections (both automated and manual)
   - Extract test plan information if present
   - **Hard error**: If spec file not found, fail with clear error message

3. **Run Automated Tests**:
   - Identify test files mentioned in the spec or infer from PR scope:
     - Config tests: `tests/test_config*.py`
     - Database tests: `tests/test_database*.py`
     - CLI tests: `tests/test_cli*.py`
     - Model tests: `tests/test_models.py`
     - Main/API tests: `tests/test_main.py`
   - Run pytest with appropriate flags:
     ```bash
     uv run pytest <test_files> -v --tb=short
     ```
   - Capture:
     - Test results (passed/failed counts)
     - Test output
     - Coverage if available
   - **Note**: If tests fail, continue but mark affected ACs as FAILED

4. **Run Manual Tests** (where applicable):
   - For each AC with manual test instructions:
     - Execute bash commands from the "Manual" section
     - Capture command output
     - Verify success criteria
   - **Note**: Some manual tests may require user interaction (e.g., confirmation prompts); handle gracefully
   - Prefer realistic CLI invocations over large inline scripts when possible:
     - `uv run tgenie db ...`
     - `uv run python -c "..."` is acceptable, but collapse it in `<details>` if long

5. **Validate Each Acceptance Criterion**:
   - For each AC in the spec:
     - Check success criteria checkboxes:
       - [x] = PASS (verified by tests)
       - [ ] = FAIL (not verified or test failed)
     - Match test results to success criteria:
       - Automated tests → map to specific criteria
       - Manual tests → map to specific criteria
     - Determine overall AC status:
       - ✅ **PASS**: All success criteria met
       - ❌ **FAIL**: One or more criteria not met
       - ⚠️ **PARTIAL**: Some criteria met but not all

6. **Generate Test Results Document**:
   - Create/update file: `docs/02-implementation/test-results/PR-<number>-TEST-RESULTS.md`
   - Structure the document (v2):
     ```markdown
     # PR-<number> Acceptance Criteria Test Results

     ## Metadata

     | Field | Value |
     |---|---|
     | PR | PR-<number> |
     | Spec | <path to PR spec> |
     | Branch | <git branch --show-current> |
     | Tested commit | <git rev-parse HEAD> |
     | Test run timestamp | <timestamp for when tests were executed> |
     | Doc generated | <ISO-8601 timestamp> |
     | Environment | <OS>, <Python>, <uv> |

     ## Status

     - **Tester:** Automated + Manual Testing
     - **Overall:** ✅ ALL CRITERIA PASS | ❌ SOME FAILURES | ⚠️ PARTIAL

     ## Summary

     | AC | Description | Status | Evidence |
     |---|------------|--------|----------|
     | [AC1](#ac1) | ... | ✅ PASS | [Automated](#ac1-automated), [Manual](#ac1-manual) |

     <a id="ac1"></a>
     ## AC1: <Title> ✅/❌

     ### Success Criteria Results

     - [x] Criterion 1
       - **Test:** `tests/test_*.py::test_name`
       - **Result:** PASSED
     - [ ] Criterion 2
       - **Test:** Manual verification
       - **Result:** FAILED
       - **Reason:** ...

     <a id="ac1-automated"></a>
     ### Automated Evidence

     **Command:** `uv run pytest tests/test_*.py::test_name -v`

     <details>
     <summary>Output</summary>

     ```text
     ...
     ```

     </details>

     <a id="ac1-manual"></a>
     ### Manual Evidence

     **Command:** <command(s) run manually>

     <details>
     <summary>Command</summary>

     ```bash
     ...
     ```

     </details>

     <details>
     <summary>Output</summary>

     ```text
     ...
     ```

     </details>

     **Result:** ✅ PASS | ❌ FAIL | ⚠️ PARTIAL

     ## Test Coverage Summary
     - Total Tests: X
     - Passed: Y ✅
     - Failed: Z ❌
     - Coverage: N%

     ## Issues Found & Resolved

     <details>
     <summary>Details</summary>

     - Issue 1: ...
     - Resolution: ...

     </details>

     ## Conclusion
     **PR-<number> Status:** ✅ READY FOR MERGE | ❌ NEEDS FIXES
     ```
   - Include:
     - Executive summary table
     - Detailed results per AC
     - Test evidence (commands + outputs)
     - Coverage summary
     - Issues found
     - Conclusion with overall status

7. **Report Results**:
   - Display summary to user:
     - Overall status (all pass / some fail / partial)
     - AC-by-AC breakdown
     - Test counts and coverage
     - Location of test results document
   - If failures found:
     - List failed ACs
     - Suggest next steps (fix issues, re-run tests)

## Important Notes

- **Test Isolation**: Use temporary directories and environment variables to avoid affecting user's actual database/config
- **Error Handling**: If a test fails, continue testing other ACs and document failures clearly
- **Manual Tests**: Some manual tests may require user interaction; document what was tested vs. what requires manual verification
- **Test Coverage**: Include coverage percentage if available (`uv run pytest --cov`)
- **Documentation**: Always update the test results document, even if tests fail (document failures clearly)
- **Determinism**: Prefer stable command strings and test node ids; wrap verbose output in `<details>`

## Example Usage

```bash
# Test PR-001 acceptance criteria
/test-ac --pr 001

# Test specific PR spec file
/test-ac --spec docs/02-implementation/pr-specs/PR-001-db-config.md

# Test with PR identifier
/test-ac --pr-id PR-001
```

## Output Format

The command should produce:
1. **Console Output**: Summary of test execution and results
2. **Test Results Document**: Detailed markdown file in `docs/02-implementation/test-results/`
3. **Status**: Clear indication of whether PR is ready for merge or needs fixes
