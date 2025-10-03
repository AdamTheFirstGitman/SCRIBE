#!/usr/bin/env python3
"""Apply migration 004: Fix hybrid_search function"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
    sys.exit(1)

def apply_migration():
    """Apply migration 004 to fix hybrid_search function"""
    try:
        # Create Supabase client
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        print("✅ Connected to Supabase")

        # Read migration SQL
        migration_file = os.path.join(os.path.dirname(__file__), "migrations", "004_fix_hybrid_search.sql")
        with open(migration_file, 'r') as f:
            sql = f.read()

        print("📄 Migration SQL loaded")
        print(f"📝 Applying migration 004...")

        # Execute migration using RPC
        # Note: Supabase Python client doesn't have direct SQL execution
        # We need to use psycopg2 for this
        print("\n⚠️  This migration requires direct database access.")
        print("Please run the following SQL in Supabase SQL Editor:")
        print("\n" + "="*80)
        print(sql)
        print("="*80 + "\n")

        print("Or use psycopg2 with DATABASE_URL to apply automatically.")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    apply_migration()
