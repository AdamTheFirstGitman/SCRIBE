#!/usr/bin/env python3
"""
Gito - Interface Leo vers MCP Git
Agent spécialisé gestion Git via MCP
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../tools/mcp'))
from gito_mcp import MCPGitTool

from dataclasses import dataclass
from typing import Dict, Any, List, Optional

@dataclass
class GitTask:
    """Spécification tâche Git de Leo"""
    task_id: str
    operation: str  # status, commit, merge, branch
    description: str
    parameters: Dict[str, Any]

class Gito:
    """Agent Gito utilisant MCP Git pour Leo"""

    def __init__(self):
        self.name = "Gito"
        self.description = "Agent Gito spécialisé avec MCP integration"
        self.capabilities = [
            "Repository Status",
            "Branch Management",
            "Commit Operations",
            "Merge Management"
        ]
        self.mcp_git = MCPGitTool()

    def execute_git_task(self, git_task: GitTask) -> Dict[str, Any]:
        """Exécute tâche Git délégée par Leo"""
        print(f"[{self.name}] Exécution Git: {git_task.operation}")

        # Dispatch selon opération
        if git_task.operation == "status":
            return self._handle_status(git_task)
        elif git_task.operation == "commit":
            return self._handle_commit(git_task)
        elif git_task.operation == "branch":
            return self._handle_branch(git_task)
        elif git_task.operation == "merge":
            return self._handle_merge(git_task)
        else:
            return {
                "task_id": git_task.task_id,
                "success": False,
                "error": f"Unknown Git operation: {git_task.operation}",
                "agent": self.name
            }

    def _handle_status(self, task: GitTask) -> Dict[str, Any]:
        """Gère git status via MCP"""
        mcp_result = self.mcp_git.status()

        return {
            "task_id": task.task_id,
            "operation": "status",
            "success": mcp_result["success"],
            "repository_clean": mcp_result.get("clean", False),
            "changes_count": len(mcp_result.get("changes", [])),
            "changes": mcp_result.get("changes", []),
            "mcp_result": mcp_result,
            "agent": self.name
        }

    def _handle_commit(self, task: GitTask) -> Dict[str, Any]:
        """Gère git commit via MCP"""
        params = task.parameters
        message = params.get("message", "Auto commit by Git Agent")
        files = params.get("files", [])

        mcp_result = self.mcp_git.commit(message, files)

        return {
            "task_id": task.task_id,
            "operation": "commit",
            "success": mcp_result["success"],
            "commit_hash": mcp_result.get("commit_hash"),
            "message": message,
            "files_committed": len(files) if files else "all staged",
            "mcp_result": mcp_result,
            "agent": self.name
        }

    def _handle_branch(self, task: GitTask) -> Dict[str, Any]:
        """Gère opérations branch via MCP"""
        params = task.parameters
        action = params.get("action", "list")  # list, create, checkout, delete
        branch_name = params.get("branch_name")

        mcp_result = self.mcp_git.branch(action, branch_name)

        return {
            "task_id": task.task_id,
            "operation": "branch",
            "action": action,
            "success": mcp_result["success"],
            "branch_name": branch_name,
            "current_branch": mcp_result.get("current_branch"),
            "mcp_result": mcp_result,
            "agent": self.name
        }

    def _handle_merge(self, task: GitTask) -> Dict[str, Any]:
        """Gère git merge via MCP"""
        params = task.parameters
        branch_name = params.get("branch_name")

        if not branch_name:
            return {
                "task_id": task.task_id,
                "operation": "merge",
                "success": False,
                "error": "branch_name required for merge",
                "agent": self.name
            }

        mcp_result = self.mcp_git.merge(branch_name)

        return {
            "task_id": task.task_id,
            "operation": "merge",
            "success": mcp_result["success"],
            "merged_branch": branch_name,
            "has_conflicts": mcp_result.get("conflicts", False),
            "mcp_result": mcp_result,
            "agent": self.name
        }

    def repository_overview(self) -> Dict[str, Any]:
        """Vue d'ensemble du repository pour Leo"""
        print(f"[{self.name}] Analyse repository...")

        # Status
        status_result = self.mcp_git.status()

        # Current branch
        current_branch = self.mcp_git._get_current_branch()

        # Overview
        overview = {
            "agent": self.name,
            "repository_status": "clean" if status_result.get("clean") else "dirty",
            "current_branch": current_branch,
            "changes_count": len(status_result.get("changes", [])),
            "changes": status_result.get("changes", []),
            "capabilities": self.capabilities,
            "mcp_available": True
        }

        print(f"  📊 Status: {overview['repository_status']}")
        print(f"  🌿 Branch: {overview['current_branch']}")
        print(f"  📝 Changes: {overview['changes_count']}")

        return overview

    def execute(self, task_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Point d'entrée Leo → Git Agent"""
        if "overview" in task_spec.get("operation", ""):
            return self.repository_overview()

        # Conversion spec Leo → GitTask
        git_task = GitTask(
            task_id=task_spec.get("task_id", "GIT001"),
            operation=task_spec.get("operation", "status"),
            description=task_spec.get("description", "Git operation"),
            parameters=task_spec.get("parameters", {})
        )

        return self.execute_git_task(git_task)

    def __str__(self):
        return f"{self.name}: {self.description}"

def main():
    """Test Gito"""
    gito = Gito()

    print(f"=== Test {gito.name} ===")

    # Test overview
    overview = gito.repository_overview()
    print(f"\n📊 Overview:")
    print(f"  Repository: {overview['repository_status']}")
    print(f"  Branch: {overview['current_branch']}")

    # Test via execute interface
    print(f"\n🧪 Test execute interface:")
    task_spec = {
        "operation": "status",
        "task_id": "T001",
        "description": "Check repository status"
    }

    result = gito.execute(task_spec)
    print(f"  Success: {result['success']}")
    print(f"  Changes: {result['changes_count']}")

if __name__ == "__main__":
    main()