import ast
from pathlib import Path

DEFAULTS = {
    "max_function_lines": 30,
    "max_params": 5,
    "max_nesting": 4,
    "max_file_lines": 300,
    "max_complexity": 10,
    "max_methods": 10,
}


def _nesting_depth(node, depth=0):
    max_depth = depth
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try,
                              ast.AsyncFor, ast.AsyncWith)):
            max_depth = max(max_depth, _nesting_depth(child, depth + 1))
        else:
            max_depth = max(max_depth, _nesting_depth(child, depth))
    return max_depth


def _cyclomatic(node):
    cc = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.IfExp, ast.For, ast.While, ast.AsyncFor)):
            cc += 1
        elif isinstance(child, ast.ExceptHandler):
            cc += 1
        elif isinstance(child, ast.BoolOp):
            cc += len(child.values) - 1
    return cc


def _analyze(source, thresholds):
    t = {**DEFAULTS, **thresholds}
    tree = ast.parse(source)
    lines = source.splitlines()
    smells = []

    if len(lines) > t["max_file_lines"]:
        smells.append({
            "smell": "large_file",
            "severity": "warning",
            "message": f"File has {len(lines)} lines (max {t['max_file_lines']})",
            "line": 1,
        })

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_lines = node.end_lineno - node.lineno + 1
            params = len(node.args.args) + len(node.args.kwonlyargs)
            depth = _nesting_depth(node)
            cc = _cyclomatic(node)

            if func_lines > t["max_function_lines"]:
                smells.append({
                    "smell": "long_function",
                    "severity": "warning",
                    "message": f"'{node.name}' has {func_lines} lines (max {t['max_function_lines']})",
                    "line": node.lineno,
                })

            if params > t["max_params"]:
                smells.append({
                    "smell": "too_many_params",
                    "severity": "warning",
                    "message": f"'{node.name}' has {params} parameters (max {t['max_params']})",
                    "line": node.lineno,
                })

            if depth > t["max_nesting"]:
                smells.append({
                    "smell": "deep_nesting",
                    "severity": "warning",
                    "message": f"'{node.name}' has nesting depth {depth} (max {t['max_nesting']})",
                    "line": node.lineno,
                })

            if cc > t["max_complexity"]:
                smells.append({
                    "smell": "high_complexity",
                    "severity": "error",
                    "message": f"'{node.name}' has cyclomatic complexity {cc} (max {t['max_complexity']})",
                    "line": node.lineno,
                })

        elif isinstance(node, ast.ClassDef):
            methods = sum(1 for n in node.body
                         if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)))
            if methods > t["max_methods"]:
                smells.append({
                    "smell": "god_class",
                    "severity": "warning",
                    "message": f"Class '{node.name}' has {methods} methods (max {t['max_methods']})",
                    "line": node.lineno,
                })

    return {
        "total_smells": len(smells),
        "smells": smells,
        "clean": len(smells) == 0,
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

    thresholds = input_data.get("thresholds", {})
    return _analyze(code, thresholds)
