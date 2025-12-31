# Fix Unit Tests Command

Fix failing unit tests and reach target coverage threshold by identifying gaps, adding targeted tests, and resolving failures for TaskGenie (personal-todo).
---

The user input to you can be provided directly by the agent or as a command argument - you **MUST** consider it before proceeding with your prompt (if not empty).

User input:

$ARGUMENTS

## Goal

Systematically identify and fix failing unit tests, then achieve target **line coverage** by adding targeted tests for uncovered lines. For genuinely unreachable code, decide with user whether to delete dead path; only use `# pragma: no cover` (with justification) if code must stay.

**Supported Project**:

- `personal-todo/` (root level)

This project uses `uv` and `pytest` with `pytest-asyncio` for async tests. Use `make test` for running all tests.

**Stopping Criteria**: The process is complete only when:

- ✅ All unit tests pass (zero failures) locally and in CI/CD
- ✅ Target coverage achieved for target modules locally and in CI/CD (unreachable code either removed or explicitly excluded with `# pragma: no cover`)
- ✅ All linting checks pass locally and in CI/CD (`make lint`, `make typecheck`)

Continue iterating through execution steps until all criteria are met in both environments.

## Execution Steps

0. **Detect Project and Prepare Environment**:
   - Identify the project root (where `pyproject.toml`, `Makefile` exist).
   - Use `uv` to install/run dependencies and tests.
   - If `pyproject.toml`/`uv.lock` changes, re-run `uv pip install -e .` to keep the environment in sync.
   - Ensure required environment variables are loaded (`.env` for database, API keys for integrations).
   - Use `make test` as the standard test runner.

1. **Identify Failing Tests**:
   - **Run the full test suite and save the output**: `make test > /tmp/test_output.log 2>&1`
     - **IMPORTANT**: Save the output to a file instead of using `head`/`tail` - this allows reading the full output multiple times without re-running the tests.
   - Read the saved output file to analyze the results.
   - Review the test output for failures and errors.
   - Identify the specific test files and test cases that are failing.
   - Note the error messages and stack traces.
   - Categorize the failures by type (TypeError, AttributeError, missing fixtures, etc.)
   - **Note**: Pre-commit hooks may auto-fix formatting issues; if tests fail due to formatting, fixes are already applied.

2. **Analyze Test Failures**:
   - Read the failing test code to understand what it's testing.
   - Read the implementation code being tested.
   - Identify the root cause of the failure:
      - Missing required arguments in function calls.
      - Missing context/configuration in test setup (e.g., Typer test runner requires context objects).
      - Incorrect mock setup.
      - Missing fixtures or environment variables.
      - Missing mocks for helper functions called during CLI command execution.
      - API signature changes.
      - Import errors or module reload issues.
      - Async/await issues (coroutine not awaited, blocking calls in async tests).
      - Database session issues (missing async context managers).
   - Check if similar tests exist that are passing (for reference).
   - **Important**: Run tests individually (`pytest path/to/test.py::TestClass::test_method`) to isolate the issue, then run the full suite to check for test isolation problems.

