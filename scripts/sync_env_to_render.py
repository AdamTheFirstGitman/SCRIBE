#!/usr/bin/env python3
"""
Sync Environment Variables to Render.com
Synchronise les secrets du .env vers Render Dashboard (via API)

Usage:
    python scripts/sync_env_to_render.py --dry-run       # Preview changes
    python scripts/sync_env_to_render.py --apply         # Apply changes
    python scripts/sync_env_to_render.py --service scribe-api --apply
"""

import os
import sys
import argparse
import requests
from pathlib import Path
from typing import Dict, List, Set
from dotenv import dotenv_values

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

# Secrets to sync to Render Dashboard (NOT in render.yaml)
SECRET_KEYS = {
    'CLAUDE_API_KEY',
    'OPENAI_API_KEY',
    'PERPLEXITY_API_KEY',
    'TAVILY_API_KEY',
    'SUPABASE_SERVICE_KEY',
    'JWT_SECRET',
    'SECRET_KEY',
}

# Render API configuration
RENDER_API_BASE = "https://api.render.com/v1"


def load_env_files() -> Dict[str, str]:
    """Load environment variables from .env files"""
    project_root = Path(__file__).parent.parent
    env_files = [
        project_root / '.env',
        project_root / 'backend' / '.env',
    ]

    env_vars = {}
    for env_file in env_files:
        if env_file.exists():
            print(f"{Colors.BLUE}📖 Loading {env_file.name}...{Colors.END}")
            file_vars = dotenv_values(env_file)
            env_vars.update(file_vars)

    return env_vars


def get_render_api_key(env_vars: Dict[str, str]) -> str:
    """Get Render API key from environment"""
    api_key = env_vars.get('RENDER_API_KEY') or os.getenv('RENDER_API_KEY')

    if not api_key:
        print(f"{Colors.RED}❌ RENDER_API_KEY not found!{Colors.END}")
        print(f"\n{Colors.YELLOW}How to get your Render API Key:{Colors.END}")
        print("1. Go to https://dashboard.render.com/")
        print("2. Click on your profile → Account Settings")
        print("3. Scroll to 'API Keys' section")
        print("4. Create a new API key")
        print("5. Add to .env: RENDER_API_KEY=rnd_xxxxxxxxxxxx\n")
        sys.exit(1)

    return api_key


def get_render_services(api_key: str) -> List[Dict]:
    """Get list of Render services"""
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/json',
    }

    try:
        response = requests.get(f"{RENDER_API_BASE}/services", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"{Colors.RED}❌ Failed to fetch Render services: {e}{Colors.END}")
        sys.exit(1)


def find_service_by_name(services: List[Dict], service_name: str) -> Dict:
    """Find service by name"""
    for service in services:
        if service.get('service', {}).get('name') == service_name:
            return service['service']

    print(f"{Colors.RED}❌ Service '{service_name}' not found!{Colors.END}")
    print(f"\n{Colors.YELLOW}Available services:{Colors.END}")
    for service in services:
        name = service.get('service', {}).get('name')
        print(f"  - {name}")
    sys.exit(1)


def get_service_env_vars(api_key: str, service_id: str) -> List[Dict]:
    """Get current environment variables for a service"""
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/json',
    }

    try:
        response = requests.get(
            f"{RENDER_API_BASE}/services/{service_id}/env-vars",
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"{Colors.RED}❌ Failed to fetch env vars: {e}{Colors.END}")
        sys.exit(1)


def update_service_env_vars(
    api_key: str,
    service_id: str,
    env_vars: List[Dict],
    dry_run: bool = True
) -> bool:
    """Update service environment variables"""
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }

    if dry_run:
        print(f"\n{Colors.YELLOW}🔍 DRY RUN - No changes will be applied{Colors.END}")
        return True

    try:
        response = requests.put(
            f"{RENDER_API_BASE}/services/{service_id}/env-vars",
            headers=headers,
            json=env_vars
        )
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"{Colors.RED}❌ Failed to update env vars: {e}{Colors.END}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return False


