#!/usr/bin/env python3
"""
Script to fix relative imports in backend files for Render deployment
Converts relative imports (from .module) to absolute imports (from module)
"""

import os
import re
from pathlib import Path

def fix_relative_imports(file_path):
    """Fix relative imports in a Python file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Pattern for relative imports: from ..module import something OR from .module import something
    patterns = [
        (r'from \.\.([a-zA-Z0-9_.]+) import', r'from \1 import'),  # from ..module import
        (r'from \.([a-zA-Z0-9_.]+) import', r'from \1 import'),    # from .module import
    ]

    changes = []
    for pattern, replacement in patterns:
        matches = re.findall(pattern, content)
        if matches:
            content = re.sub(pattern, replacement, content)
            changes.extend(matches)

    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return changes

    return []

def main():
    backend_dir = Path('backend')
    if not backend_dir.exists():
        print("Backend directory not found!")
        return

    total_files = 0
    total_changes = 0

    # Find all Python files in backend directory
    for py_file in backend_dir.rglob('*.py'):
        if py_file.name == '__init__.py':
            continue

        print(f"Processing: {py_file}")
        changes = fix_relative_imports(py_file)

        if changes:
            print(f"  ✅ Fixed {len(changes)} imports: {changes}")
            total_changes += len(changes)
        else:
            print(f"  ⏭️  No changes needed")

        total_files += 1

    print(f"\n📊 Summary:")
    print(f"Files processed: {total_files}")
    print(f"Total imports fixed: {total_changes}")

if __name__ == "__main__":
    main()