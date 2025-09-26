#!/usr/bin/env python3
"""
SCRIBE - Plume & Mimir System Launcher
Entry point for running agents and development tools
"""

import sys
import os
import argparse
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def main():
    parser = argparse.ArgumentParser(description="SCRIBE - Système Plume & Mimir")
    parser.add_argument('command', choices=['dev', 'build', 'test', 'deploy', 'agent'],
                       help='Command to execute')
    parser.add_argument('--agent', choices=['leo', 'koda', 'gito', 'plume', 'mimir'],
                       help='Specific agent to run')
    parser.add_argument('--task', type=str, help='Task description for agent')
    parser.add_argument('--env', choices=['dev', 'staging', 'prod'], default='dev',
                       help='Environment to use')

    args = parser.parse_args()

    print("🚀 SCRIBE - Système Plume & Mimir")
    print("=" * 50)

    if args.command == 'dev':
        print("🔧 Mode développement")
        print("\nCommandes disponibles :")
        print("  Backend:  cd backend && uvicorn main:app --reload")
        print("  Frontend: cd frontend && npm run dev")
        print("  Database: cd database && python test_connection.py")
        print("  Docker:   docker-compose up")

    elif args.command == 'build':
        print("🏗️ Mode build")
        if args.agent:
            print(f"Activation agent {args.agent.upper()}")
            run_agent(args.agent, args.task)
        else:
            print("Spécifiez un agent avec --agent")

    elif args.command == 'test':
        print("🧪 Mode test")
        run_tests()

    elif args.command == 'deploy':
        print("🚀 Mode déploiement")
        run_deployment(args.env)

    elif args.command == 'agent':
        if args.agent:
            run_agent(args.agent, args.task)
        else:
            print("Spécifiez un agent avec --agent")

def run_agent(agent_name, task=None):
    """Run a specific agent"""
    try:
        from TOOLS.forge import AgentForge

        forge = AgentForge()

        print(f"🤖 Activation agent {agent_name.upper()}")

        if task:
            print(f"📋 Tâche: {task}")
            # Here you would integrate with Claude Code to run the agent
            result = forge.launch_agent(agent_name, task)
            print(f"✅ Résultat: {result}")
        else:
            print(f"Agent {agent_name} prêt. Spécifiez une tâche avec --task")

    except ImportError as e:
        print(f"❌ Erreur import: {e}")
        print("Assurez-vous que les dépendances sont installées")
    except Exception as e:
        print(f"❌ Erreur agent: {e}")

def run_tests():
    """Run test suite"""
    print("Exécution des tests...")

    tests = [
        ("Database", "cd database && python test_connection.py"),
        ("Backend", "cd backend && python -m pytest tests/"),
        ("Frontend", "cd frontend && npm test"),
    ]

    for test_name, command in tests:
        print(f"\n🔍 Test {test_name}")
        print(f"Commande: {command}")

def run_deployment(env):
    """Run deployment process"""
    print(f"Déploiement environnement: {env}")

    if env == 'prod':
        print("⚠️  Déploiement PRODUCTION")
        print("1. Tests complets")
        print("2. Build optimisé")
        print("3. Configuration Render/Vercel")
        print("4. Variables environnement")
        print("5. Monitoring activation")
    else:
        print(f"Déploiement {env}")

if __name__ == "__main__":
    main()