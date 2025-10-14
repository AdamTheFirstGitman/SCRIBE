"""
Tests unitaires pour message_filter.py
Test du filtering 2-couches backend → frontend
"""

import pytest
from utils.message_filter import (
    MessageFilter,
    ToolActivityFilter,
    ConversationStorageFilter,
    filter_for_ui,
    filter_tool_for_ui,
    should_create_archive_note
)


class TestMessageFilter:
    """Tests pour MessageFilter class"""

    def test_filter_removes_internal_keywords(self):
        """Test que les keywords internes sont supprimés"""
        raw = """
        Reasoning: Je vais effectuer une recherche.
        Debug: Configuration tools chargée.
        Voici ma réponse finale pour l'utilisateur.
        """
        filtered = MessageFilter.filter_agent_message("plume", raw)

        assert "Reasoning:" not in filtered["content"]
        assert "Debug:" not in filtered["content"]
        assert "Voici ma réponse finale" in filtered["content"]

    def test_filter_removes_tool_call_syntax(self):
        """Test que la syntaxe tool calls est masquée"""
        raw = """
        [TOOL_START: search_knowledge]
        Tool params: {"query": "test", "limit": 10}
        [TOOL_END: search_knowledge]
        Résultat : J'ai trouvé 5 documents.
        """
        filtered = MessageFilter.filter_agent_message("mimir", raw)

        assert "[TOOL_START" not in filtered["content"]
        assert "[TOOL_END" not in filtered["content"]
        assert "Tool params:" not in filtered["content"]
        assert "trouvé 5 documents" in filtered["content"]

    def test_filter_condenses_long_messages(self):
        """Test que les messages trop longs sont condensés"""
        raw = "A" * 1000  # 1000 caractères
        filtered = MessageFilter.filter_agent_message("plume", raw)

        # Max 500 chars après condensation
        assert len(filtered["content"]) <= 500
        assert "[...]" in filtered["content"]  # Ellipsis ajouté

    def test_filter_preserves_short_messages(self):
        """Test que les messages courts sont préservés intacts"""
        raw = "Salut ! Je suis Plume."
        filtered = MessageFilter.filter_agent_message("plume", raw)

        assert filtered["content"] == raw.strip()
        assert filtered["filtered"] is True

    def test_extract_action_summary(self):
        """Test extraction résumé actions"""
        raw = """
        J'ai effectué plusieurs actions.
        En résumé: J'ai recherché dans les archives et trouvé 5 résultats.
        Voici les détails...
        """
        filtered = MessageFilter.filter_agent_message("mimir", raw)

        # Vérifie que action_summary est extrait
        assert filtered["action_summary"] is not None
        assert "recherché" in filtered["action_summary"]


class TestToolActivityFilter:
    """Tests pour ToolActivityFilter class"""

    def test_filter_search_knowledge_completed(self):
        """Test filtering tool search_knowledge completed"""
        activity = ToolActivityFilter.filter_tool_activity(
            tool_name="search_knowledge",
            tool_params={"query": "test", "limit": 10},
            tool_result={"success": True, "results_count": 5},
            status="completed"
        )

        assert activity["tool"] == "search_knowledge"
        assert activity["label"] == "🔍 Recherche archives"
        assert activity["status"] == "completed"
        assert "5 résultat" in activity["summary"]

    def test_filter_search_knowledge_running(self):
        """Test filtering tool search_knowledge running"""
        activity = ToolActivityFilter.filter_tool_activity(
            tool_name="search_knowledge",
            tool_params={"query": "test"},
            tool_result=None,
            status="running"
        )

        assert activity["status"] == "running"
        assert activity["summary"] == "Recherche en cours..."

    def test_filter_create_note_completed(self):
        """Test filtering tool create_note completed"""
        activity = ToolActivityFilter.filter_tool_activity(
            tool_name="create_note",
            tool_params={"title": "Test Note"},
            tool_result={"success": True, "note_id": "123"},
            status="completed"
        )

        assert activity["label"] == "📝 Création note"
        assert activity["summary"] == "Note créée"

    def test_filter_web_search(self):
        """Test filtering tool web_search"""
        activity = ToolActivityFilter.filter_tool_activity(
            tool_name="web_search",
            tool_params={"query": "test"},
            tool_result={"success": True, "sources_count": 3},
            status="completed"
        )

        assert activity["label"] == "🌐 Recherche web"
        assert "3 source" in activity["summary"]

    def test_filter_get_related_content(self):
        """Test filtering tool get_related_content"""
        activity = ToolActivityFilter.filter_tool_activity(
            tool_name="get_related_content",
            tool_params={"note_id": "123"},
            tool_result={"success": True, "related_count": 4},
            status="completed"
        )

        assert activity["label"] == "🔗 Contenus similaires"
        assert "4 connexion" in activity["summary"]

    def test_filter_update_note(self):
        """Test filtering tool update_note"""
        activity = ToolActivityFilter.filter_tool_activity(
            tool_name="update_note",
            tool_params={"note_id": "123"},
            tool_result={"success": True},
            status="completed"
        )

        assert activity["label"] == "✏️ Mise à jour note"
        assert activity["summary"] == "Note mise à jour"


class TestConversationStorageFilter:
    """Tests pour ConversationStorageFilter class"""

    def test_should_create_note_when_create_note_tool_used(self):
        """Test création note quand tool create_note utilisé"""
        data = {
            "user_input": "Recherche projet X",
            "tools_used": ["search_knowledge", "create_note"]
        }

        assert ConversationStorageFilter.should_create_archive_note(data) is True

    def test_should_create_note_when_explicit_user_request(self):
        """Test création note quand user demande explicitement"""
        data = {
            "user_input": "Crée une note avec ces infos",
            "tools_used": ["search_knowledge"]
        }

        assert ConversationStorageFilter.should_create_archive_note(data) is True

    def test_should_not_create_note_for_casual_chat(self):
        """Test pas de création note pour chat casual"""
        data = {
            "user_input": "Salut, comment ça va ?",
            "tools_used": []
        }

        assert ConversationStorageFilter.should_create_archive_note(data) is False

    def test_should_not_create_note_for_search_only(self):
        """Test pas de création note pour simple recherche"""
        data = {
            "user_input": "Recherche projet X",
            "tools_used": ["search_knowledge"]  # Pas de create_note
        }

        assert ConversationStorageFilter.should_create_archive_note(data) is False

    def test_archive_keywords_variations(self):
        """Test différentes variations mots-clés archivage"""
        variations = [
            "crée une note",
            "créer une note",
            "archive cette info",
            "sauvegarde ça"
        ]

        for variation in variations:
            data = {
                "user_input": variation,
                "tools_used": []
            }
            assert ConversationStorageFilter.should_create_archive_note(data) is True


class TestConvenienceFunctions:
    """Tests pour fonctions convenience"""

    def test_filter_for_ui(self):
        """Test fonction convenience filter_for_ui"""
        result = filter_for_ui("plume", "Reasoning: test. Réponse finale.")

        assert "Reasoning:" not in result["content"]
        assert "Réponse finale" in result["content"]

    def test_filter_tool_for_ui(self):
        """Test fonction convenience filter_tool_for_ui"""
        result = filter_tool_for_ui(
            "search_knowledge",
            {"query": "test"},
            {"results_count": 5},
            "completed"
        )

        assert result["label"] == "🔍 Recherche archives"
        assert "5 résultat" in result["summary"]

    def test_should_create_archive_note_function(self):
        """Test fonction convenience should_create_archive_note"""
        data = {"user_input": "test", "tools_used": ["create_note"]}

        assert should_create_archive_note(data) is True


# Run tests with pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
