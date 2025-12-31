# Test Results

This directory contains acceptance criteria test results for PR specifications.

## Purpose

Each PR specification in `docs/02-implementation/pr-specs/` defines acceptance criteria (ACs) that must be validated before a PR is considered complete. This directory stores the test results documents that validate those criteria.

## File Naming Convention

Test results files follow this naming pattern:
- `PR-<number>-TEST-RESULTS.md`

Example:
- `PR-001-TEST-RESULTS.md` - Test results for PR-001 (Database & Configuration)

## Generating Test Results

Use the `/test-ac` command to generate or update test results:

```bash
# Test PR-001 acceptance criteria
/test-ac --pr 001

# Test specific PR spec file
/test-ac --spec docs/02-implementation/pr-specs/PR-001-db-config.md
```

## Test Results Document Structure

Each test results document includes:

1. **Summary Table** - Quick overview of all ACs and their status
2. **Detailed Results** - Per-AC breakdown with:
   - Success criteria checklist
   - Automated test evidence
   - Manual test evidence
   - Final result (PASS/FAIL/PARTIAL)
3. **Test Coverage Summary** - Overall test statistics
4. **Issues Found & Resolved** - Any problems encountered during testing
5. **Conclusion** - Overall PR status (READY FOR MERGE / NEEDS FIXES)

## Status Indicators

- ✅ **PASS** - All success criteria met
- ❌ **FAIL** - One or more criteria not met
- ⚠️ **PARTIAL** - Some criteria met but not all

## Related Documentation

- PR Specifications: `docs/02-implementation/pr-specs/`
- Test Plan: See "Test Plan" section in each PR spec file
- Test Command: `.cursor/commands/test-ac.md`
