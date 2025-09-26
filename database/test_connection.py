#!/usr/bin/env python3
"""
Test script for Supabase connection and database schema validation
"""

import os
import asyncio
from typing import List, Dict, Any
from supabase import create_client, Client
import numpy as np
from datetime import datetime

# Test configuration
TEST_CONFIG = {
    'supabase_url': os.getenv('SUPABASE_URL', 'your-supabase-url'),
    'supabase_key': os.getenv('SUPABASE_ANON_KEY', 'your-supabase-key'),
}

class SupabaseConnectionTest:
    def __init__(self):
        self.supabase: Client = create_client(
            TEST_CONFIG['supabase_url'],
            TEST_CONFIG['supabase_key']
        )

    async def test_connection(self) -> bool:
        """Test basic connection to Supabase"""
        try:
            # Simple health check
            result = self.supabase.table('notes').select('id').limit(1).execute()
            print("✅ Connection successful")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False

    def test_schema_tables(self) -> bool:
        """Test that all required tables exist"""
        required_tables = ['notes', 'embeddings', 'conversations', 'search_queries']

        try:
            for table in required_tables:
                result = self.supabase.table(table).select('*').limit(1).execute()
                print(f"✅ Table '{table}' exists and accessible")
            return True
        except Exception as e:
            print(f"❌ Schema validation failed: {e}")
            return False

    def test_pgvector_extension(self) -> bool:
        """Test pgvector extension functionality"""
        try:
            # Create test embedding
            test_embedding = np.random.rand(1536).tolist()

            # Test note creation
            note_result = self.supabase.table('notes').insert({
                'title': 'Test Note for Vector',
                'content': 'This is a test note to validate pgvector functionality',
                'metadata': {'test': True}
            }).execute()

            note_id = note_result.data[0]['id']

            # Test embedding insertion
            embedding_result = self.supabase.table('embeddings').insert({
                'note_id': note_id,
                'chunk_text': 'Test chunk for vector search',
                'embedding': test_embedding,
                'chunk_index': 0
            }).execute()

            print("✅ pgvector extension working - embedding stored successfully")

            # Cleanup
            self.supabase.table('embeddings').delete().eq('note_id', note_id).execute()
            self.supabase.table('notes').delete().eq('id', note_id).execute()

            return True
        except Exception as e:
            print(f"❌ pgvector test failed: {e}")
            return False

    def test_rpc_functions(self) -> bool:
        """Test RPC functions for vector search"""
        try:
            # Create test data
            test_embedding = np.random.rand(1536).tolist()

            # Test match_documents RPC
            result = self.supabase.rpc('match_documents', {
                'query_embedding': test_embedding,
                'match_threshold': 0.1,
                'match_count': 5
            }).execute()

            print("✅ match_documents RPC function working")

            # Test hybrid_search RPC
            result = self.supabase.rpc('hybrid_search', {
                'query_text': 'test query',
                'match_count': 5
            }).execute()

            print("✅ hybrid_search RPC function working")
            return True
        except Exception as e:
            print(f"❌ RPC functions test failed: {e}")
            return False

    def test_full_workflow(self) -> bool:
        """Test complete workflow: insert note -> create embeddings -> search"""
        try:
            # 1. Insert test note
            note_data = {
                'title': 'Plume & Mimir Test Note',
                'content': 'This is a comprehensive test of the Plume & Mimir system. It includes various features like vector search, full-text search, and hybrid retrieval.',
                'html': '<p>This is a comprehensive test of the <strong>Plume & Mimir</strong> system.</p>',
                'tags': ['test', 'plume', 'mimir'],
                'metadata': {
                    'test_type': 'full_workflow',
                    'created_by': 'test_script',
                    'timestamp': datetime.now().isoformat()
                }
            }

            note_result = self.supabase.table('notes').insert(note_data).execute()
            note_id = note_result.data[0]['id']
            print(f"✅ Test note created: {note_id}")

            # 2. Create test embeddings
            chunks = [
                'This is a comprehensive test of the Plume & Mimir system.',
                'It includes various features like vector search.',
                'Full-text search and hybrid retrieval are also tested.'
            ]

            for i, chunk in enumerate(chunks):
                embedding = np.random.rand(1536).tolist()
                embedding_data = {
                    'note_id': note_id,
                    'chunk_text': chunk,
                    'embedding': embedding,
                    'chunk_index': i,
                    'chunk_metadata': {'chunk_type': 'test', 'position': i}
                }

                self.supabase.table('embeddings').insert(embedding_data).execute()

            print("✅ Test embeddings created")

            # 3. Test search functionality
            search_result = self.supabase.rpc('hybrid_search', {
                'query_text': 'Plume Mimir system',
                'match_count': 10
            }).execute()

            print(f"✅ Search test completed - found {len(search_result.data)} results")

            # 4. Test conversation logging
            conversation_data = {
                'messages': [
                    {'role': 'user', 'content': 'Test message', 'timestamp': datetime.now().isoformat()},
                    {'role': 'plume', 'content': 'Test response from Plume', 'timestamp': datetime.now().isoformat()}
                ],
                'agents_involved': ['plume'],
                'session_id': 'test_session_123'
            }

            conversation_result = self.supabase.table('conversations').insert(conversation_data).execute()
            conversation_id = conversation_result.data[0]['id']
            print("✅ Conversation logging tested")

            # Cleanup
            self.supabase.table('conversations').delete().eq('id', conversation_id).execute()
            self.supabase.table('embeddings').delete().eq('note_id', note_id).execute()
            self.supabase.table('notes').delete().eq('id', note_id).execute()
            print("✅ Cleanup completed")

            return True
        except Exception as e:
            print(f"❌ Full workflow test failed: {e}")
            return False

    def test_performance(self) -> bool:
        """Test performance monitoring views"""
        try:
            # Test performance stats view
            result = self.supabase.table('performance_stats').select('*').execute()

            print("📊 Database Performance Stats:")
            for row in result.data:
                print(f"   {row['table_name']}: {row['row_count']} rows, {row['size']}")

            return True
        except Exception as e:
            print(f"❌ Performance test failed: {e}")
            return False

