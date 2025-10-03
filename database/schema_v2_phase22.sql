-- Plume & Mimir Database Schema - Phase 2.2 Compatible
-- PostgreSQL with pgvector extension for embeddings
-- Compatible with backend API expectations

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Documents table for file uploads and processing
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL DEFAULT 'king_001',
    filename TEXT NOT NULL,
    title TEXT NOT NULL,
    content_text TEXT NOT NULL,
    content_html TEXT NOT NULL,
    file_type TEXT NOT NULL DEFAULT 'text/plain',
    file_size INTEGER,
    upload_source TEXT DEFAULT 'manual',
    processing_status TEXT DEFAULT 'completed' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',
    is_deleted BOOLEAN DEFAULT FALSE
);

-- Notes table (UPDATED for Phase 2.2 backend compatibility)
CREATE TABLE IF NOT EXISTS notes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL DEFAULT 'king_001',
    title TEXT NOT NULL,
    text_content TEXT NOT NULL,  -- Renamed from 'content'
    html_content TEXT,            -- Renamed from 'html'
    document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',
    is_deleted BOOLEAN DEFAULT FALSE
);

-- Embeddings table for RAG
CREATE TABLE IF NOT EXISTS embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    note_id UUID REFERENCES notes(id) ON DELETE CASCADE,
    chunk_text TEXT NOT NULL,
    embedding vector(1536), -- OpenAI text-embedding-3-large dimensions
    chunk_index INTEGER NOT NULL,
    chunk_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Conversations table for chat history
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL DEFAULT 'king_001',
    title TEXT DEFAULT 'Nouvelle conversation',
    note_titles TEXT[] DEFAULT '{}',
    message_count INTEGER DEFAULT 0,
    messages JSONB NOT NULL DEFAULT '[]',
    agents_involved TEXT[] DEFAULT '{}',
    session_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE
);

-- Search analytics for optimization
CREATE TABLE IF NOT EXISTS search_queries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query TEXT NOT NULL,
    results_count INTEGER,
    execution_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for optimal performance

-- Vector similarity search with ivfflat
CREATE INDEX IF NOT EXISTS idx_embeddings_vector ON embeddings
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Full-text search in French (UPDATED column names)
CREATE INDEX IF NOT EXISTS idx_notes_fulltext_french ON notes
USING GIN (to_tsvector('french', title || ' ' || text_content));

-- Standard indexes
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents (user_id);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_documents_filename ON documents (filename);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents (processing_status);
CREATE INDEX IF NOT EXISTS idx_documents_tags ON documents USING GIN (tags);
CREATE INDEX IF NOT EXISTS idx_documents_metadata ON documents USING GIN (metadata);

