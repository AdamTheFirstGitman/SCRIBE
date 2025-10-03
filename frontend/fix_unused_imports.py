#!/usr/bin/env python3
"""
Script to automatically fix unused imports in TypeScript files.
Targets common patterns: getErrorMessage, toast, etc.
"""

import re
import subprocess
from pathlib import Path

def fix_unused_imports(file_path):
    """Remove common unused imports from a TypeScript file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Pattern 1: Remove entire import line if it's getErrorMessage alone
    content = re.sub(
        r"^import \{ getErrorMessage \} from ['\"].*?['\"]$\n",
        "",
        content,
        flags=re.MULTILINE
    )

    # Pattern 2: Remove entire import line if it's toast alone
    content = re.sub(
        r"^import \{ toast \} from ['\"]sonner['\"]$\n",
        "",
        content,
        flags=re.MULTILINE
    )

    # Pattern 3: Remove getErrorMessage from multi-import lines
    content = re.sub(
        r"import \{ getErrorMessage, (.*?) \}",
        r"import { \1 }",
        content
    )
    content = re.sub(
        r"import \{ (.*?), getErrorMessage \}",
        r"import { \1 }",
        content
    )

    # Pattern 4: Remove toast from multi-import lines
    content = re.sub(
        r"import \{ toast, (.*?) \}",
        r"import { \1 }",
        content
    )
    content = re.sub(
        r"import \{ (.*?), toast \}",
        r"import { \1 }",
        content
    )

    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    frontend_dir = Path(__file__).parent
    tsx_files = list(frontend_dir.rglob("*.tsx")) + list(frontend_dir.rglob("*.ts"))

    # Exclude node_modules and .next
    tsx_files = [f for f in tsx_files if 'node_modules' not in str(f) and '.next' not in str(f)]

    fixed_count = 0
    for file_path in tsx_files:
        if fix_unused_imports(file_path):
            print(f"✓ Fixed: {file_path.relative_to(frontend_dir)}")
            fixed_count += 1

    print(f"\n✅ Fixed {fixed_count} files")
    print("\nRunning build to check for remaining errors...")

    # Run build to see if there are more errors
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=frontend_dir,
        capture_output=True,
        text=True
    )

    if "Failed to compile" in result.stdout:
        print("\n⚠️ Build still has errors:")
        # Extract error info
        lines = result.stdout.split('\n')
        for i, line in enumerate(lines):
            if "Failed to compile" in line or "Type error:" in line:
                print('\n'.join(lines[i:i+10]))
                break
    else:
        print("\n🎉 Build successful!")

if __name__ == "__main__":
    main()
