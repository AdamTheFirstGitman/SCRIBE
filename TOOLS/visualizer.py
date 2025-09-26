#!/usr/bin/env python3
"""
Visualizer - Outil de visualisation holographique d'architecture
Génère des diagrammes Mermaid avec affichage futuriste translucide
"""

import json
import tempfile
import webbrowser
import threading
import http.server
import socketserver
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class ArchNode:
    """Nœud d'architecture"""
    id: str
    label: str
    type: str  # "agent", "task", "tool", "data", "process"
    properties: Dict[str, Any]
    position: Optional[Dict[str, float]] = None


@dataclass
class ArchEdge:
    """Lien d'architecture"""
    source: str
    target: str
    label: str
    type: str  # "delegates", "uses", "produces", "depends"
    properties: Dict[str, Any]


class ArchitectureVisualizer:
    """
    Visualiseur d'architecture avec rendu holographique
    """

    def __init__(self):
        self.nodes: Dict[str, ArchNode] = {}
        self.edges: List[ArchEdge] = []
        self.metadata = {
            "title": "Architecture EMPYR",
            "created_at": datetime.now().isoformat(),
            "theme": "hologram"
        }

    def add_node(self, node_id: str, label: str, node_type: str,
                 properties: Optional[Dict[str, Any]] = None) -> ArchNode:
        """Ajoute un nœud à l'architecture"""
        node = ArchNode(
            id=node_id,
            label=label,
            type=node_type,
            properties=properties or {}
        )
        self.nodes[node_id] = node
        return node

    def add_edge(self, source: str, target: str, label: str, edge_type: str,
                 properties: Optional[Dict[str, Any]] = None) -> ArchEdge:
        """Ajoute une liaison à l'architecture"""
        edge = ArchEdge(
            source=source,
            target=target,
            label=label,
            type=edge_type,
            properties=properties or {}
        )
        self.edges.append(edge)
        return edge

    def remove_node(self, node_id: str) -> bool:
        """Supprime un nœud et ses liaisons"""
        if node_id not in self.nodes:
            return False

        # Supprimer le nœud
        del self.nodes[node_id]

        # Supprimer les liaisons associées
        self.edges = [e for e in self.edges
                     if e.source != node_id and e.target != node_id]

        return True

    def get_node_style(self, node_type: str) -> str:
        """Retourne le style CSS Mermaid pour un type de nœud"""
        styles = {
            "agent": "fill:#00ffff,stroke:#0099cc,stroke-width:2px,color:#000",
            "task": "fill:#9966ff,stroke:#6633cc,stroke-width:2px,color:#fff",
            "tool": "fill:#ff6600,stroke:#cc5500,stroke-width:2px,color:#fff",
            "data": "fill:#00cc99,stroke:#009966,stroke-width:2px,color:#000",
            "process": "fill:#ffcc00,stroke:#cc9900,stroke-width:2px,color:#000"
        }
        return styles.get(node_type, "fill:#333,stroke:#666,stroke-width:1px,color:#fff")

    def generate_mermaid(self) -> str:
        """Génère le code Mermaid de l'architecture"""

        # En-tête du graphique
        mermaid_code = f"""graph TD
    %% {self.metadata['title']}
    %% Généré le {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

"""

        # Ajouter les nœuds
        for node in self.nodes.values():
            # Formatage sécurisé du label
            safe_label = node.label.replace('"', '\\"').replace('\n', ' ')
            mermaid_code += f'    {node.id}["{safe_label}"]\n'

        mermaid_code += "\n"

        # Ajouter les liaisons
        for edge in self.edges:
            arrow_type = self._get_arrow_type(edge.type)
            safe_label = edge.label.replace('"', '\\"')
            mermaid_code += f'    {edge.source} {arrow_type}|"{safe_label}"| {edge.target}\n'

        mermaid_code += "\n"

        # Ajouter les styles
        for node in self.nodes.values():
            style = self.get_node_style(node.type)
            mermaid_code += f'    classDef {node.type}Style {style}\n'

        # Appliquer les styles aux nœuds
        for node_type in set(node.type for node in self.nodes.values()):
            nodes_of_type = [node.id for node in self.nodes.values() if node.type == node_type]
            if nodes_of_type:
                mermaid_code += f'    class {",".join(nodes_of_type)} {node_type}Style\n'

        return mermaid_code

    def _get_arrow_type(self, edge_type: str) -> str:
        """Retourne le type de flèche Mermaid selon le type de liaison"""
        arrows = {
            "delegates": "-->",
            "uses": "-.->",
            "produces": "==>",
            "depends": "o--o"
        }
        return arrows.get(edge_type, "-->")

    def generate_html_hologram(self, mermaid_code: str) -> str:
        """Génère le HTML avec style holographique"""

        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EMPYR Architecture Hologram</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Consolas', 'Monaco', monospace;
            background: transparent;
            min-height: 100vh;
            overflow: hidden;
            margin: 0;
            padding: 0;
        }}

        .hologram-container {{
            position: fixed;
            bottom: 20px;
            left: 20px;
            width: 50vw;
            height: 33vh;
            z-index: 9999;
            background: rgba(0, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(0, 255, 255, 0.3);
            border-radius: 15px;
            padding: 20px;
            box-shadow:
                0 0 50px rgba(0, 255, 255, 0.2),
                inset 0 0 30px rgba(0, 255, 255, 0.05);
            opacity: 0.85;
            animation: hologramPulse 3s ease-in-out infinite alternate;
        }}

        .hologram-header {{
            color: #00ffff;
            font-size: 14px;
            font-weight: bold;
            text-align: center;
            margin-bottom: 15px;
            text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
            letter-spacing: 1px;
        }}

        .mermaid-container {{
            width: 100%;
            height: calc(100% - 40px);
            overflow: auto;
            border-radius: 10px;
        }}

        .mermaid {{
            background: transparent !important;
        }}

        /* Styles Mermaid personnalisés */
        .mermaid .node rect,
        .mermaid .node circle,
        .mermaid .node polygon {{
            filter: drop-shadow(0 0 8px rgba(0, 255, 255, 0.4));
        }}

        .mermaid .edgePath path {{
            stroke: #00ffff !important;
            stroke-width: 2px !important;
            filter: drop-shadow(0 0 5px rgba(0, 255, 255, 0.6));
        }}

        .mermaid .edgeLabel {{
            background: rgba(0, 0, 0, 0.7) !important;
            color: #00ffff !important;
            font-size: 11px !important;
            border-radius: 5px !important;
        }}

        @keyframes hologramPulse {{
            0% {{
                box-shadow:
                    0 0 30px rgba(0, 255, 255, 0.2),
                    inset 0 0 20px rgba(0, 255, 255, 0.05);
            }}
            100% {{
                box-shadow:
                    0 0 60px rgba(0, 255, 255, 0.4),
                    inset 0 0 40px rgba(0, 255, 255, 0.1);
            }}
        }}

        /* Scrollbar personnalisée */
        .mermaid-container::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}

        .mermaid-container::-webkit-scrollbar-track {{
            background: rgba(0, 255, 255, 0.1);
            border-radius: 4px;
        }}

        .mermaid-container::-webkit-scrollbar-thumb {{
            background: rgba(0, 255, 255, 0.4);
            border-radius: 4px;
        }}

        .mermaid-container::-webkit-scrollbar-thumb:hover {{
            background: rgba(0, 255, 255, 0.6);
        }}
    </style>
