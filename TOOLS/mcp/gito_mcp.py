#!/usr/bin/env python3
"""
MCP Gito Tool - Interface pour Gito Agent
Wrapper sur MCP Git disponible dans Claude Code
"""

import subprocess
from typing import Dict, Any, List, Optional
import json

class MCPGitTool:
    """Interface MCP Git pour Gito EMPYR"""

    def __init__(self):
        self.name = "MCP Git Tool"
        self.available_commands = [
            "status", "add", "commit", "push", "pull",
            "branch", "checkout", "merge", "diff", "log"
        ]

    def status(self) -> Dict[str, Any]:
        """Git status via MCP"""
        try:
            # Simulation appel MCP Git
            # Dans vraie implémentation, appel MCP natif
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=True
            )

            # Parse output pour format standardisé
            changes = self._parse_status_output(result.stdout)

            return {
                "command": "status",
                "success": True,
                "changes": changes,
                "clean": len(changes) == 0,
                "raw_output": result.stdout
            }

        except subprocess.CalledProcessError as e:
            return {
                "command": "status",
                "success": False,
                "error": str(e),
                "message": "Git status failed"
            }

    def add(self, files: List[str]) -> Dict[str, Any]:
        """Git add via MCP"""
        try:
            cmd = ["git", "add"] + files
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            return {
                "command": "add",
                "success": True,
                "files_added": files,
                "message": f"Added {len(files)} files to staging"
            }

        except subprocess.CalledProcessError as e:
            return {
                "command": "add",
                "success": False,
                "error": str(e),
                "files": files
            }

    def commit(self, message: str, files: Optional[List[str]] = None) -> Dict[str, Any]:
        """Git commit via MCP"""
        try:
            cmd = ["git", "commit", "-m", message]
            if files:
                # Add files first
                self.add(files)

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            return {
                "command": "commit",
                "success": True,
                "message": message,
                "commit_hash": self._extract_commit_hash(result.stdout),
                "raw_output": result.stdout
            }

        except subprocess.CalledProcessError as e:
            return {
                "command": "commit",
                "success": False,
                "error": str(e),
                "message": message
            }

    def branch(self, action: str, branch_name: Optional[str] = None) -> Dict[str, Any]:
        """Git branch operations via MCP"""
        try:
            if action == "list":
                cmd = ["git", "branch"]
            elif action == "create" and branch_name:
                cmd = ["git", "branch", branch_name]
            elif action == "checkout" and branch_name:
                cmd = ["git", "checkout", branch_name]
            elif action == "delete" and branch_name:
                cmd = ["git", "branch", "-d", branch_name]
            else:
                raise ValueError(f"Invalid branch action: {action}")

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            return {
                "command": f"branch_{action}",
                "success": True,
                "branch_name": branch_name,
                "raw_output": result.stdout,
                "current_branch": self._get_current_branch()
            }

        except (subprocess.CalledProcessError, ValueError) as e:
            return {
                "command": f"branch_{action}",
                "success": False,
                "error": str(e),
                "branch_name": branch_name
            }

    def merge(self, branch_name: str) -> Dict[str, Any]:
        """Git merge via MCP"""
        try:
            cmd = ["git", "merge", branch_name]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            return {
                "command": "merge",
                "success": True,
                "merged_branch": branch_name,
                "conflicts": self._detect_conflicts(result.stdout),
                "raw_output": result.stdout
            }

        except subprocess.CalledProcessError as e:
            return {
                "command": "merge",
                "success": False,
                "error": str(e),
                "branch_name": branch_name,
                "conflicts": True
            }

    def _parse_status_output(self, output: str) -> List[Dict[str, str]]:
        """Parse git status porcelain output"""
        changes = []
        for line in output.strip().split('\n'):
            if line:
                status_code = line[:2]
                filename = line[3:]
                changes.append({
                    "file": filename,
                    "status": self._decode_status(status_code),
                    "code": status_code
                })
        return changes

    def _decode_status(self, code: str) -> str:
        """Decode git status codes"""
        status_map = {
            "M ": "modified",
            " M": "modified_unstaged",
            "A ": "added",
            "D ": "deleted",
            "??": "untracked",
            "R ": "renamed",
            "C ": "copied"
        }
        return status_map.get(code, "unknown")

    def _extract_commit_hash(self, output: str) -> Optional[str]:
        """Extract commit hash from commit output"""
        lines = output.strip().split('\n')
        for line in lines:
            if line.startswith('['):
                # Extract hash from line like "[main abc1234] commit message"
                parts = line.split(' ')
                if len(parts) >= 2:
                    return parts[1].rstrip(']')
        return None

    def _get_current_branch(self) -> Optional[str]:
        """Get current branch name"""
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None

    def _detect_conflicts(self, output: str) -> bool:
        """Detect merge conflicts in output"""
        conflict_indicators = ["CONFLICT", "Automatic merge failed", "fix conflicts"]
        return any(indicator in output for indicator in conflict_indicators)

    def execute_command(self, command: str, **kwargs) -> Dict[str, Any]:
        """Execute git command via MCP"""
        if command not in self.available_commands:
            return {
                "command": command,
                "success": False,
                "error": f"Command '{command}' not supported",
                "available": self.available_commands
            }

        if command == "status":
            return self.status()
        elif command == "add":
            return self.add(kwargs.get("files", []))
        elif command == "commit":
            return self.commit(kwargs.get("message", ""), kwargs.get("files"))
        elif command == "branch":
            return self.branch(kwargs.get("action", "list"), kwargs.get("branch_name"))
        elif command == "merge":
            return self.merge(kwargs.get("branch_name", ""))
        else:
            return {
                "command": command,
                "success": False,
                "error": f"Command '{command}' implementation missing"
            }

def main():
    """Test MCP Git Tool"""
    git_tool = MCPGitTool()

    print("=== Test MCP Git Tool ===")

    # Test status
    result = git_tool.status()
    print(f"Status: {result['success']}")
    if result['success']:
        print(f"  Changes: {len(result['changes'])}")
        print(f"  Clean: {result['clean']}")

if __name__ == "__main__":
    main()