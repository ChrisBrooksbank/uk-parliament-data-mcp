#!/usr/bin/env python3
"""Verify README.md collapsible sections are properly formatted for GitHub rendering.

This script validates that:
1. All <details> tags are properly closed
2. All <summary> tags are properly closed
3. There's proper whitespace after <summary> tags
4. The structure follows GitHub Markdown spec for collapsible sections
"""

import re
import sys
from pathlib import Path


def verify_collapsible_sections(readme_path: Path) -> tuple[bool, list[str]]:
    """Verify collapsible sections in README are properly formatted.

    Args:
        readme_path: Path to README.md file

    Returns:
        Tuple of (success: bool, errors: list[str])
    """
    errors = []

    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for matching <details> tags
    details_open = content.count('<details>')
    details_close = content.count('</details>')
    if details_open != details_close:
        errors.append(f"Mismatched <details> tags: {details_open} open, {details_close} close")

    # Check for matching <summary> tags
    summary_open = content.count('<summary>')
    summary_close = content.count('</summary>')
    if summary_open != summary_close:
        errors.append(f"Mismatched <summary> tags: {summary_open} open, {summary_close} close")

    # Check that each <details> has a <summary>
    if details_open != summary_open:
        errors.append(f"Each <details> should have a <summary>: {details_open} details, {summary_open} summaries")

    # Find all collapsible sections and validate structure
    pattern = re.compile(
        r'<details>\s*\n<summary><strong>([^<]+)</strong>[^<]*</summary>\s*\n',
        re.MULTILINE
    )

    sections = pattern.findall(content)
    if sections:
        print(f"Found {len(sections)} collapsible sections:")
        for section in sections:
            print(f"  - {section}")
    else:
        errors.append("No properly formatted collapsible sections found")

    # Verify there's a blank line after each </summary> (required for GitHub rendering)
    summary_pattern = re.compile(r'</summary>\n\n', re.MULTILINE)
    summary_with_blank = len(summary_pattern.findall(content))
    if summary_with_blank != summary_open:
        errors.append(
            f"Some <summary> tags missing blank line after: "
            f"{summary_with_blank}/{summary_open} have proper spacing"
        )

    # Check for proper closing structure (blank line before </details>)
    details_pattern = re.compile(r'\n\n</details>', re.MULTILINE)
    details_with_blank = len(details_pattern.findall(content))
    if details_with_blank != details_close:
        errors.append(
            f"Some </details> tags missing blank line before: "
            f"{details_with_blank}/{details_close} have proper spacing"
        )

    return len(errors) == 0, errors


def main() -> int:
    """Main entry point."""
    readme_path = Path(__file__).parent / 'README.md'

    if not readme_path.exists():
        print(f"ERROR: README.md not found at {readme_path}")
        return 1

    print(f"Verifying collapsible sections in {readme_path}...")
    print()

    success, errors = verify_collapsible_sections(readme_path)

    if success:
        print()
        print("[PASS] All collapsible sections are properly formatted for GitHub rendering")
        return 0
    else:
        print()
        print("[FAIL] Found formatting issues:")
        for error in errors:
            print(f"  - {error}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
