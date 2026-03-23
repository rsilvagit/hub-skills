from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

STARTUP_NAME = "agent-skill-hub"


def _get_startup_dir() -> Path:
    """Windows Startup folder."""
    appdata = os.environ.get("APPDATA", "")
    return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def _get_bat_content() -> str:
    agent_skill_bin = shutil.which("agent-skill")
    if agent_skill_bin:
        cmd = f'"{agent_skill_bin}" serve'
    else:
        cmd = f'"{sys.executable}" -m agent_skill_hub.cli.main serve'

    return f"""@echo off
title Agent Skill Hub - MCP Server
{cmd}
"""


def _get_vbs_content(bat_path: Path) -> str:
    """VBScript to run the bat file hidden (no console window)."""
    return f"""Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & "{bat_path}" & chr(34), 0
Set WshShell = Nothing
"""


def register_startup(silent: bool = True) -> tuple[bool, str]:
    """Register agent-skill serve to run at Windows startup."""
    startup_dir = _get_startup_dir()
    if not startup_dir.is_dir():
        return False, f"Startup folder not found: {startup_dir}"

    bat_path = startup_dir / f"{STARTUP_NAME}.bat"
    bat_path.write_text(_get_bat_content(), encoding="utf-8")

    if silent:
        # Use VBScript to hide console window
        vbs_path = startup_dir / f"{STARTUP_NAME}.vbs"
        vbs_path.write_text(_get_vbs_content(bat_path), encoding="utf-8")
        return True, f"Registered silent startup at {vbs_path}"

    return True, f"Registered startup at {bat_path}"


def unregister_startup() -> tuple[bool, str]:
    """Remove agent-skill from Windows startup."""
    startup_dir = _get_startup_dir()
    removed = []

    for ext in (".bat", ".vbs"):
        path = startup_dir / f"{STARTUP_NAME}{ext}"
        if path.exists():
            path.unlink()
            removed.append(str(path))

    if removed:
        return True, f"Removed: {', '.join(removed)}"
    return False, "Not registered in startup"


def is_registered() -> bool:
    """Check if agent-skill is registered in startup."""
    startup_dir = _get_startup_dir()
    return (
        (startup_dir / f"{STARTUP_NAME}.bat").exists()
        or (startup_dir / f"{STARTUP_NAME}.vbs").exists()
    )
