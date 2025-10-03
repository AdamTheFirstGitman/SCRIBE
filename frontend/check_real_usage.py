#!/usr/bin/env python3
"""
Check which files REALLY use toast and getErrorMessage before removing imports.
"""

import re
from pathlib import Path

def check_usage(file_path):
    """Check if file uses toast or getErrorMessage in code."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for actual usage (not just imports)
    toast_usage = bool(re.search(r'\btoast\.', content))
    get_error_usage = bool(re.search(r'\bgetErrorMessage\(', content))

    # Check for imports
    has_toast_import = bool(re.search(r"import.*\btoast\b.*from.*sonner", content))
    has_error_import = bool(re.search(r"import.*\bgetErrorMessage\b", content))

    return {
        'toast_used': toast_usage,
        'toast_imported': has_toast_import,
        'error_used': get_error_usage,
        'error_imported': has_error_import,
        'needs_toast': toast_usage and not has_toast_import,
        'needs_error': get_error_usage and not has_error_import
    }

def main():
    frontend_dir = Path(__file__).parent

    # Files modified by fix script
    modified_files = [
        "app/page.tsx",
        "app/archives/page.tsx",
        "app/chat/page.tsx",
        "app/settings/page.tsx",
        "app/upload/page.tsx",
        "app/viz/[id]/page.tsx",
        "app/works/[id]/page.tsx",
        "app/works/page.tsx",
        "components/chat/VoiceRecorder.tsx",
        "components/pwa/InstallPrompt.tsx"
    ]

    needs_fix = []

    for file_rel in modified_files:
        file_path = frontend_dir / file_rel
        if not file_path.exists():
            continue

        result = check_usage(file_path)

        if result['needs_toast'] or result['needs_error']:
            print(f"\n⚠️ {file_rel}")
            if result['needs_toast']:
                print(f"  ❌ Uses toast.* but import missing")
            if result['needs_error']:
                print(f"  ❌ Uses getErrorMessage() but import missing")
            needs_fix.append((file_rel, result))
        else:
            status = "✓" if not (result['toast_used'] or result['error_used']) else "✓"
            print(f"{status} {file_rel}")

    if needs_fix:
        print(f"\n\n⚠️ {len(needs_fix)} files need imports restored:")
        for file_rel, result in needs_fix:
            print(f"\n{file_rel}:")
            if result['needs_toast']:
                print('  import { toast } from "sonner"')
            if result['needs_error']:
                print('  import { getErrorMessage } from "../../lib/api/error-handler"')
    else:
        print("\n✅ All files have correct imports!")

if __name__ == "__main__":
    main()
