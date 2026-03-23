import ast
from pathlib import Path


def _analyze(source, ignore_private):
    tree = ast.parse(source)
    items = []

    # Module docstring
    module_doc = ast.get_docstring(tree)
    items.append({
        "type": "module",
        "name": "<module>",
        "line": 1,
        "has_docstring": module_doc is not None,
    })

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            if ignore_private and node.name.startswith("_"):
                continue
            doc = ast.get_docstring(node)
            items.append({
                "type": "class",
                "name": node.name,
                "line": node.lineno,
                "has_docstring": doc is not None,
            })

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if ignore_private and node.name.startswith("_"):
                continue
            doc = ast.get_docstring(node)
            items.append({
                "type": "function",
                "name": node.name,
                "line": node.lineno,
                "has_docstring": doc is not None,
            })

    documented = sum(1 for i in items if i["has_docstring"])
    total = len(items)
    coverage = round((documented / total) * 100, 1) if total > 0 else 100.0

    missing = [i for i in items if not i["has_docstring"]]

    return {
        "coverage_percent": coverage,
        "total_items": total,
        "documented": documented,
        "missing_count": len(missing),
        "missing": missing,
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

    ignore_private = input_data.get("ignore_private", True)
    return _analyze(code, ignore_private)
