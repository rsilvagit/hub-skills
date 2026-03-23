from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from agent_skill_hub.core import load_skills, run_skill
from agent_skill_hub.mcp_server import create_mcp_server


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


def main() -> None:
    parser = argparse.ArgumentParser(prog="agent-skill", description="Agent Skill Hub CLI")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list", help="List all installed skills")

    run_parser = sub.add_parser("run", help="Run a skill")
    run_parser.add_argument("skill_name", help="Name of the skill to run")
    run_parser.add_argument("input", nargs="?", default=None, help="JSON input")

    serve_parser = sub.add_parser("serve", help="Start MCP server")
    serve_parser.add_argument("--port", "-p", type=int, default=3100, help="Port (default: 3100)")

    args = parser.parse_args()

    commands = {
        "list": cmd_list,
        "run": cmd_run,
        "serve": cmd_serve,
    }

    handler = commands.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
