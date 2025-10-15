"""
Test enhanced tool_message_formatter patterns
Validates that production-observed formats are properly cleaned
"""

import pytest
from utils.tool_message_formatter import format_tool_activity_for_ui


class TestEnhancedToolFormatter:
    """Test new regex patterns added to handle production logs"""

    def test_clean_note_id_dict(self):
        """Test cleaning dict with note_id (observed in production)"""
        raw = "Note created {'note_id': 'b38160c1-6e76-4b91-9645-ed6785932301', 'title': 'Test'}"
        cleaned = format_tool_activity_for_ui(raw, 'plume')

        assert 'note_id' not in cleaned
        assert 'b38160c1' not in cleaned
        assert cleaned.strip() == "Note created"

    def test_clean_created_at_timestamp(self):
        """Test cleaning dict with created_at timestamp"""
        raw = "{'success': True, 'created_at': '2025-10-14T13:09:41.073607+00:00'}"
        cleaned = format_tool_activity_for_ui(raw, 'mimir')

        assert 'created_at' not in cleaned
        assert '2025-10-14' not in cleaned
        assert cleaned.strip() == ""  # Should be completely removed

    def test_clean_confidence_dict(self):
        """Test cleaning dict with confidence scores"""
        raw = "Found results {'count': 2, 'confidence': 0.58}"
        cleaned = format_tool_activity_for_ui(raw, 'mimir')

        assert 'confidence' not in cleaned
        assert '0.58' not in cleaned
        assert 'count' not in cleaned
        assert cleaned.strip() == "Found results"

    def test_clean_complex_production_case(self):
        """
        Test exact format from production logs:
        {'success': True, 'note_id': 'b38160c1-...', 'title': '...', 'created_at': '2025-...'}
        """
        raw = "{'success': True, 'note_id': 'b38160c1-6e76-4b91-9645-ed6785932301', 'title': 'Communauté égyptienne Al Masri à Gaza', 'created_at': '2025-10-14T13:09:41.073607+00:00'}"
        cleaned = format_tool_activity_for_ui(raw, 'plume')

        # Should be completely removed (no user-facing value)
        assert 'success' not in cleaned
        assert 'note_id' not in cleaned
        assert 'title' not in cleaned
        assert 'created_at' not in cleaned
        assert 'b38160c1' not in cleaned
        assert '2025-10-14' not in cleaned

        # Result should be empty or whitespace only
        assert len(cleaned.strip()) == 0

    def test_clean_function_call_with_dict(self):
        """Test FunctionCall followed by dict result"""
        raw = "[FunctionCall(name='create_note', arguments='{...}')] {'success': True, 'note_id': 'abc123'}"
        cleaned = format_tool_activity_for_ui(raw, 'plume')

        assert 'FunctionCall' not in cleaned
        assert 'success' not in cleaned
        assert 'note_id' not in cleaned
        assert '✍️' in cleaned  # Should contain create_note emoji

    def test_clean_fragment_pattern_from_logs(self):
        """Test fragment pattern: ], 'count': 2, 'confidence': 0.58}"""
        raw = "Results: [doc1, doc2], 'count': 2, 'confidence': 0.58}"
        cleaned = format_tool_activity_for_ui(raw, 'mimir')

        assert 'count' not in cleaned
        assert 'confidence' not in cleaned
        assert cleaned.strip().startswith("Results:")

    def test_preserve_user_friendly_content(self):
        """Ensure user-facing content is NOT removed"""
        raw = "J'ai trouvé 5 documents pertinents sur ce sujet."
        cleaned = format_tool_activity_for_ui(raw, 'mimir')

        assert cleaned == raw  # Should be unchanged

    def test_mixed_content_technical_and_human(self):
        """Test message with both technical and human-friendly parts"""
        raw = "🔍 Recherche effectuée {'results': 5, 'confidence': 0.92}. Voici ce que j'ai trouvé."
        cleaned = format_tool_activity_for_ui(raw, 'mimir')

        assert 'results' not in cleaned
        assert 'confidence' not in cleaned
        assert '🔍 Recherche effectuée' in cleaned
        assert 'Voici ce que j\'ai trouvé' in cleaned


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
