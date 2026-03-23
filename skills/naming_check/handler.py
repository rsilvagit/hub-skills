import ast
import re
from pathlib import Path

SNAKE_CASE = re.compile(r'^_*[a-z][a-z0-9_]*$')
PASCAL_CASE = re.compile(r'^_*[A-Z][a-zA-Z0-9]*$')
UPPER_CASE = re.compile(r'^_*[A-Z][A-Z0-9_]*$')

DUNDER = re.compile(r'^__[a-z][a-z0-9_]*__$')

BUILTIN_OVERRIDES = {"__init__", "__str__", "__repr__", "__len__", "__eq__",
                     "__hash__", "__enter__", "__exit__", "__call__",
                     "__getitem__", "__setitem__", "__delitem__", "__iter__",
                     "__next__", "__contains__", "__bool__", "__new__"}


def _analyze(source):
    tree = ast.parse(source)
    violations = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            name = node.name
            if DUNDER.match(name) or name in BUILTIN_OVERRIDES:
                continue
            if not SNAKE_CASE.match(name):
                violations.append({
                    "type": "function",
                    "name": name,
                    "line": node.lineno,
                    "expected": "snake_case",
                    "suggestion": _to_snake(name),
                })

            # Check param names
            for arg in node.args.args + node.args.kwonlyargs:
                if arg.arg == "self" or arg.arg == "cls":
                    continue
                if not SNAKE_CASE.match(arg.arg):
                    violations.append({
                        "type": "parameter",
                        "name": arg.arg,
                        "line": arg.lineno,
                        "expected": "snake_case",
                        "function": name,
                        "suggestion": _to_snake(arg.arg),
                    })

        elif isinstance(node, ast.ClassDef):
            if not PASCAL_CASE.match(node.name):
                violations.append({
                    "type": "class",
                    "name": node.name,
                    "line": node.lineno,
                    "expected": "PascalCase",
                    "suggestion": _to_pascal(node.name),
                })

        elif isinstance(node, ast.Assign):
            # Top-level UPPER_CASE constants check
            for target in node.targets:
                if isinstance(target, ast.Name):
                    name = target.id
                    if name.startswith("_"):
                        continue
                    # If it looks like it SHOULD be a constant (all caps partial)
                    # but isn't fully compliant
                    if any(c.isupper() for c in name) and any(c.islower() for c in name):
                        if not SNAKE_CASE.match(name) and not PASCAL_CASE.match(name):
                            violations.append({
                                "type": "variable",
                                "name": name,
                                "line": node.lineno,
                                "expected": "snake_case or UPPER_CASE",
                                "suggestion": _to_snake(name),
                            })

    return {
        "total_violations": len(violations),
        "violations": violations,
        "clean": len(violations) == 0,
    }


def _to_snake(name):
    name = name.lstrip("_")
    result = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', name)
    result = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', result)
    return result.lower()


def _to_pascal(name):
    return "".join(word.capitalize() for word in name.replace("-", "_").split("_"))


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
