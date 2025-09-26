#!/usr/bin/env python3
"""
Forge - Lanceur d'agents Claude Code connectés
Crée des sessions autonomes avec contexte et mission
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
import json
from datetime import datetime


class Forge:
    """
    Outil de création de sessions d'agents Claude Code connectés
    """

    def __init__(self, tools_dir: Optional[str] = None):
        self.tools_dir = Path(tools_dir or Path(__file__).parent)
        self.templates_dir = self.tools_dir / "templates"
        self.sessions_dir = self.tools_dir / "sessions"

        # Créer dossiers nécessaires
        self.templates_dir.mkdir(exist_ok=True)
        self.sessions_dir.mkdir(exist_ok=True)

        self.agents_dir = self.tools_dir.parent / "AGENTS"

    def load_agent_spec(self, agent_name: str) -> Dict[str, Any]:
        """Charge les spécifications d'un agent depuis AGENTS/"""
        agent_dir = self.agents_dir / agent_name.title()
        agent_file = agent_dir / f"{agent_name.lower()}.json"
        claude_md = agent_dir / "CLAUDE.md"

        spec = {"name": agent_name, "persona": "", "capabilities": []}

        # Charger JSON si existe
        if agent_file.exists():
            with open(agent_file, 'r', encoding='utf-8') as f:
                agent_data = json.load(f)
                spec.update({
                    "description": agent_data.get("description", ""),
                    "purpose": agent_data.get("purpose", ""),
                    "personality": agent_data.get("personality", ""),
                    "capabilities": [cap.get("name", "") for cap in agent_data.get("capabilities", [])],
                    "constraints": agent_data.get("constraints", [])
                })

        # Charger CLAUDE.md si existe
        if claude_md.exists():
            spec["claude_context"] = claude_md.read_text(encoding='utf-8')

        return spec

    def load_context_files(self, context_paths: List[str]) -> str:
        """Charge fichiers de contexte depuis chemins glob"""
        context_content = ""

        for path_pattern in context_paths:
            if "*" in path_pattern:
                # Glob pattern
                base_path = Path(path_pattern.split("*")[0])
                if base_path.exists():
                    for file_path in base_path.rglob("*"):
                        if file_path.is_file():
                            try:
                                content = file_path.read_text(encoding='utf-8')
                                context_content += f"\n=== {file_path.name} ===\n{content}\n"
                            except Exception as e:
                                print(f"⚠️ Erreur lecture {file_path}: {e}")
            else:
                # Chemin direct
                file_path = Path(path_pattern)
                if file_path.exists():
                    content = file_path.read_text(encoding='utf-8')
                    context_content += f"\n=== {file_path.name} ===\n{content}\n"

        return context_content

    def create_mission_prompt(self, agent_spec: Dict[str, Any], mission: str, context: str) -> str:
        """Génère le prompt de mission pour l'agent"""

        prompt = f"""# 🤖 Agent {agent_spec['name']} - Session Claude Code

## Persona et Configuration
**Tu es {agent_spec['name']}** - {agent_spec.get('description', 'Agent spécialisé')}

**Mission principale :** {agent_spec.get('purpose', 'Accomplir les tâches assignées')}
**Personnalité :** {agent_spec.get('personality', 'Professionnel et efficace')}

### Capacités disponibles
{chr(10).join([f"- {cap}" for cap in agent_spec.get('capabilities', [])])}

### Contraintes
{chr(10).join([f"- {constraint}" for constraint in agent_spec.get('constraints', [])])}

## Contexte Mission
{context}

## Mission Spécifique
{mission}

## Instructions Claude Code
Tu as accès à tous les outils Claude Code standard (Read, Write, Edit, Bash, Glob, Grep, etc.).
Utilise ces outils pour accomplir ta mission de manière autonome.

**IMPORTANT :** Tu opères en tant qu'agent {agent_spec['name']} avec sa personnalité et ses contraintes.

{'## Configuration Agent' + chr(10) + agent_spec.get('claude_context', '') if agent_spec.get('claude_context') else ''}

---
> Session générée par la Forge EMPYR - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        return prompt

    def create_session(self, agent_name: str, mission: str, context_paths: List[str]) -> str:
        """Crée une session d'agent Claude Code"""

        print(f"🏗️ Forge - Création session {agent_name}")

        # 1. Charger spécifications agent
        print(f"📋 Chargement agent {agent_name}...")
        agent_spec = self.load_agent_spec(agent_name)

        # 2. Charger contexte
        print(f"📁 Chargement contexte depuis {len(context_paths)} sources...")
        context_content = self.load_context_files(context_paths)

        # 3. Créer dossier session
        session_name = f"{agent_name.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        session_dir = self.sessions_dir / session_name
        session_dir.mkdir(exist_ok=True)

        # 4. Générer prompt mission
        mission_prompt = self.create_mission_prompt(agent_spec, mission, context_content)

        # 5. Sauvegarder session
        (session_dir / "mission_prompt.md").write_text(mission_prompt, encoding='utf-8')
        (session_dir / "context.txt").write_text(context_content, encoding='utf-8')

        session_config = {
            "agent_name": agent_name,
            "mission": mission,
            "context_paths": context_paths,
            "created_at": datetime.now().isoformat(),
            "session_dir": str(session_dir)
        }

        (session_dir / "session_config.json").write_text(
            json.dumps(session_config, indent=2), encoding='utf-8'
        )

        print(f"✅ Session créée: {session_dir}")
        print(f"📄 Prompt: {session_dir / 'mission_prompt.md'}")

        return str(session_dir)

    def launch_claude_session(self, session_dir: str) -> None:
        """Lance une nouvelle session Claude Code avec le prompt"""
        session_path = Path(session_dir)
        prompt_file = session_path / "mission_prompt.md"

        if not prompt_file.exists():
            print(f"❌ Prompt non trouvé: {prompt_file}")
            return

        prompt_content = prompt_file.read_text(encoding='utf-8')

        print(f"🚀 Lancement session Claude Code...")
        print(f"📍 Dossier: {session_path}")
        print(f"📝 Prompt: {len(prompt_content)} caractères")

        # TODO: Intégration avec CLI Claude Code
        print(f"\n🔧 MANUEL - Copiez ce prompt dans une nouvelle session Claude Code:")
        print(f"=" * 80)
        print(prompt_content)
        print(f"=" * 80)

    def list_sessions(self) -> List[Dict[str, Any]]:
        """Liste les sessions actives"""
        sessions = []

        for session_dir in self.sessions_dir.glob("*"):
            if session_dir.is_dir():
                config_file = session_dir / "session_config.json"
                if config_file.exists():
                    config = json.loads(config_file.read_text())
                    sessions.append(config)

        return sessions


