import ast
from pathlib import Path


def _cyclomatic_complexity(node):
    """Count branches: if/elif/for/while/except/and/or/assert/with/ternary."""
    complexity = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.IfExp)):
            complexity += 1
        elif isinstance(child, (ast.For, ast.While, ast.AsyncFor)):
            complexity += 1
        elif isinstance(child, ast.ExceptHandler):
            complexity += 1
        elif isinstance(child, (ast.With, ast.AsyncWith)):
            complexity += 1
        elif isinstance(child, ast.Assert):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += len(child.values) - 1
    return complexity


def _analyze(source):
    tree = ast.parse(source)
    lines = source.splitlines()
    total_lines = len(lines)
    blank_lines = sum(1 for l in lines if not l.strip())
    comment_lines = sum(1 for l in lines if l.strip().startswith("#"))
    code_lines = total_lines - blank_lines - comment_lines

    functions = []
    classes = []
    top_level_funcs = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_lines = node.end_lineno - node.lineno + 1
            cc = _cyclomatic_complexity(node)
            params = len(node.args.args) + len(node.args.kwonlyargs)
            functions.append({
                "name": node.name,
                "line": node.lineno,
                "length": func_lines,
                "params": params,
                "complexity": cc,
            })
        elif isinstance(node, ast.ClassDef):
            methods = sum(1 for n in node.body
                         if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)))
            classes.append({
                "name": node.name,
                "line": node.lineno,
                "methods": methods,
            })

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            top_level_funcs.append(node.name)

    avg_func_length = (sum(f["length"] for f in functions) / len(functions)) if functions else 0
    avg_complexity = (sum(f["complexity"] for f in functions) / len(functions)) if functions else 0
    max_complexity = max((f["complexity"] for f in functions), default=0)

    return {
        "summary": {
            "total_lines": total_lines,
            "code_lines": code_lines,
            "blank_lines": blank_lines,
            "comment_lines": comment_lines,
            "functions": len(functions),
            "classes": len(classes),
            "avg_function_length": round(avg_func_length, 1),
            "avg_complexity": round(avg_complexity, 1),
            "max_complexity": max_complexity,
        },
        "functions": functions,
        "classes": classes,
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
