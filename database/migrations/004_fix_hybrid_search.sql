-- Migration 004: Fix hybrid_search function SQL error
-- Issue: SELECT DISTINCT with ORDER BY expression not in select list
-- Error code: 42P10
-- Fix: Remove DISTINCT (unnecessary since e.id is unique)
-- Date: 2025-10-01
-- Phase: 2.2 Backend SSE Streaming
-- Applied: 2025-10-03 via Supabase SQL Editor

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
        )::float AS rank
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
            THEN (1 - (e.embedding <=> query_embedding)) * 0.7 + ts_rank_cd(to_tsvector('french', n.title || ' ' || n.text_content), plainto_tsquery('french', query_text))::float * 0.3
            ELSE ts_rank_cd(to_tsvector('french', n.title || ' ' || n.text_content), plainto_tsquery('french', query_text))::float
        END DESC
    LIMIT match_count;
END;
$$;

COMMENT ON FUNCTION hybrid_search IS 'Hybrid search combining vector similarity and fulltext search';
