#!/usr/bin/env python3
"""Documentation quality checker.

Validates markdown links, naming consistency, and PR spec structure.

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import re
from pathlib import Path

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
BANNED_COMMAND_RE = re.compile(r"^\s*(?:\$ )?(todo|taskgenie)(?:\s|$)")
BANNED_HOME_RE = re.compile(r"(?:~\/\.todo|\.todo)(?:\/|\b)")


def iter_markdown_files() -> list[Path]:
    roots = [Path("docs")]
    files: list[Path] = []
    for root in roots:
        if root.exists():
            files.extend(root.rglob("*.md"))
    return sorted(files)


def check_relative_links(markdown_files: list[Path]) -> list[str]:
    missing: list[str] = []

    for md in markdown_files:
        text = md.read_text(encoding="utf-8")

        # Remove code blocks to avoid false positives from code examples
        code_block_pattern = re.compile(r"```[\s\S]*?```", re.MULTILINE)
        text_without_code = code_block_pattern.sub("", text)

        for raw_target in LINK_RE.findall(text_without_code):
            target = raw_target.strip()
            if not target or target.startswith("#"):
                continue

            if target.startswith(("http://", "https://", "mailto:")):
                continue

            # Handle optional markdown titles: (path "title")
            if " " in target:
                target = target.split(" ", 1)[0]

            # Strip anchors.
            path_part = target.split("#", 1)[0]
            if not path_part:
                continue

            # Skip absolute filesystem paths.
            if path_part.startswith("/"):
                continue

            resolved = (md.parent / path_part).resolve()
            if not resolved.exists():
                missing.append(f"{md}:{raw_target}")

    return missing


def check_naming(markdown_files: list[Path]) -> list[str]:
    violations: list[str] = []
    for md in markdown_files:
        for line_no, line in enumerate(md.read_text(encoding="utf-8").splitlines(), start=1):
            if BANNED_COMMAND_RE.search(line):
                violations.append(f"{md}:{line_no}: banned command example: {line.strip()}")
            if BANNED_HOME_RE.search(line):
                violations.append(f"{md}:{line_no}: banned home dir: {line.strip()}")
    return violations


def check_pr_spec_structure() -> list[str]:
    specs_dir = Path("docs/02-implementation/pr-specs")
    if not specs_dir.exists():
        return []

    required_sections = [
        "## Goal",
        "## Scope",
        "## Mini-Specs",
        "## Acceptance Criteria",
        "## Test Plan",
    ]

    issues: list[str] = []
    for md in sorted(specs_dir.glob("PR-*.md")):
        if md.name == "TEMPLATE.md":
            continue

        text = md.read_text(encoding="utf-8")
        for section in required_sections:
            if section not in text:
                issues.append(f"{md}: missing required section: {section}")

    return issues


def main() -> int:
    markdown_files = iter_markdown_files()
    if not markdown_files:
        print("No markdown files found under docs/")
        return 0

    missing_links = check_relative_links(markdown_files)
    naming_issues = check_naming(markdown_files)
    pr_spec_issues = check_pr_spec_structure()

    if missing_links or naming_issues or pr_spec_issues:
        if missing_links:
            print("Missing/invalid relative links:")
            for item in missing_links:
                print(f"- {item}")
        if naming_issues:
            print("Naming consistency violations:")
            for item in naming_issues:
                print(f"- {item}")
        if pr_spec_issues:
            print("PR spec completeness violations:")
            for item in pr_spec_issues:
                print(f"- {item}")
        return 1

    print(f"OK: {len(markdown_files)} markdown files checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
