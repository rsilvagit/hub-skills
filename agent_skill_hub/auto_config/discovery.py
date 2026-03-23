from __future__ import annotations

import os
import shutil
from pathlib import Path
from dataclasses import dataclass


@dataclass
class AgentInfo:
    name: str
    installed: bool
    config_path: Path | None
    config_exists: bool
    already_configured: bool


def _home() -> Path:
    return Path.home()


def _appdata() -> Path:
    return Path(os.environ.get("APPDATA", _home() / "AppData" / "Roaming"))


def _detect_cursor() -> AgentInfo:
    # Cursor stores MCP config in ~/.cursor/mcp.json (global)
    config_path = _home() / ".cursor" / "mcp.json"
    installed = (
        shutil.which("cursor") is not None
        or (_home() / ".cursor").is_dir()
        or any(
            (Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "cursor").glob("Cursor*")
        ) if os.environ.get("LOCALAPPDATA") else False
    )
    configured = _check_configured(config_path)
    return AgentInfo(
        name="Cursor",
        installed=installed or config_path.parent.is_dir(),
        config_path=config_path,
        config_exists=config_path.exists(),
        already_configured=configured,
    )


def _detect_claude_desktop() -> AgentInfo:
    # Claude Desktop: %APPDATA%/Claude/claude_desktop_config.json
    config_path = _appdata() / "Claude" / "claude_desktop_config.json"
    installed = config_path.parent.is_dir()
    configured = _check_configured(config_path)
    return AgentInfo(
        name="Claude Desktop",
        installed=installed,
        config_path=config_path,
        config_exists=config_path.exists(),
        already_configured=configured,
    )


def _detect_vscode() -> AgentInfo:
    # VS Code: %APPDATA%/Code/User/settings.json
    config_path = _appdata() / "Code" / "User" / "settings.json"
    installed = shutil.which("code") is not None or config_path.parent.is_dir()
    # VS Code MCP is configured differently, check for mcp servers
    configured = _check_configured(config_path, key="mcp")
    return AgentInfo(
        name="VS Code",
        installed=installed,
        config_path=config_path,
        config_exists=config_path.exists(),
        already_configured=configured,
    )


def _detect_windsurf() -> AgentInfo:
    # Windsurf: ~/.codeium/windsurf/mcp_config.json
    config_path = _home() / ".codeium" / "windsurf" / "mcp_config.json"
    installed = (
        shutil.which("windsurf") is not None
        or (_home() / ".codeium" / "windsurf").is_dir()
    )
    configured = _check_configured(config_path)
    return AgentInfo(
        name="Windsurf",
        installed=installed,
        config_path=config_path,
        config_exists=config_path.exists(),
        already_configured=configured,
    )


def _check_configured(config_path: Path, key: str = "mcpServers") -> bool:
    if not config_path.exists():
        return False
    try:
        import json
        data = json.loads(config_path.read_text(encoding="utf-8"))
        # Check standard mcpServers key
        servers = data.get(key, {})
        if isinstance(servers, dict) and "agent-skill-hub" in servers:
            return True
        # Check VS Code nested mcp.servers structure
        mcp = data.get("mcp", {})
        if isinstance(mcp, dict):
            mcp_servers = mcp.get("servers", {})
            if isinstance(mcp_servers, dict) and "agent-skill-hub" in mcp_servers:
                return True
    except Exception:
        pass
    return False


def discover_agents() -> list[AgentInfo]:
    return [
        _detect_cursor(),
        _detect_claude_desktop(),
        _detect_vscode(),
        _detect_windsurf(),
    ]
