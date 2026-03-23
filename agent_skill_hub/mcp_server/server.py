from __future__ import annotations

import asyncio
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any

from agent_skill_hub.core import load_skills, run_skill, Skill


class McpHandler(BaseHTTPRequestHandler):
    skills: dict[str, Skill] = {}

    def log_message(self, format: str, *args: Any) -> None:
        print(f"[mcp] {args[0] if args else format}")

    def _send_json(self, data: Any, status: int = 200) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send_json({"status": "ok", "skills": len(self.skills)})
        else:
            self._send_json({"error": "Not found"}, 404)

    def do_POST(self) -> None:
        if self.path != "/mcp":
            self._send_json({"error": "Not found"}, 404)
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length)
            body = json.loads(raw)
        except Exception:
            self._send_json({"error": "Invalid request"}, 400)
            return

        result = asyncio.run(self._handle_mcp(body))
        self._send_json(result)

    async def _handle_mcp(self, body: dict[str, Any]) -> dict[str, Any]:
        method = body.get("method")
        params = body.get("params", {})

        if method == "list_tools":
            tools = [
                {
                    "name": s.name,
                    "description": s.description,
                    "input_schema": s.input_schema,
                }
                for s in self.skills.values()
            ]
            return {"tools": tools}

        elif method == "call_tool":
            name = params.get("name")
            if not name:
                return {"error": "Missing 'name' in params"}
            skill = self.skills.get(name)
            if not skill:
                return {"error": f"Skill '{name}' not found"}
            result = await run_skill(skill, params.get("arguments", {}))
            return result.model_dump()

        else:
            return {"error": f"Unknown method: {method}"}


def create_mcp_server(skills_dir: str, port: int = 3100) -> HTTPServer:
    skills = load_skills(skills_dir)
    print(f"[mcp] Loaded {len(skills)} skill(s): {', '.join(skills.keys())}")

    McpHandler.skills = skills

    server = HTTPServer(("0.0.0.0", port), McpHandler)
    print(f"[mcp] Server running at http://localhost:{port}")
    print(f"[mcp] POST /mcp — list_tools | call_tool")
    return server
