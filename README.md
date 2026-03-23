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
│   ├── echo/            # utilitario
│   ├── http_request/    # utilitario
│   ├── json_transform/  # utilitario
│   ├── base64_codec/    # utilitario
│   ├── hash_gen/        # utilitario
│   ├── jwt_decode/      # utilitario
│   ├── timestamp_convert/ # utilitario
│   ├── uuid_gen/        # utilitario
│   ├── regex_test/      # utilitario
│   ├── port_check/      # utilitario
│   ├── code_metrics/    # code quality
│   ├── code_smell/      # code quality
│   ├── dead_code/       # code quality
│   ├── naming_check/    # code quality
│   ├── security_scan/   # code quality
│   ├── diff_review/     # code quality
│   ├── docstring_check/ # code quality
│   └── import_analyzer/ # code quality
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

### Utilitarios Backend

| Skill | Descricao |
|-------|-----------|
| `echo` | Retorna o texto recebido |
| `http_request` | Faz requisicoes HTTP (GET/POST/PUT/DELETE) |
| `json_transform` | Pretty print, minify, query por dot-path, flatten JSON |
| `base64_codec` | Encode/decode Base64 |
| `hash_gen` | Gera hashes MD5, SHA1, SHA256, SHA512 |
| `jwt_decode` | Decodifica JWT (header, payload, expiracao) |
| `timestamp_convert` | Converte entre Unix timestamp e ISO 8601 |
| `uuid_gen` | Gera UUIDs v4 ou valida existentes |
| `regex_test` | Testa regex com matches, groups e named groups |
| `port_check` | Verifica se porta esta aberta ou scan de portas |

### Code Quality e Review

| Skill | Descricao |
|-------|-----------|
| `code_metrics` | LOC, funcoes, classes, complexidade ciclomatica, media de linhas |
| `code_smell` | Detecta funcoes longas, nesting profundo, muitos params, god class |
| `dead_code` | Encontra imports e variaveis nao usados, codigo inalcancavel |
| `naming_check` | Valida PEP 8 (snake_case, PascalCase, UPPER_CASE) com sugestoes |
| `security_scan` | Detecta secrets hardcoded, SQL/command injection, eval, pickle |
| `diff_review` | Analisa git diff com stats e flags de mudancas arriscadas |
| `docstring_check` | Mede cobertura de docstrings em modulos, classes e funcoes |
| `import_analyzer` | Classifica imports (stdlib/third-party/local), ordem PEP 8 |

As skills de code quality aceitam `code` (string) ou `file_path` (caminho do arquivo) como input.