def sync_secrets(
    env_vars: Dict[str, str],
    current_env_vars: List[Dict],
    dry_run: bool = True
) -> List[Dict]:
    """
    Sync secrets from .env to Render
    Returns updated env vars list
    """
    print(f"\n{Colors.BOLD}📋 Analyzing secrets to sync...{Colors.END}\n")

    # Build dict of current env vars
    current_dict = {var['key']: var for var in current_env_vars}

    # Prepare updates
    updated_vars = []
    changes = {'added': [], 'updated': [], 'unchanged': []}

    for key in SECRET_KEYS:
        value = env_vars.get(key)

        if not value:
            print(f"{Colors.YELLOW}⚠️  {key}: Not found in .env (skipping){Colors.END}")
            continue

        current_var = current_dict.get(key)

        if current_var:
            # Check if value changed
            current_value = current_var.get('value', '')
            if current_value.startswith('YOUR_') or current_value != value:
                print(f"{Colors.CYAN}🔄 {key}: Will UPDATE{Colors.END}")
                changes['updated'].append(key)
                updated_vars.append({'key': key, 'value': value})
            else:
                print(f"{Colors.GREEN}✓ {key}: Already up to date{Colors.END}")
                changes['unchanged'].append(key)
                updated_vars.append(current_var)
        else:
            print(f"{Colors.GREEN}➕ {key}: Will ADD{Colors.END}")
            changes['added'].append(key)
            updated_vars.append({'key': key, 'value': value})

    # Keep non-secret vars as-is
    for key, var in current_dict.items():
        if key not in SECRET_KEYS:
            updated_vars.append(var)

    # Summary
    print(f"\n{Colors.BOLD}📊 Summary:{Colors.END}")
    print(f"  {Colors.GREEN}Added: {len(changes['added'])}{Colors.END}")
    print(f"  {Colors.CYAN}Updated: {len(changes['updated'])}{Colors.END}")
    print(f"  {Colors.BLUE}Unchanged: {len(changes['unchanged'])}{Colors.END}")

    if changes['added']:
        print(f"\n  {Colors.GREEN}New secrets:{Colors.END}")
        for key in changes['added']:
            print(f"    - {key}")

    if changes['updated']:
        print(f"\n  {Colors.CYAN}Updated secrets:{Colors.END}")
        for key in changes['updated']:
            print(f"    - {key}")

    total_changes = len(changes['added']) + len(changes['updated'])

    if total_changes == 0:
        print(f"\n{Colors.GREEN}✓ All secrets are already up to date!{Colors.END}")

    return updated_vars, total_changes


def main():
    parser = argparse.ArgumentParser(
        description='Sync environment variables to Render.com',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview changes without applying
  python scripts/sync_env_to_render.py --dry-run

  # Apply changes to scribe-api service
  python scripts/sync_env_to_render.py --service scribe-api --apply

  # Apply to all backend services
  python scripts/sync_env_to_render.py --apply
        """
    )

    parser.add_argument(
        '--service',
        default='scribe-api',
        help='Render service name (default: scribe-api)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without applying them'
    )

    parser.add_argument(
        '--apply',
        action='store_true',
        help='Apply changes to Render'
    )

    args = parser.parse_args()

    # Default to dry-run if --apply not specified
    dry_run = not args.apply

    print(f"{Colors.BOLD}{Colors.BLUE}🚀 Render Environment Sync Tool{Colors.END}\n")

    # Load .env files
    env_vars = load_env_files()
    print(f"{Colors.GREEN}✓ Loaded {len(env_vars)} environment variables{Colors.END}\n")

    # Get Render API key
    api_key = get_render_api_key(env_vars)
    print(f"{Colors.GREEN}✓ Render API key found{Colors.END}\n")

    # Get Render services
    print(f"{Colors.BLUE}🔍 Fetching Render services...{Colors.END}")
    services = get_render_services(api_key)
    print(f"{Colors.GREEN}✓ Found {len(services)} services{Colors.END}\n")

    # Find target service
    service = find_service_by_name(services, args.service)
    service_id = service['id']
    service_name = service['name']

    print(f"{Colors.CYAN}📦 Target service: {service_name} ({service_id}){Colors.END}")

    # Get current env vars
    print(f"{Colors.BLUE}🔍 Fetching current environment variables...{Colors.END}")
    current_env_vars = get_service_env_vars(api_key, service_id)
    print(f"{Colors.GREEN}✓ Found {len(current_env_vars)} existing env vars{Colors.END}")

    # Sync secrets
    updated_vars, total_changes = sync_secrets(env_vars, current_env_vars, dry_run)

    # Apply changes
    if total_changes > 0:
        if dry_run:
            print(f"\n{Colors.YELLOW}💡 Run with --apply to apply these changes{Colors.END}")
        else:
            print(f"\n{Colors.BOLD}🚀 Applying changes to Render...{Colors.END}")
            success = update_service_env_vars(api_key, service_id, updated_vars, dry_run=False)

            if success:
                print(f"\n{Colors.GREEN}{Colors.BOLD}✓ Successfully synced secrets to Render!{Colors.END}")
                print(f"\n{Colors.YELLOW}⚠️  Note: Render will automatically redeploy your service{Colors.END}")
            else:
                print(f"\n{Colors.RED}❌ Failed to sync secrets{Colors.END}")
                sys.exit(1)
    else:
        print(f"\n{Colors.GREEN}✓ Nothing to do!{Colors.END}")


if __name__ == '__main__':
    main()