-- Migration: Add Memory Features (Long-term + User Preferences)
-- Date: 2025-09-30
-- Description: Adds embeddings to messages and creates user_preferences table

-- =============================================================================
-- 1. ADD EMBEDDING COLUMN TO MESSAGES TABLE
-- =============================================================================

-- Add vector extension if not exists (required for pgvector)
CREATE EXTENSION IF NOT EXISTS vector;

-- Add embedding column to messages table
ALTER TABLE messages
ADD COLUMN IF NOT EXISTS embedding vector(1536);

-- Create index on embedding for fast similarity search
CREATE INDEX IF NOT EXISTS messages_embedding_idx
ON messages USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Add comment
COMMENT ON COLUMN messages.embedding IS 'Vector embedding for semantic search (1536 dimensions from text-embedding-3-large)';

-- =============================================================================
-- 2. CREATE USER_PREFERENCES TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE,
    preferred_agent TEXT DEFAULT 'auto' CHECK (preferred_agent IN ('auto', 'plume', 'mimir')),
    topics_of_interest TEXT[] DEFAULT '{}',
    interaction_patterns JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Foreign key to users table (if exists)
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE
);

-- Create indexes
CREATE INDEX IF NOT EXISTS user_preferences_user_id_idx ON user_preferences(user_id);
CREATE INDEX IF NOT EXISTS user_preferences_updated_at_idx ON user_preferences(updated_at DESC);

-- Add comments
COMMENT ON TABLE user_preferences IS 'User preferences and interaction patterns for personalization';
COMMENT ON COLUMN user_preferences.preferred_agent IS 'Default agent preference (auto, plume, or mimir)';
COMMENT ON COLUMN user_preferences.topics_of_interest IS 'Array of user favorite topics';
COMMENT ON COLUMN user_preferences.interaction_patterns IS 'JSON object with usage analytics and patterns';

-- =============================================================================
-- 3. CREATE SEARCH FUNCTION FOR SIMILAR MESSAGES
-- =============================================================================

-- Function to search similar messages using vector similarity
CREATE OR REPLACE FUNCTION search_similar_messages(
    query_embedding vector(1536),
    p_user_id UUID,
    p_cutoff_date TIMESTAMP WITH TIME ZONE,
    p_exclude_conversation_id UUID DEFAULT NULL,
    p_limit INT DEFAULT 5
)
RETURNS TABLE (
    id UUID,
    conversation_id UUID,
    role TEXT,
    content TEXT,
    created_at TIMESTAMP WITH TIME ZONE,
    conversation_title TEXT,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        m.id,
        m.conversation_id,
        m.role,
        m.content,
        m.created_at,
        c.title as conversation_title,
        1 - (m.embedding <=> query_embedding) as similarity
    FROM messages m
    JOIN conversations c ON m.conversation_id = c.id
    WHERE
        c.user_id = p_user_id
        AND m.created_at > p_cutoff_date
        AND (p_exclude_conversation_id IS NULL OR m.conversation_id != p_exclude_conversation_id)
        AND m.embedding IS NOT NULL
    ORDER BY m.embedding <=> query_embedding
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql STABLE;

-- Add comment
COMMENT ON FUNCTION search_similar_messages IS 'Search semantically similar messages using vector embeddings';

-- =============================================================================
-- 4. ADD SUMMARY COLUMN TO CONVERSATIONS TABLE
-- =============================================================================

-- Add summary column for auto-generated conversation summaries
ALTER TABLE conversations
ADD COLUMN IF NOT EXISTS summary TEXT;

-- Add comment
COMMENT ON COLUMN conversations.summary IS 'Auto-generated conversation summary for quick context';

-- =============================================================================
-- 5. UPDATE EXISTING DATA (Optional - can be run separately)
-- =============================================================================

-- Update existing conversations to add default agents_used if NULL
UPDATE conversations
SET agents_used = ARRAY['plume']::TEXT[]
WHERE agents_used IS NULL OR array_length(agents_used, 1) IS NULL;

-- =============================================================================
-- 6. ROW LEVEL SECURITY (RLS) FOR USER_PREFERENCES
-- =============================================================================

-- Enable RLS on user_preferences
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own preferences
CREATE POLICY user_preferences_select_policy ON user_preferences
    FOR SELECT
    USING (auth.uid() = user_id);

-- Policy: Users can only insert their own preferences
CREATE POLICY user_preferences_insert_policy ON user_preferences
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Policy: Users can only update their own preferences
CREATE POLICY user_preferences_update_policy ON user_preferences
    FOR UPDATE
    USING (auth.uid() = user_id);

-- Policy: Users can only delete their own preferences
CREATE POLICY user_preferences_delete_policy ON user_preferences
    FOR DELETE
    USING (auth.uid() = user_id);

-- =============================================================================
-- 7. CREATE UPDATED_AT TRIGGER FOR USER_PREFERENCES
-- =============================================================================

-- Trigger function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to user_preferences
DROP TRIGGER IF EXISTS update_user_preferences_updated_at ON user_preferences;
CREATE TRIGGER update_user_preferences_updated_at
    BEFORE UPDATE ON user_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- 8. PERFORMANCE INDEXES
-- =============================================================================

-- Index on conversations for user_id and created_at (for history queries)
CREATE INDEX IF NOT EXISTS conversations_user_id_created_at_idx
ON conversations(user_id, created_at DESC);

-- Index on messages for conversation_id and created_at (for recent messages)
CREATE INDEX IF NOT EXISTS messages_conversation_id_created_at_idx
ON messages(conversation_id, created_at DESC);

-- =============================================================================
-- ROLLBACK SCRIPT (For reference - do not execute)
-- =============================================================================

/*
-- To rollback this migration, run:

DROP FUNCTION IF EXISTS search_similar_messages(vector, UUID, TIMESTAMP WITH TIME ZONE, UUID, INT);
DROP INDEX IF EXISTS messages_embedding_idx;
ALTER TABLE messages DROP COLUMN IF EXISTS embedding;
ALTER TABLE conversations DROP COLUMN IF EXISTS summary;
DROP TABLE IF EXISTS user_preferences;

*/

-- =============================================================================
-- MIGRATION COMPLETE
-- =============================================================================

-- Insert migration record (if migrations table exists)
DO $$
BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'migrations') THEN
        INSERT INTO migrations (name, executed_at)
        VALUES ('002_add_memory_features', NOW())
        ON CONFLICT (name) DO NOTHING;
    END IF;
END $$;