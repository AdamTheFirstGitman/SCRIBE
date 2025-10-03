#!/usr/bin/env python3
"""
Apply migration 003: Add fulltext search function
"""

import os
import sys
from supabase import create_client

def apply_migration():
    """Apply migration 003_search_function.sql"""

    # Get Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_ANON_KEY')

    if not supabase_url or not supabase_key:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_KEY environment variables")
        sys.exit(1)

    print("🔗 Connecting to Supabase...")
    supabase = create_client(supabase_url, supabase_key)

    # Read migration SQL
    migration_path = os.path.join(os.path.dirname(__file__), 'migrations', '003_search_function.sql')

    print(f"📖 Reading migration from {migration_path}...")
    with open(migration_path, 'r') as f:
        sql = f.read()

    print("🚀 Applying migration...")

    try:
        # Execute the migration using SQL query
        # Note: Supabase Python client doesn't have direct SQL execution
        # We need to use the REST API or supabase-py v2 features

        # Split SQL into statements
        statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]

        for i, statement in enumerate(statements):
            if statement:
                print(f"  Executing statement {i+1}/{len(statements)}...")
                # Using PostgREST RPC to execute raw SQL
                result = supabase.rpc('exec_sql', {'query': statement}).execute()
                print(f"  ✅ Statement {i+1} executed")

        print("✅ Migration 003 applied successfully!")

        # Test the function
        print("\n🧪 Testing search function...")
        result = supabase.rpc('search_notes_fulltext', {
            'search_query': 'test',
            'user_id_param': 'king_001',
            'limit_param': 5
        }).execute()

        print(f"✅ Search function working! Found {len(result.data)} results")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        print("\n⚠️  Alternative: Apply migration manually via Supabase Dashboard")
        print("   1. Go to Supabase Dashboard → SQL Editor")
        print(f"   2. Copy content of: {migration_path}")
        print("   3. Execute in SQL Editor")
        sys.exit(1)

if __name__ == "__main__":
    apply_migration()
