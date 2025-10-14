"""
Test d'intégration filtering workflow backend
Vérifie que le filtering 2-couches fonctionne end-to-end
"""

import pytest
from utils.message_filter import filter_for_ui, should_create_archive_note


class TestIntegrationFiltering:
    """Tests d'intégration workflow filtering"""

    def test_simulated_discussion_message_filtering(self):
        """Test simulation message discussion autogen filtré pour UI"""

        # Simulate backend internal message (Layer 1)
        backend_msg = """
        Reasoning: L'utilisateur demande une recherche.
        Internal: Je vais utiliser search_knowledge.
        [TOOL_START: search_knowledge]
        Tool params: {"query": "projet X", "limit": 10}
        [TOOL_END: search_knowledge]

        J'ai trouvé 5 documents pertinents sur le projet X.
        """

        # Filter for frontend (Layer 2)
        filtered = filter_for_ui("mimir", backend_msg)

        # Verify internal content removed
        assert "Reasoning:" not in filtered["content"]
        assert "Internal:" not in filtered["content"]
        assert "[TOOL_START" not in filtered["content"]
        assert "Tool params:" not in filtered["content"]

        # Verify user-relevant content preserved
        assert "trouvé 5 documents" in filtered["content"]
        assert "projet X" in filtered["content"]

    def test_simulated_storage_works_only(self):
        """Test storage Works uniquement (pas Archives)"""

        conversation_data = {
            "user_input": "Salut, comment ça va ?",
            "tools_used": []  # Pas de create_note
        }

        # Ne devrait PAS créer note Archives
        assert should_create_archive_note(conversation_data) is False

    def test_simulated_storage_archives_create_note_tool(self):
        """Test storage Archives quand create_note tool utilisé"""

        conversation_data = {
            "user_input": "Recherche projet X",
            "tools_used": ["search_knowledge", "create_note"]  # create_note utilisé
        }

        # DOIT créer note Archives
        assert should_create_archive_note(conversation_data) is True

    def test_simulated_storage_archives_explicit_request(self):
        """Test storage Archives quand user demande explicitement"""

        conversation_data = {
            "user_input": "Crée une note avec ces infos sur projet X",
            "tools_used": ["search_knowledge"]  # Pas create_note tool, mais user dit "crée une note"
        }

        # DOIT créer note Archives (intent explicite)
        assert should_create_archive_note(conversation_data) is True

    def test_workflow_casual_chat_whatsapp_style(self):
        """Test workflow casual chat WhatsApp-style"""

        # Message backend verbeux
        backend = """
        Reasoning: Salutation simple, pas besoin search.
        Debug: Plume répond directement.

        Salut ! Je suis Plume. Comment puis-je t'aider aujourd'hui ?
        """

        # Filter
        filtered = filter_for_ui("plume", backend)

        # Verification
        assert "Reasoning:" not in filtered["content"]
        assert "Debug:" not in filtered["content"]
        assert "Salut !" in filtered["content"]
        assert "Comment puis-je t'aider" in filtered["content"]

        # Storage decision
        assert should_create_archive_note({
            "user_input": "salut",
            "tools_used": []
        }) is False  # Works only, pas Archives

    def test_workflow_complex_query_with_tools(self):
        """Test workflow query complexe avec tools et archivage"""

        # User input
        user_input = "Recherche toutes les infos sur projet X et crée une note"

        # Backend processing (verbose)
        backend_mimir = """
        Reasoning: Query nécessite search_knowledge.
        [TOOL_START: search_knowledge]
        Tool params: {"query": "projet X"}
        [TOOL_END: search_knowledge]

        J'ai trouvé 8 documents. Les plus pertinents concernent l'architecture.
        """

        backend_plume = """
        Internal: Je reformule la synthèse de Mimir.

        Résumé: Projet X utilise Python/React, budget 50K€, livraison Q2 2025.
        """

        # Filter both
        filtered_mimir = filter_for_ui("mimir", backend_mimir)
        filtered_plume = filter_for_ui("plume", backend_plume)

        # Verify filtering
        assert "Reasoning:" not in filtered_mimir["content"]
        assert "[TOOL_START" not in filtered_mimir["content"]
        assert "trouvé 8 documents" in filtered_mimir["content"]

        assert "Internal:" not in filtered_plume["content"]
        assert "Résumé:" in filtered_plume["content"] or "Python/React" in filtered_plume["content"]

        # Storage decision (create_note tool used)
        assert should_create_archive_note({
            "user_input": user_input,
            "tools_used": ["search_knowledge", "create_note"]
        }) is True  # Works + Archives


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
