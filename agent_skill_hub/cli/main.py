from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from agent_skill_hub.core import load_skills, run_skill
from agent_skill_hub.mcp_server import create_mcp_server
from agent_skill_hub.auto_config import discover_agents, configure_all, configure_agent
from agent_skill_hub.auto_config.startup import register_startup, unregister_startup, is_registered


def get_skills_dir() -> str:
    return str(Path.cwd() / "skills")


def cmd_list(args: argparse.Namespace) -> None:
    skills = load_skills(get_skills_dir())
    if not skills:
        print(f"No skills found in {get_skills_dir()}")
        return
    print(f"\nFound {len(skills)} skill(s):\n")
    for name, skill in skills.items():
        print(f"  {name} — {skill.description} [{skill.execution.type}]")
    print()


def cmd_run(args: argparse.Namespace) -> None:
    skills = load_skills(get_skills_dir())
    skill = skills.get(args.skill_name)
    if not skill:
        print(f'Skill "{args.skill_name}" not found')
        sys.exit(1)
    input_data = json.loads(args.input) if args.input else {}
    result = asyncio.run(run_skill(skill, input_data))
    print(json.dumps(result.model_dump(), indent=2))


def cmd_serve(args: argparse.Namespace) -> None:
    server = create_mcp_server(get_skills_dir(), port=args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[mcp] Shutting down...")
        server.shutdown()


def cmd_setup(args: argparse.Namespace) -> None:
    print("\n[setup] Agent Skill Hub — Auto Setup\n")

    # Step 1: Discover agents
    print("[1/3] Detecting AI agents...\n")
    agents = discover_agents()
    found = [a for a in agents if a.installed]

    if not found:
        print("  No supported agents found.")
        print("  Supported: Cursor, Claude Desktop, VS Code, Windsurf\n")
        return

    for agent in agents:
        status = "FOUND" if agent.installed else "not found"
        configured = " (already configured)" if agent.already_configured else ""
        icon = "+" if agent.installed else "-"
        print(f"  [{icon}] {agent.name}: {status}{configured}")
    print()

    # Step 2: Configure agents
    print("[2/3] Configuring MCP connection...\n")
    results = configure_all(use_url=args.url if hasattr(args, "url") else False)

    for agent, success, msg in results:
        icon = "+" if success else "x"
        print(f"  [{icon}] {msg}")
    print()

    # Step 3: Startup registration
    if not args.no_startup:
        print("[3/3] Registering auto-start...\n")
        success, msg = register_startup(silent=True)
        icon = "+" if success else "x"
        print(f"  [{icon}] {msg}")
    else:
        print("[3/3] Skipping auto-start (--no-startup)\n")

    print()
    print("Done! Start the server with: agent-skill serve")
    print()


def cmd_doctor(args: argparse.Namespace) -> None:
    print("\n[doctor] Agent Skill Hub — Health Check\n")

    # Check skills
    skills = load_skills(get_skills_dir())
    print(f"  Skills directory: {get_skills_dir()}")
    print(f"  Skills loaded: {len(skills)}")
    if skills:
        for name in sorted(skills.keys()):
            print(f"    + {name}")
    print()

    # Check agents
    print("  AI Agents:")
    agents = discover_agents()
    for agent in agents:
        if agent.installed:
            status = "configured" if agent.already_configured else "NOT configured"
            icon = "+" if agent.already_configured else "!"
            print(f"    [{icon}] {agent.name}: {status}")
            if agent.config_path:
                print(f"        config: {agent.config_path}")
        else:
            print(f"    [-] {agent.name}: not installed")
    print()

    # Check startup
    startup = is_registered()
    icon = "+" if startup else "-"
    print(f"  [{icon}] Auto-start: {'registered' if startup else 'not registered'}")

    # Check server
    import urllib.request
    try:
        with urllib.request.urlopen("http://localhost:3100/health", timeout=2) as resp:
            print(f"  [+] MCP Server: running (port 3100)")
    except Exception:
        print(f"  [-] MCP Server: not running")

    print()


def cmd_uninstall(args: argparse.Namespace) -> None:
    print("\n[uninstall] Removing auto-start...\n")
    success, msg = unregister_startup()
    icon = "+" if success else "-"
    print(f"  [{icon}] {msg}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(prog="agent-skill", description="Agent Skill Hub CLI")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list", help="List all installed skills")

    run_parser = sub.add_parser("run", help="Run a skill")
    run_parser.add_argument("skill_name", help="Name of the skill to run")
    run_parser.add_argument("input", nargs="?", default=None, help="JSON input")

    serve_parser = sub.add_parser("serve", help="Start MCP server")
    serve_parser.add_argument("--port", "-p", type=int, default=3100, help="Port (default: 3100)")

    setup_parser = sub.add_parser("setup", help="Auto-detect and configure AI agents")
    setup_parser.add_argument("--url", action="store_true", help="Use URL mode instead of command mode")
    setup_parser.add_argument("--no-startup", action="store_true", help="Skip auto-start registration")

    sub.add_parser("doctor", help="Check configuration and health status")

    sub.add_parser("uninstall", help="Remove auto-start and cleanup")

    args = parser.parse_args()

    commands = {
        "list": cmd_list,
        "run": cmd_run,
        "serve": cmd_serve,
        "setup": cmd_setup,
        "doctor": cmd_doctor,
        "uninstall": cmd_uninstall,
    }

    handler = commands.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
