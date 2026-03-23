import ast
import sys
from pathlib import Path

STDLIB_MODULES = set(sys.stdlib_module_names) if hasattr(sys, 'stdlib_module_names') else {
    "os", "sys", "json", "re", "math", "datetime", "pathlib", "typing",
    "collections", "functools", "itertools", "hashlib", "base64", "uuid",
    "socket", "http", "urllib", "asyncio", "logging", "unittest", "abc",
    "ast", "io", "csv", "sqlite3", "subprocess", "threading", "multiprocessing",
    "contextlib", "dataclasses", "enum", "copy", "shutil", "tempfile",
    "time", "random", "string", "struct", "textwrap", "traceback", "warnings",
}


def _classify(module_name):
    root = module_name.split(".")[0]
    if root in STDLIB_MODULES:
        return "stdlib"
    if module_name.startswith("."):
        return "local"
    return "third_party"


def _analyze(source):
    tree = ast.parse(source)

    imports = {"stdlib": [], "third_party": [], "local": []}
    all_imports = []
    late_imports = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                category = _classify(alias.name)
                entry = {
                    "module": alias.name,
                    "alias": alias.asname,
                    "line": node.lineno,
                    "category": category,
                }
                imports[category].append(entry)
                all_imports.append(entry)

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            level = node.level or 0
            category = "local" if level > 0 else _classify(module)
            names = [a.name for a in node.names]
            entry = {
                "module": ("." * level + module) if level else module,
                "names": names,
                "line": node.lineno,
                "category": category,
            }
            imports[category].append(entry)
            all_imports.append(entry)

    # Late imports (inside functions)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for child in ast.walk(node):
                if isinstance(child, (ast.Import, ast.ImportFrom)):
                    mod = ""
                    if isinstance(child, ast.Import):
                        mod = child.names[0].name
                    elif child.module:
                        mod = child.module
                    late_imports.append({
                        "module": mod,
                        "inside_function": node.name,
                        "line": child.lineno,
                    })

    # Sort order check (stdlib -> third_party -> local)
    order_issues = []
    last_category_order = -1
    category_rank = {"stdlib": 0, "third_party": 1, "local": 2}
    for imp in all_imports:
        rank = category_rank[imp["category"]]
        if rank < last_category_order:
            order_issues.append({
                "line": imp["line"],
                "message": f"Import '{imp.get('module', '')}' ({imp['category']}) should come before previous imports",
            })
        last_category_order = rank

    return {
        "total_imports": len(all_imports),
        "stdlib": len(imports["stdlib"]),
        "third_party": len(imports["third_party"]),
        "local": len(imports["local"]),
        "imports": imports,
        "late_imports": late_imports,
        "order_issues": order_issues,
        "well_ordered": len(order_issues) == 0,
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