3. **Fix Failing Tests**:
   - **Missing Arguments**: Add the required arguments to function calls based on actual method signatures.
   - **Missing Context/Configuration**: CLI commands that read from context require context objects in the test setup. Identify what the command reads from context and provide it in the Typer test runner.
   - **Mock Setup**: Ensure mocks match actual method signatures and return values.
   - **Missing Mocks**: Identify all helper functions called during CLI execution by reading the implementation. Mock functions that have side effects or external dependencies (e.g., LLM calls, Gmail API, GitHub API). For complex commands, trace the execution path to identify all the helpers.
   - **Fixtures**: Add or update fixtures to provide the required environment variables, database sessions, or test data.
   - **Module Reload**: For lazy import tests, use `importlib.import_module()` after clearing `sys.modules` cache.
   - **Type Errors**: Verify types match between test expectations and actual implementations (Pydantic models, SQLAlchemy models).
   - **Async/Await Errors**: Ensure async functions are properly awaited and not called in sync contexts.
   - **Database Issues**: Use async context managers for database sessions in tests.
   - **Attribute Errors**: Check if attributes exist before accessing, or use proper lazy import patterns.
   - **Assertion Adjustments**: When functions delegate to helpers, verify delegation (check helper calls) rather than indirect effects. Read the implementation to understand the execution flow.
   - **Patching Strategy**: Patch where the object is **imported/used** (not where it's defined). Read the implementation to identify which module imports/uses the function, then patch at that location. Prefer `unittest.mock.patch(..., autospec=True)` over `monkeypatch.setattr` for nested paths.

4. **Run Coverage Analysis**:
   - Run a coverage-enabled test command and save the output: `uv run pytest --cov=backend --cov-report=term-missing:skip-covered > /tmp/test_output.log 2>&1`
   - Extract the coverage report from the saved output (`grep -A 200 "coverage:" /tmp/test_output.log`).
   - Review the coverage report for modules with less than 100% coverage.
   - Identify the specific lines that are missing coverage (check for the "Missing" column).
   - Focus on critical modules first (services, models, CLI commands).
   - **Note**: Branch coverage (`--cov-branch`) can be helpful for debugging gaps but is not required for the target.

5. **Identify Coverage Gaps**:
   - Look for missing coverage in:
      - Error handling branches (try/except blocks).
      - Conditional branches (if/else statements).
      - Loop early returns or breaks.
      - Logger calls (often missed).
      - `__getattr__` implementations for lazy imports.
      - Helper methods that aren't directly tested.
      - Edge cases and boundary conditions (empty task lists, invalid IDs).
      - Async path error handling.
      - Database rollback scenarios.
      - LLM service error responses.
   - Parameterize inputs to exercise each conditional branch and early return.
   - Prioritize remediation: start with 0% modules, then <50% modules, then the remainder; for large files, tackle one feature/section at a time.
   - Use quick smoke tests to cover top-level behaviors before drilling into branch-level cases.
   - Check the coverage report for the "Missing" column to see exact line numbers.

6. **Add Targeted Tests**:
   - **For Error Branches**: Create tests that trigger exceptions with `pytest.raises(..., match=...)` so errors are asserted, not swallowed.
   - **For Conditional Branches**: Create tests for each branch (if/else paths).
   - **For Logger Calls**: Patch the logger and assert level + message (pre-interpolation) so log branches count without brittle string matches.
   - **For `__getattr__`**: Test lazy imports by clearing the module cache and accessing attributes.
   - **For Helper Methods**: Add direct tests for private helper methods if they contain complex logic.
   - **For Edge Cases**: Test boundary conditions, None values, empty collections, invalid task IDs.
   - **For Import-Time Code**: Test effects (constants, behavior) rather than import itself.
   - **For Optional Dependencies**: Test both when dependency is available (e.g., Gmail integration) and when it's not.
   - **For Exception Handling**: Patch dependencies to raise exceptions, use `side_effect=Exception("msg")`, and verify cleanup/finally behavior.
   - **For Async Code**: Ensure async functions are tested with `pytest-asyncio` and properly awaited.
   - **For Database Operations**: Test both success and failure scenarios (transaction rollback, constraint violations).

7. **Test Coverage Patterns (checklist)**:
   - Task CRUD operations: create, read, update, delete, list with filters.
   - Async operations: proper await usage, no blocking calls.
   - Database sessions: context managers, cleanup, rollback on error.
   - LLM integration: successful responses, error responses, rate limits.
   - External services (Gmail, GitHub): successful API calls, network failures, auth errors.
   - CLI commands: valid input, invalid input, help text display.
   - Configuration handling: env vars, .env file, TOML config, defaults.

8. **Verify Fixes**:
   - Run specific failing tests with `pytest path/to/test_file.py::TestClass::test_method -xvs`.
   - Run all tests with `make test`.
   - Verify no new failures were introduced.
   - Check coverage improved for target modules.

9. **Iterate Until Target Coverage**:
   - Run the coverage report again and save the output: `uv run pytest --cov=backend --cov-report=term-missing:skip-covered > /tmp/test_output.log 2>&1`
   - Read the saved output file to identify remaining gaps by checking the coverage report's "Missing" column for specific line numbers.
   - Add more targeted tests; if a line is unreachable, confirm whether to remove it. Only mark with `# pragma: no cover` (with justification) when unreachable line must stay.
   - **Common hard-to-test patterns**:
      - Import-time code (test effects, not import itself).
      - Optional dependencies (test both scenarios: Gmail enabled/disabled).
      - Defensive exception handlers (may need `# pragma: no cover`).
      - LLM error paths (may need specific test scenarios).
      - Async event loop edge cases.
   - Repeat until target modules report the target coverage locally; verify tests still pass after each iteration.
   - Push changes and ensure CI/CD matches; if results differ, reconcile environments/configs and repeat.

10. **Final Verification**:
     - Run `make test` to confirm all tests pass and coverage is achieved locally.
     - Confirm linting passes: `make lint`, `make typecheck`.
     - Push and confirm CI/CD passes; if not, align environments/configs and repeat.

## Common Fix Patterns (quick reference)

- Read the implementation first to understand the execution flow and dependencies.
- Patch where imported/used, not where defined.
- Provide the required context/configuration identified from the implementation.
- Mock functions with side effects or external dependencies (LLM calls, Gmail API, GitHub API, database operations).
- Use `*args, **kwargs` in mock functions to avoid signature mismatches.
- Test effects rather than implementation details (e.g., import-time code, delegated functions).
- For async code, use `pytest.mark.asyncio` and proper await semantics.

## Best Practices

1. **Test One Thing**: Each test should verify one specific behavior or branch.
2. **Use Descriptive Names**: Test names should clearly describe what they're testing.
3. **Arrange-Act-Assert**: Structure tests with clear setup, execution, and verification.
4. **Mock External Dependencies**: Mock API calls, file operations, and external services (LLM, Gmail, GitHub, database).
5. **Test Edge Cases**: Include tests for None values, empty collections, boundary conditions, invalid IDs.
6. **Verify Assertions**: Ensure assertions actually verify expected behavior.
7. **Clean Up**: Use context managers (`with` statements) for proper cleanup (database sessions, files).
8. **Isolate Tests**: Tests should not depend on each other or execution order.
9. **Cover Error Paths**: Test both success and failure scenarios.
10. **Make Bugs Visible**: Capture regressions with a failing test before applying a fix.
11. **Stabilize Determinism**: Fix seeds, freeze time, and isolate temp directories to avoid flaky gaps while chasing coverage.
12. **Check Coverage Incrementally**: Verify coverage improves after adding each test by running the tests and reading the saved output file.
13. **Save Test Output**: Always save test output to a file - test runs are slow, avoid re-running unnecessarily.

## What Works Well / What to Avoid

- ✅ Save test output to files for repeated analysis without re-running.
- ✅ Test effects rather than implementation details (import-time code, delegated functions).
- ✅ Read the implementation to identify dependencies and execution paths.
- ❌ Don't use `head`/`tail` on test output (re-runs unnecessarily).
- ❌ Don't patch where defined instead of where used.
- ❌ Don't assume exception handlers are covered without explicit triggers.
- ❌ Don't forget to await async functions in async tests.

## Troubleshooting

**Tests pass locally but fail in CI/CD**: Check for missing environment variables, verify fixtures are set up, ensure Python versions and dependencies match, and normalize the environment (freeze time, fix seeds, isolate temp paths).

**Coverage not improving**:

- Verify that the test actually executes the target code path.
- Check if the code path is reachable (not dead code).
- Ensure mocks aren't preventing code execution.
- Verify test assertions aren't failing silently.
- Run coverage with `uv run pytest --cov=backend --cov-report=term-missing > /tmp/test_output.log 2>&1` and read the file to see missing lines.
- **Import-time code**: If lines are in `try/except ImportError` blocks, test effects (constants, behavior) rather than import itself.
- **Optional dependencies**: Ensure you're testing both when dependency is available and when it's not.
- **Exception handlers**: May need to explicitly trigger exceptions via mocks with `side_effect`.
- **Async code**: Ensure async functions are properly awaited and tested with `pytest-asyncio`.

**Coverage differs between local and CI/CD**: Compare coverage reports, check for environment-specific code paths, verify test isolation, and ensure environments match (Python version, dependencies, coverage tool configuration).

**Import errors in tests**: Check if modules need reloading (lazy imports), verify import paths, and check for circular imports.

**Mock not working**:

- Read the implementation to identify where dependencies are imported/used, then patch at that location.
- Use `autospec=True`/`spec_set=True` to keep signatures aligned; allow `*args`, `**kwargs` in side effects.
- For CLI commands: Identify which command module executes, then patch symbols from that module.
- For shared module helpers: Patch where they're imported/used in the code being tested.
- For context-dependent commands: Read the implementation to identify required context, then provide it in the test setup.
- For complex commands: Trace the execution path to identify all helpers that need mocking.
- For async functions: Ensure async functions are properly awaited in tests.

**Tests pass individually but fail in full suite**:

- Check for shared state between tests (module-level variables, class attributes).
- Verify test isolation - each test should clean up after itself.
- Check for fixture scope issues (`function` vs `class` vs `module` scope).
- Look for import-time side effects that affect other tests.
- Reset random seeds/frozen time and isolate temp directories to prevent cross-test leakage.
- For database tests: Ensure each test uses a fresh database or properly rolls back transactions.

## Behavior Rules

- Continue until all tests pass and target coverage is achieved locally and in CI/CD.
- Fix failing tests before adding new coverage tests.
- Read the implementation first to understand the execution flow and dependencies.
- Patch where imported/used, not where defined.
- Verify incrementally: run the tests after each fix to ensure no regressions.
- Test isolation: run failing tests individually before running the full suite.
- Save test output to files to avoid unnecessary re-runs.

## Output Summary

After completing fixes, provide:

1. **Summary of Fixes**:
   - Number of failing tests fixed.
   - Number of new tests added.
   - Coverage improvement (before/after percentages).

2. **Files Modified**:
   - List of test files updated.
   - List of test files created.

3. **Coverage Report**:
   - Modules that reached the target coverage.
   - Overall coverage percentage.
   - Remaining gaps (if any).

4. **Verification**:
   - Confirmation that all tests pass.
   - Confirmation that linting passes.
   - Any remaining issues or recommendations.
