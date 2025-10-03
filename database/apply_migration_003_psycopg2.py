#!/usr/bin/env python3
"""
Apply migration 003: Add fulltext search function using psycopg2
"""

import os
import sys
import psycopg2
from urllib.parse import urlparse

def apply_migration():
    """Apply migration 003_search_function.sql"""

    # Get Supabase URL and convert to PostgreSQL connection string
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')

    if not supabase_url:
        print("❌ Missing SUPABASE_URL environment variable")
        print("\n📋 Instructions:")
        print("   1. Go to Supabase Dashboard → SQL Editor")
        print("   2. Copy content of: database/migrations/003_search_function.sql")
        print("   3. Execute in SQL Editor")
        sys.exit(1)

    # Parse Supabase URL to get database connection info
    # Format: https://xxx.supabase.co
    # PostgreSQL: postgres://postgres:[password]@db.xxx.supabase.co:5432/postgres

    # Extract project reference from URL
    parsed = urlparse(supabase_url)
    project_ref = parsed.hostname.split('.')[0] if parsed.hostname else None

    if not project_ref:
        print("❌ Invalid SUPABASE_URL format")
        sys.exit(1)

    # Database password (usually same as service key or separate)
    db_password = os.getenv('SUPABASE_DB_PASSWORD') or supabase_service_key

    if not db_password:
        print("❌ Missing database credentials")
        print("\n📋 Alternative: Apply migration via Supabase Dashboard SQL Editor")
        print(f"   File: database/migrations/003_search_function.sql")
        sys.exit(1)

    # Construct PostgreSQL connection string
    db_url = f"postgresql://postgres.{project_ref}:{db_password}@aws-0-us-west-1.pooler.supabase.com:6543/postgres"

    print(f"🔗 Connecting to Supabase database...")

    try:
        # Connect to database
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cursor = conn.cursor()

        # Read migration SQL
        migration_path = os.path.join(os.path.dirname(__file__), 'migrations', '003_search_function.sql')

        print(f"📖 Reading migration from {migration_path}...")
        with open(migration_path, 'r') as f:
            sql = f.read()

        print("🚀 Applying migration...")
        cursor.execute(sql)

        print("✅ Migration 003 applied successfully!")

        # Test the function
        print("\n🧪 Testing search function...")
        cursor.execute("""
            SELECT search_notes_fulltext('test', 'king_001', 5);
        """)

        result = cursor.fetchall()
        print(f"✅ Search function working! Test query returned {len(result)} results")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        print("\n📋 Alternative: Apply migration manually via Supabase Dashboard")
        print("   1. Go to Supabase Dashboard → SQL Editor")
        print("   2. Copy content of: database/migrations/003_search_function.sql")
        print("   3. Execute in SQL Editor")
        sys.exit(1)

if __name__ == "__main__":
    apply_migration()