async def run_all_tests():
    """Run all database tests"""
    print("🚀 Starting Supabase Database Tests for Plume & Mimir\n")

    # Check environment variables
    if TEST_CONFIG['supabase_url'] == 'your-supabase-url':
        print("❌ Please set SUPABASE_URL environment variable")
        return False

    if TEST_CONFIG['supabase_key'] == 'your-supabase-key':
        print("❌ Please set SUPABASE_ANON_KEY environment variable")
        return False

    tester = SupabaseConnectionTest()

    tests = [
        ('Connection Test', tester.test_connection),
        ('Schema Validation', tester.test_schema_tables),
        ('pgvector Extension', tester.test_pgvector_extension),
        ('RPC Functions', tester.test_rpc_functions),
        ('Full Workflow', tester.test_full_workflow),
        ('Performance Monitoring', tester.test_performance),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name}...")
        if await test_func() if asyncio.iscoroutinefunction(test_func) else test_func():
            passed += 1
        else:
            print(f"   Test '{test_name}' failed!")

    print(f"\n📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Database is ready for Plume & Mimir.")
        return True
    else:
        print("⚠️  Some tests failed. Please check your database setup.")
        return False

if __name__ == "__main__":
    # Example usage
    print("Plume & Mimir Database Connection Test")
    print("=====================================")
    print()
    print("Before running this test, make sure you have:")
    print("1. Created a Supabase project")
    print("2. Applied the schema.sql file")
    print("3. Set environment variables:")
    print("   export SUPABASE_URL='your-supabase-url'")
    print("   export SUPABASE_ANON_KEY='your-supabase-key'")
    print()

    # Run tests
    asyncio.run(run_all_tests())