# Agent Skill Hub

Runtime + MCP Server + Adapter para skills de agentes AI.

Carrega skills locais, executa com seguranca (async + timeout), expoe via protocolo MCP e converte para formato OpenAI/Copilot.

## Arquitetura

```
hub-skills/
├── agent_skill_hub/
│   ├── core/            # engine: types (Pydantic), loader, runner
│   ├── mcp_server/      # servidor HTTP MCP (list_tools + call_tool)
│   ├── cli/             # CLI: list, run, serve
│   ├── adapters/        # conversor OpenAI/Copilot
│   └── sdk/             # helpers para criar skills
├── skills/              # skills instaladas
│   ├── echo/
│   └── http_request/
└── pyproject.toml
```

## Instalacao

```bash
# Python >= 3.11
pip install -e .
```

## Uso

### CLI

```bash
# Listar skills disponiveis
agent-skill list

# Executar uma skill
agent-skill run echo '{"text": "hello"}'
agent-skill run http_request '{"url": "https://httpbin.org/get"}'

# Subir servidor MCP (default: porta 3100)
agent-skill serve
agent-skill serve --port 8080
```

### MCP Server

O servidor expoe 2 metodos via `POST /mcp`:

**list_tools** — lista todas as skills como tools:

```bash
curl -X POST http://localhost:3100/mcp \
  -H "Content-Type: application/json" \
  -d '{"method": "list_tools"}'
```

```json
{
  "tools": [
    {
      "name": "echo",
      "description": "Echo back the input text",
      "input_schema": { "type": "object", "properties": { "text": { "type": "string" } } }
    }
  ]
}
```

**call_tool** — executa uma skill:

```bash
curl -X POST http://localhost:3100/mcp \
  -H "Content-Type: application/json" \
  -d '{"method": "call_tool", "params": {"name": "echo", "arguments": {"text": "hello"}}}'
```

```json
{ "success": true, "data": { "output": "hello" } }
```

**Health check:** `GET /health`

### Adapter OpenAI/Copilot

```python
from agent_skill_hub.core import load_skills
from agent_skill_hub.adapters import to_openai_tools

skills = load_skills("./skills")
tools = to_openai_tools(skills)
# Retorna formato compativel com OpenAI function calling
```

## Criando uma Skill

### 1. Criar pasta em `skills/`

```
skills/minha_skill/
├── skill.json
└── handler.py
```

### 2. Definir `skill.json`

```json
{
  "name": "minha_skill",
  "description": "O que a skill faz",
  "input_schema": {
    "type": "object",
    "properties": {
      "param1": { "type": "string", "description": "Descricao do param" }
    },
    "required": ["param1"]
  },
  "execution": {
    "type": "python",
    "entry": "handler.py"
  }
}
```

### 3. Implementar `handler.py`

```python
def handler(input_data):
    return {"resultado": input_data["param1"]}
```

A funcao pode ser `handler`, `run` ou `main`. Suporta funcoes sync e async.

### Tipos de execucao

| Tipo | Campo | Descricao |
|------|-------|-----------|
| `python` | `entry` | Caminho do arquivo `.py` relativo a pasta da skill |
| `http` | `endpoint` | URL do servico externo (POST com JSON) |

## Integracao com Cursor

1. Suba o servidor: `agent-skill serve`
2. No Cursor, configure o MCP apontando para `http://localhost:3100/mcp`
3. As skills aparecem como tools disponiveis

## Seguranca

- Timeout de 30s por execucao de skill
- Timeout de 15s em requests HTTP
- Validacao de schema via Pydantic
- try/catch global no runner

## Skills incluidas

| Skill | Descricao |
|-------|-----------|
| `echo` | Retorna o texto recebido |
| `http_request` | Faz requisicoes HTTP (GET/POST/PUT/DELETE) |