</head>
<body>
    <div class="hologram-container">
        <div class="hologram-header">
            🧠 LEO ARCHITECTURE HOLOGRAM
        </div>
        <div class="mermaid-container">
            <div class="mermaid">
{mermaid_code}
            </div>
        </div>
    </div>

    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'dark',
            themeVariables: {{
                primaryColor: '#00ffff',
                primaryTextColor: '#ffffff',
                primaryBorderColor: '#0099cc',
                lineColor: '#00ffff',
                sectionBkgColor: 'rgba(0, 255, 255, 0.1)',
                altSectionBkgColor: 'rgba(0, 255, 255, 0.05)',
                gridColor: 'rgba(0, 255, 255, 0.2)',
                tertiaryColor: 'rgba(153, 102, 255, 0.2)'
            }}
        }});

        // Refresh automatique toutes les 5 secondes
        setTimeout(() => {{
            location.reload();
        }}, 5000);
    </script>
</body>
</html>"""
        return html_content

    def show_hologram(self, auto_refresh: bool = True, use_local_server: bool = True) -> str:
        """Affiche l'architecture en mode hologramme"""

        mermaid_code = self.generate_mermaid()
        html_content = self.generate_html_hologram(mermaid_code)

        if use_local_server:
            # Serveur local pour rester dans le même bureau
            return self._serve_hologram_locally(html_content)
        else:
            # Méthode originale (fichier temporaire)
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                f.write(html_content)
                temp_file = f.name

            file_url = f'file://{temp_file}'
            webbrowser.open(file_url)
            print(f"🌌 Hologramme architectural affiché: {file_url}")
            return temp_file

    def _serve_hologram_locally(self, html_content: str) -> str:
        """Affichage hologramme simple et direct"""
        import subprocess
        import tempfile

        # Créer fichier HTML temporaire
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html_content)
            temp_file = f.name

        # Ouvrir directement sans changer de focus
        subprocess.run(['open', temp_file], check=False)
        print(f"🌌 Hologramme Leo activé!")

        return temp_file

    def save_architecture(self, filename: str) -> str:
        """Sauvegarde l'architecture actuelle"""
        arch_data = {
            "metadata": self.metadata,
            "nodes": {node_id: asdict(node) for node_id, node in self.nodes.items()},
            "edges": [asdict(edge) for edge in self.edges]
        }

        file_path = Path(filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(arch_data, f, indent=2, ensure_ascii=False)

        return str(file_path)

    def load_architecture(self, filename: str) -> bool:
        """Charge une architecture sauvegardée"""
        try:
            file_path = Path(filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                arch_data = json.load(f)

            self.metadata = arch_data.get("metadata", {})

            # Charger nœuds
            self.nodes = {}
            for node_id, node_data in arch_data.get("nodes", {}).items():
                self.nodes[node_id] = ArchNode(**node_data)

            # Charger liaisons
            self.edges = []
            for edge_data in arch_data.get("edges", []):
                self.edges.append(ArchEdge(**edge_data))

            return True
        except Exception as e:
            print(f"❌ Erreur chargement architecture: {e}")
            return False

    def clear_architecture(self):
        """Efface l'architecture actuelle"""
        self.nodes.clear()
        self.edges.clear()
        self.metadata["updated_at"] = datetime.now().isoformat()

    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de l'architecture"""
        node_types = {}
        for node in self.nodes.values():
            node_types[node.type] = node_types.get(node.type, 0) + 1

        edge_types = {}
        for edge in self.edges:
            edge_types[edge.type] = edge_types.get(edge.type, 0) + 1

        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "node_types": node_types,
            "edge_types": edge_types,
            "metadata": self.metadata
        }


def demo_architecture():
    """Démonstration du visualiseur"""
    viz = ArchitectureVisualizer()

    # Créer architecture exemple
    viz.add_node("leo", "Leo\\nArchitecte", "agent", {"role": "architect"})
    viz.add_node("koda", "Koda\\nDeveloper", "agent", {"role": "developer"})
    viz.add_node("golem", "Golem\\nCreator", "tool", {"type": "creator"})
    viz.add_node("task1", "Build\\nPLUME", "task", {"priority": "high"})
    viz.add_node("task2", "Build\\nMIMIR", "task", {"priority": "high"})

    viz.add_edge("leo", "task1", "decomposes", "delegates")
    viz.add_edge("leo", "task2", "decomposes", "delegates")
    viz.add_edge("leo", "koda", "delegates to", "delegates")
    viz.add_edge("leo", "golem", "uses", "uses")
    viz.add_edge("koda", "task1", "implements", "produces")
    viz.add_edge("koda", "task2", "implements", "produces")

    # Afficher hologramme
    viz.show_hologram()

    # Stats
    stats = viz.get_stats()
    print(f"📊 Architecture stats: {stats}")


if __name__ == "__main__":
    demo_architecture()