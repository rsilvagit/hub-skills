from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from .discovery import AgentInfo, discover_agents

# Resolve paths for the MCP config
def _get_skills_dir() -> str:
    # Find skills dir relative to the package install
    candidate = Path.cwd() / "skills"
    if candidate.is_dir():
        return str(candidate.resolve())
    # Fallback: package location
    pkg_dir = Path(__file__).resolve().parent.parent.parent / "skills"
    return str(pkg_dir)


def _get_serve_command() -> list[str]:
    agent_skill_bin = shutil.which("agent-skill")
    if agent_skill_bin:
        return [agent_skill_bin, "serve"]
    return [sys.executable, "-m", "agent_skill_hub.cli.main", "serve"]


def _mcp_server_entry() -> dict:
    return {
        "command": _get_serve_command()[0],
        "args": _get_serve_command()[1:],
        "env": {},
    }


def _mcp_server_entry_url() -> dict:
    return {
        "url": "http://localhost:3100/mcp",
    }


def configure_agent(agent: AgentInfo, use_url: bool = False) -> tuple[bool, str]:
    """Configure a single agent. Returns (success, message)."""
    if not agent.installed:
        return False, f"{agent.name} not found"

    if agent.already_configured:
        return True, f"{agent.name} already configured"

    if agent.config_path is None:
        return False, f"{agent.name} config path unknown"

    config_path = agent.config_path

    # Read existing config or start fresh
    if config_path.exists():
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except Exception:
            data = {}
    else:
        data = {}

    # Determine config structure based on agent
    if agent.name == "VS Code":
        return _configure_vscode(config_path, data)
    else:
        return _configure_mcp_json(agent.name, config_path, data, use_url)


def _configure_mcp_json(
    name: str, config_path: Path, data: dict, use_url: bool
) -> tuple[bool, str]:
    """Configure agents that use mcpServers format (Cursor, Claude Desktop, Windsurf)."""
    if "mcpServers" not in data:
        data["mcpServers"] = {}

    entry = _mcp_server_entry_url() if use_url else _mcp_server_entry()
    data["mcpServers"]["agent-skill-hub"] = entry

    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Backup existing config
    if config_path.exists():
        backup = config_path.with_suffix(".json.bak")
        if not backup.exists():
            config_path.rename(backup)
            backup.rename(backup)  # just ensure it exists
            # Re-read since we renamed
            config_path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        else:
            config_path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
    else:
        config_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    return True, f"{name} configured at {config_path}"


def _configure_vscode(config_path: Path, data: dict) -> tuple[bool, str]:
    """Configure VS Code with MCP settings."""
    if "mcp" not in data:
        data["mcp"] = {}
    if "servers" not in data["mcp"]:
        data["mcp"]["servers"] = {}

    data["mcp"]["servers"]["agent-skill-hub"] = {
        "type": "http",
        "url": "http://localhost:3100/mcp",
    }

    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Backup
    if config_path.exists():
        backup = config_path.with_suffix(".json.bak")
        if not backup.exists():
            import shutil as sh
            sh.copy2(config_path, backup)

    config_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return True, f"VS Code configured at {config_path}"


def configure_all(use_url: bool = False) -> list[tuple[AgentInfo, bool, str]]:
    """Discover and configure all found agents."""
    agents = discover_agents()
    results = []
    for agent in agents:
        if agent.installed:
            success, msg = configure_agent(agent, use_url=use_url)
            results.append((agent, success, msg))
    return results
