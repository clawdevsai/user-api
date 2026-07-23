#!/usr/bin/env python3
"""
Fetch agent prompt from academy repo and create local agent.
Usage:
  python fetch_and_create_agent.py <agent-name> [--output-dir=.claude/agents]
  python fetch_and_create_agent.py list
"""

import subprocess
import json
import sys
import os
from pathlib import Path
from typing import Optional


ACADEMY_REPO = "clawdevsai/academy"
PROMPTS_PATH = "prompts"
AGENT_TEMPLATE = """---
name: {name}
description: {description}
tools: {tools}
---

{content}
"""


def run_cmd(cmd: list[str]) -> str:
    """Execute shell command, return stdout."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{e.stderr}")
    except FileNotFoundError:
        raise RuntimeError(f"Command not found: {cmd[0]}. Install 'gh' CLI first.")


def list_available_agents() -> list[str]:
    """List all agent prompts in academy/prompts."""
    try:
        # Use gh api to list files
        response = run_cmd([
            "gh", "api",
            f"repos/{ACADEMY_REPO}/contents/{PROMPTS_PATH}",
            "--jq", ".[].name"
        ])
        files = response.split("\n")
        agents = [f.replace("criar-agente-", "").replace(".md", "") for f in files if f.endswith(".md")]
        return sorted(agents)
    except Exception as e:
        print(f"Error listing agents: {e}", file=sys.stderr)
        return []


def find_agent(query: str) -> Optional[str]:
    """Find agent prompt matching query (exact or substring)."""
    agents = list_available_agents()

    # Exact match
    if query in agents:
        return query

    # Substring match (case-insensitive)
    query_lower = query.lower()
    matches = [a for a in agents if query_lower in a.lower()]

    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        print(f"Multiple matches for '{query}':", file=sys.stderr)
        for m in matches:
            print(f"  - {m}", file=sys.stderr)
        sys.exit(1)

    return None


def fetch_agent_content(agent_name: str) -> str:
    """Fetch agent prompt from academy repo."""
    filename = f"criar-agente-{agent_name}.md"

    try:
        # Use gh api to get content (base64 encoded)
        response = run_cmd([
            "gh", "api",
            f"repos/{ACADEMY_REPO}/contents/{PROMPTS_PATH}/{filename}",
            "--jq", ".content"
        ])

        # Decode base64
        import base64
        content = base64.b64decode(response).decode("utf-8")
        return content
    except RuntimeError as e:
        raise RuntimeError(f"Failed to fetch {filename}: {e}")


def create_local_agent(agent_name: str, content: str, output_dir: str = ".claude/agents") -> Path:
    """Create agent file in local .claude/agents directory."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    agent_file = output_path / f"{agent_name}.md"

    # Check if exists
    if agent_file.exists():
        print(f"Warning: {agent_file} already exists", file=sys.stderr)
        # User will handle overwrite decision

    agent_file.write_text(content, encoding="utf-8")
    return agent_file


def main():
    if len(sys.argv) < 2:
        print("Usage: fetch_and_create_agent.py <agent-name> | list", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]

    if command == "list":
        agents = list_available_agents()
        for agent in agents:
            print(agent)
        sys.exit(0)

    agent_name = command
    output_dir = ".claude/agents"
    if len(sys.argv) > 2:
        for arg in sys.argv[2:]:
            if arg.startswith("--output-dir="):
                output_dir = arg.split("=", 1)[1]

    # Find matching agent
    print(f"Searching for agent: {agent_name}...", file=sys.stderr)
    found = find_agent(agent_name)

    if not found:
        print(f"Agent not found: {agent_name}", file=sys.stderr)
        print("Available agents:", file=sys.stderr)
        for a in list_available_agents():
            print(f"  - {a}", file=sys.stderr)
        sys.exit(1)

    print(f"Found: {found}", file=sys.stderr)

    # Fetch content
    print(f"Fetching prompt from academy/prompts/criar-agente-{found}.md...", file=sys.stderr)
    content = fetch_agent_content(found)

    # Create local agent
    print(f"Creating agent in {output_dir}/{found}.md...", file=sys.stderr)
    agent_file = create_local_agent(found, content, output_dir)

    print(f"✓ Agent created: {agent_file}", file=sys.stderr)
    print(agent_file)


if __name__ == "__main__":
    main()
