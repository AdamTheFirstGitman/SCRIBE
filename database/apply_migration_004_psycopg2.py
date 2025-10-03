#!/usr/bin/env python3
"""Apply migration 004: Fix hybrid_search function using psycopg2"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_URL")

if not DATABASE_URL:
    print("❌ Error: DATABASE_URL or SUPABASE_URL must be set in .env")
    print("Format: postgresql://user:pass@host:5432/database")
    sys.exit(1)

def apply_migration():
    """Apply migration 004 to fix hybrid_search function"""
    try:
        # Convert Supabase URL to PostgreSQL URL if needed
        if DATABASE_URL.startswith("https://"):
            print("❌ Error: Need PostgreSQL connection string, not HTTP URL")
            print("Please set DATABASE_URL in format: postgresql://user:pass@host:5432/database")
            sys.exit(1)

        # Connect to database
        print(f"🔌 Connecting to database...")
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
        cursor = conn.cursor()
        print("✅ Connected to database")

        # Read migration SQL
        migration_file = os.path.join(os.path.dirname(__file__), "migrations", "004_fix_hybrid_search.sql")
        with open(migration_file, 'r') as f:
            sql = f.read()

        print("📄 Migration SQL loaded")
        print(f"📝 Applying migration 004: Fix hybrid_search function...")

        # Execute migration
        cursor.execute(sql)
        conn.commit()

        print("✅ Migration 004 applied successfully!")
        print("\n📊 Verification:")

        # Verify function exists
        cursor.execute("""
            SELECT proname, pg_get_functiondef(oid)::text LIKE '%DISTINCT%' as has_distinct
            FROM pg_proc
            WHERE proname = 'hybrid_search'
        """)
        result = cursor.fetchone()

        if result:
            func_name, has_distinct = result
            print(f"   ✓ Function '{func_name}' exists")
            print(f"   ✓ Contains DISTINCT: {'Yes ❌ (ISSUE!)' if has_distinct else 'No ✅ (FIXED!)'}")
        else:
            print("   ⚠️  Function 'hybrid_search' not found")

        cursor.close()
        conn.close()
        print("\n🎉 Migration completed successfully!")

    except psycopg2.Error as e:
        print(f"❌ Database Error: {e}")
        if conn:
            conn.rollback()
        sys.exit(1)
    except FileNotFoundError:
        print(f"❌ Migration file not found: {migration_file}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    apply_migration()
