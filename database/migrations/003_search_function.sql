-- Migration 003: Add fulltext search function for notes
-- Created for Phase 2.2 Backend API
-- Date: 2025-10-01

-- Create fulltext search function with French language support
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

-- Create GIN index on notes for faster fulltext search
CREATE INDEX IF NOT EXISTS notes_fulltext_idx ON notes
USING GIN (to_tsvector('french', title || ' ' || text_content));

-- Add comment
COMMENT ON FUNCTION search_notes_fulltext IS 'Fulltext search in notes with French language support and relevance scoring';