def main():
    parser = argparse.ArgumentParser(description="Forge - Lanceur d'agents Claude Code")
    subparsers = parser.add_subparsers(dest='command', help='Commandes disponibles')

    # Commande create
    create_parser = subparsers.add_parser('create', help='Créer une session agent')
    create_parser.add_argument('agent_name', help='Nom de l\'agent (ex: leo)')
    create_parser.add_argument('--mission', '-m', required=True, help='Mission à accomplir')
    create_parser.add_argument('--context', '-c', action='append',
                              help='Chemins contexte (support glob)', default=[])
    create_parser.add_argument('--launch', '-l', action='store_true',
                              help='Lancer automatiquement la session')

    # Commande list
    list_parser = subparsers.add_parser('list', help='Lister les sessions')

    # Commande launch
    launch_parser = subparsers.add_parser('launch', help='Lancer une session existante')
    launch_parser.add_argument('session_dir', help='Dossier de la session')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    forge = Forge()

    if args.command == 'create':
        session_dir = forge.create_session(
            args.agent_name,
            args.mission,
            args.context or []
        )

        if args.launch:
            forge.launch_claude_session(session_dir)

    elif args.command == 'list':
        sessions = forge.list_sessions()
        print(f"\n📋 Sessions actives ({len(sessions)}):")
        for session in sessions:
            print(f"  🤖 {session['agent_name']} - {session['created_at']}")
            print(f"     📁 {session['session_dir']}")
            print(f"     🎯 {session['mission'][:80]}...")
            print()

    elif args.command == 'launch':
        forge.launch_claude_session(args.session_dir)


if __name__ == "__main__":
    main()