CREATE INDEX IF NOT EXISTS idx_notes_user_id ON notes (user_id);
CREATE INDEX IF NOT EXISTS idx_notes_created_at ON notes (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notes_tags ON notes USING GIN (tags);
CREATE INDEX IF NOT EXISTS idx_notes_metadata ON notes USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_notes_document_id ON notes (document_id);

CREATE INDEX IF NOT EXISTS idx_embeddings_document_id ON embeddings (document_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_note_id ON embeddings (note_id);

CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations (user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_session_id ON conversations (session_id);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations (created_at DESC);

-- Updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers (DROP IF EXISTS to avoid errors)
DROP TRIGGER IF EXISTS update_documents_updated_at ON documents;
CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_notes_updated_at ON notes;
CREATE TRIGGER update_notes_updated_at BEFORE UPDATE ON notes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_conversations_updated_at ON conversations;
CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- RPC Functions for RAG search (UPDATED column names)

-- Vector similarity search function
CREATE OR REPLACE FUNCTION match_documents(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.78,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    note_id UUID,
    chunk_text TEXT,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        e.id,
        e.note_id,
        e.chunk_text,
        1 - (e.embedding <=> query_embedding) AS similarity
    FROM embeddings e
    JOIN notes n ON e.note_id = n.id
    WHERE n.is_deleted = FALSE
    AND 1 - (e.embedding <=> query_embedding) > match_threshold
    ORDER BY e.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Hybrid search combining vector and full-text (UPDATED column names)
CREATE OR REPLACE FUNCTION hybrid_search(
    query_text TEXT,
    query_embedding vector(1536) DEFAULT NULL,
    match_threshold float DEFAULT 0.78,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    note_id UUID,
    title TEXT,
    chunk_text TEXT,
    similarity float,
    rank float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        e.id,
        e.note_id,
        n.title,
        e.chunk_text,
        CASE
            WHEN query_embedding IS NOT NULL
            THEN 1 - (e.embedding <=> query_embedding)
            ELSE 0.0
        END AS similarity,
        ts_rank_cd(
            to_tsvector('french', n.title || ' ' || n.text_content),
            plainto_tsquery('french', query_text)
        ) AS rank
    FROM embeddings e
    JOIN notes n ON e.note_id = n.id
    WHERE n.is_deleted = FALSE
    AND (
        (query_embedding IS NOT NULL AND 1 - (e.embedding <=> query_embedding) > match_threshold)
        OR to_tsvector('french', n.title || ' ' || n.text_content) @@ plainto_tsquery('french', query_text)
    )
    ORDER BY
        CASE
            WHEN query_embedding IS NOT NULL
            THEN (1 - (e.embedding <=> query_embedding)) * 0.7 + ts_rank_cd(to_tsvector('french', n.title || ' ' || n.text_content), plainto_tsquery('french', query_text)) * 0.3
            ELSE ts_rank_cd(to_tsvector('french', n.title || ' ' || n.text_content), plainto_tsquery('french', query_text))
        END DESC
    LIMIT match_count;
END;
$$;

-- Fulltext search function (from migration 003)
CREATE OR REPLACE FUNCTION search_notes_fulltext(
    search_query TEXT,
    user_id_param TEXT,
    limit_param INT
)
RETURNS TABLE (
    id UUID,
    title TEXT,
    text_content TEXT,
    html_content TEXT,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    relevance_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        n.id,
        n.title,
        n.text_content,
        n.html_content,
        n.created_at,
        n.updated_at,
        ts_rank(
            to_tsvector('french', n.title || ' ' || n.text_content),
            to_tsquery('french', search_query)
        ) AS relevance_score
    FROM notes n
    WHERE
        n.user_id = user_id_param
        AND to_tsvector('french', n.title || ' ' || n.text_content) @@ to_tsquery('french', search_query)
    ORDER BY relevance_score DESC
    LIMIT limit_param;
END;
$$ LANGUAGE plpgsql;

-- Row Level Security (RLS) setup for future multi-user support
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE search_queries ENABLE ROW LEVEL SECURITY;

-- For now, allow all operations (single user)
-- These policies can be refined later for multi-user scenarios
DROP POLICY IF EXISTS "Allow all operations on documents" ON documents;
CREATE POLICY "Allow all operations on documents" ON documents FOR ALL USING (true);

DROP POLICY IF EXISTS "Allow all operations on notes" ON notes;
CREATE POLICY "Allow all operations on notes" ON notes FOR ALL USING (true);

DROP POLICY IF EXISTS "Allow all operations on embeddings" ON embeddings;
CREATE POLICY "Allow all operations on embeddings" ON embeddings FOR ALL USING (true);

DROP POLICY IF EXISTS "Allow all operations on conversations" ON conversations;
CREATE POLICY "Allow all operations on conversations" ON conversations FOR ALL USING (true);

DROP POLICY IF EXISTS "Allow all operations on search_queries" ON search_queries;
CREATE POLICY "Allow all operations on search_queries" ON search_queries FOR ALL USING (true);

-- Performance monitoring views (UPDATED column names)
CREATE OR REPLACE VIEW performance_stats AS
SELECT
    'notes' as table_name,
    COUNT(*) as row_count,
    pg_size_pretty(pg_total_relation_size('notes')) as size
FROM notes
UNION ALL
SELECT
    'embeddings' as table_name,
    COUNT(*) as row_count,
    pg_size_pretty(pg_total_relation_size('embeddings')) as size
FROM embeddings
UNION ALL
SELECT
    'conversations' as table_name,
    COUNT(*) as row_count,
    pg_size_pretty(pg_total_relation_size('conversations')) as size
FROM conversations;

-- Comment
COMMENT ON TABLE notes IS 'Phase 2.2 compatible notes table with user_id, text_content, html_content';
COMMENT ON FUNCTION search_notes_fulltext IS 'Fulltext search in notes with French language support and relevance scoring';
