import ast
import re
from pathlib import Path

SECRET_PATTERNS = [
    (re.compile(r'(?i)(password|passwd|pwd|secret|api_?key|token|auth)\s*=\s*["\'][^"\']{4,}["\']'), "hardcoded_secret"),
    (re.compile(r'(?i)(aws_access_key|aws_secret|private_key)\s*=\s*["\'][^"\']+["\']'), "hardcoded_credential"),
    (re.compile(r'["\'](?:sk-|pk_live_|pk_test_|ghp_|gho_|AKIA)[A-Za-z0-9]+["\']'), "api_key_pattern"),
]

DANGEROUS_CALLS = {
    "eval": "Use ast.literal_eval() instead of eval()",
    "exec": "Avoid exec() — it runs arbitrary code",
    "compile": "compile() with user input can be dangerous",
    "__import__": "Use importlib.import_module() instead",
}

DANGEROUS_MODULES = {
    "pickle": "pickle can execute arbitrary code on deserialization",
    "marshal": "marshal is not safe for untrusted data",
    "shelve": "shelve uses pickle internally",
}


class _SecurityVisitor(ast.NodeVisitor):
    def __init__(self, lines):
        self.issues = []
        self.lines = lines

    def visit_Call(self, node):
        # Check dangerous builtins
        if isinstance(node.func, ast.Name):
            name = node.func.id
            if name in DANGEROUS_CALLS:
                self.issues.append({
                    "type": "dangerous_call",
                    "severity": "error",
                    "line": node.lineno,
                    "name": name,
                    "message": DANGEROUS_CALLS[name],
                })

        # Check subprocess with shell=True
        if isinstance(node.func, ast.Attribute) and node.func.attr in ("call", "run", "Popen"):
            for kw in node.keywords:
                if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    self.issues.append({
                        "type": "command_injection",
                        "severity": "error",
                        "line": node.lineno,
                        "message": "subprocess with shell=True is vulnerable to command injection",
                    })

        # Check os.system
        if (isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "os"
                and node.func.attr == "system"):
            self.issues.append({
                "type": "command_injection",
                "severity": "error",
                "line": node.lineno,
                "message": "os.system() is vulnerable to command injection. Use subprocess.run() instead",
            })

        # SQL injection: string formatting in execute()
        if isinstance(node.func, ast.Attribute) and node.func.attr == "execute":
            if node.args:
                arg = node.args[0]
                if isinstance(arg, (ast.JoinedStr, ast.BinOp)):
                    self.issues.append({
                        "type": "sql_injection",
                        "severity": "error",
                        "line": node.lineno,
                        "message": "Possible SQL injection: use parameterized queries instead of string formatting",
                    })

        self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            name = alias.name.split(".")[0]
            if name in DANGEROUS_MODULES:
                self.issues.append({
                    "type": "insecure_module",
                    "severity": "warning",
                    "line": node.lineno,
                    "name": name,
                    "message": DANGEROUS_MODULES[name],
                })

    def visit_ImportFrom(self, node):
        if node.module:
            name = node.module.split(".")[0]
            if name in DANGEROUS_MODULES:
                self.issues.append({
                    "type": "insecure_module",
                    "severity": "warning",
                    "line": node.lineno,
                    "name": name,
                    "message": DANGEROUS_MODULES[name],
                })


def _scan_patterns(source, lines):
    issues = []
    for i, line in enumerate(lines, 1):
        for pattern, issue_type in SECRET_PATTERNS:
            if pattern.search(line):
                issues.append({
                    "type": issue_type,
                    "severity": "error",
                    "line": i,
                    "message": f"Possible hardcoded secret detected",
                    "snippet": line.strip()[:80],
                })
                break

        # Debug leftovers
        stripped = line.strip()
        if stripped == "import pdb; pdb.set_trace()":
            issues.append({
                "type": "debug_leftover",
                "severity": "warning",
                "line": i,
                "message": "Debugger breakpoint left in code",
            })
        elif stripped.startswith("print(") and "debug" in stripped.lower():
            issues.append({
                "type": "debug_leftover",
                "severity": "warning",
                "line": i,
                "message": "Debug print statement left in code",
            })

    return issues


def _analyze(source):
    lines = source.splitlines()
    tree = ast.parse(source)

    visitor = _SecurityVisitor(lines)
    visitor.visit(tree)

    pattern_issues = _scan_patterns(source, lines)

    all_issues = visitor.issues + pattern_issues
    all_issues.sort(key=lambda x: x["line"])

    errors = sum(1 for i in all_issues if i["severity"] == "error")
    warnings = sum(1 for i in all_issues if i["severity"] == "warning")

    return {
        "total_issues": len(all_issues),
        "errors": errors,
        "warnings": warnings,
        "issues": all_issues,
        "secure": len(all_issues) == 0,
    }


def handler(input_data):
    code = input_data.get("code")
    file_path = input_data.get("file_path")

    if file_path:
        p = Path(file_path)
        if not p.exists():
            return {"error": f"File not found: {file_path}"}
        code = p.read_text(encoding="utf-8")
    elif not code:
        return {"error": "Provide 'code' or 'file_path'"}

    return _analyze(code)
