#!/usr/bin/env python3
"""
Script to audit all imports in backend files and identify missing modules
"""

import os
import re
import ast
from pathlib import Path
from collections import defaultdict

def extract_imports_from_file(file_path):
    """Extract all imports from a Python file"""
    imports = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(('import', alias.name))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append(('from', f"{module}.{alias.name}" if module else alias.name))

    except Exception as e:
        print(f"❌ Error parsing {file_path}: {e}")

    return imports

def check_module_exists(module_path, base_dir):
    """Check if a module exists in the filesystem"""
    # Handle relative imports
    if module_path.startswith('.'):
        return False, "Relative import (should be absolute)"

    # Convert module path to file path
    parts = module_path.split('.')

    # Check if it's a built-in or third-party module
    builtin_modules = {
        'os', 'sys', 'json', 'time', 'datetime', 'uuid', 'asyncio',
        'typing', 'enum', 'hashlib', 'base64', 'tempfile', 'secrets'
    }

    third_party_modules = {
        'fastapi', 'pydantic', 'pydantic_settings', 'uvicorn', 'slowapi',
        'openai', 'anthropic', 'langchain', 'langgraph', 'supabase',
        'sqlalchemy', 'asyncpg', 'psycopg2', 'httpx', 'requests', 'aiohttp',
        'structlog', 'pytest', 'passlib', 'python_jose', 'bcrypt',
        'beautifulsoup4', 'markdown', 'python_multipart', 'python_dotenv'
    }

    if parts[0] in builtin_modules or parts[0] in third_party_modules:
        return True, "Built-in/Third-party"

    # Check local modules
    current_path = base_dir
    for part in parts:
        potential_file = current_path / f"{part}.py"
        potential_dir = current_path / part / "__init__.py"

        if potential_file.exists():
            return True, f"Local file: {potential_file}"
        elif potential_dir.exists():
            current_path = current_path / part
            continue
        else:
            return False, f"Missing: {current_path / part}"

    return True, "Local module directory"

def main():
    backend_dir = Path('backend')
    if not backend_dir.exists():
        print("Backend directory not found!")
        return

    print("🔍 SCRIBE Backend Import Audit")
    print("=" * 50)

    all_imports = defaultdict(list)
    missing_modules = defaultdict(list)

    # Find all Python files
    for py_file in backend_dir.rglob('*.py'):
        if py_file.name == '__init__.py':
            continue

        print(f"\n📁 {py_file}")
        imports = extract_imports_from_file(py_file)

        for import_type, module in imports:
            all_imports[module].append(str(py_file))

            exists, reason = check_module_exists(module, backend_dir)

            if exists:
                print(f"  ✅ {import_type} {module} - {reason}")
            else:
                print(f"  ❌ {import_type} {module} - {reason}")
                missing_modules[module].append(str(py_file))

    print(f"\n📊 SUMMARY")
    print("=" * 50)

    if missing_modules:
        print(f"❌ Found {len(missing_modules)} missing modules:")
        for module, files in missing_modules.items():
            print(f"\n🔴 {module}")
            for file in files:
                print(f"   Used in: {file}")
    else:
        print("✅ All imports are valid!")

    # Suggest fixes
    if missing_modules:
        print(f"\n🔧 SUGGESTED FIXES")
        print("=" * 50)

        for module in missing_modules.keys():
            parts = module.split('.')

            if 'services.agents' in module:
                print(f"• {module} → agents.{parts[-1]} (move from services.agents to agents)")
            elif 'database.supabase_client' in module:
                print(f"• {module} → Create services/supabase_client.py")
            elif 'services.conversation_manager' in module:
                print(f"• {module} → Create services/conversation_manager.py")
            elif module == 'get_settings':
                print(f"• {module} → Use 'settings' instead from config")

if __name__ == "__main__":
    main()