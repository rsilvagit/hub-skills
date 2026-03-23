import ast
from pathlib import Path


class _NameCollector(ast.NodeVisitor):
    def __init__(self):
        self.imported = {}      # name -> line
        self.assigned = {}      # name -> line
        self.used = set()
        self.unreachable = []

    def visit_Import(self, node):
        for alias in node.names:
            name = alias.asname or alias.name.split(".")[0]
            self.imported[name] = node.lineno

    def visit_ImportFrom(self, node):
        for alias in node.names:
            name = alias.asname or alias.name
            self.imported[name] = node.lineno

    def visit_Name(self, node):
        if isinstance(node.ctx, (ast.Load, ast.Del)):
            self.used.add(node.id)
        elif isinstance(node.ctx, ast.Store):
            if node.id not in self.assigned:
                self.assigned[node.id] = node.lineno
        self.generic_visit(node)

    def visit_Attribute(self, node):
        if isinstance(node.value, ast.Name):
            self.used.add(node.value.id)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        for decorator in node.decorator_list:
            self.visit(decorator)
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Return(self, node):
        self.generic_visit(node)
        parent = getattr(node, '_parent', None)
        if parent and isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
            idx = parent.body.index(node) if node in parent.body else -1
            if idx >= 0 and idx < len(parent.body) - 1:
                next_node = parent.body[idx + 1]
                self.unreachable.append({
                    "type": "unreachable_code",
                    "line": next_node.lineno,
                    "message": f"Code after return statement at line {node.lineno}",
                })


def _set_parents(node):
    for child in ast.iter_child_nodes(node):
        child._parent = node
        _set_parents(child)


def _analyze(source):
    tree = ast.parse(source)
    _set_parents(tree)

    collector = _NameCollector()
    collector.visit(tree)

    issues = []

    # Unused imports
    for name, line in collector.imported.items():
        if name not in collector.used and not name.startswith("_"):
            issues.append({
                "type": "unused_import",
                "name": name,
                "line": line,
                "message": f"Import '{name}' is never used",
            })

    # Unused variables (exclude params, loop vars in comprehensions, _prefixed)
    func_params = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for arg in node.args.args + node.args.kwonlyargs:
                func_params.add(arg.arg)
            if node.args.vararg:
                func_params.add(node.args.vararg.arg)
            if node.args.kwarg:
                func_params.add(node.args.kwarg.arg)

    for name, line in collector.assigned.items():
        if (name not in collector.used
                and name not in func_params
                and name not in collector.imported
                and not name.startswith("_")):
            issues.append({
                "type": "unused_variable",
                "name": name,
                "line": line,
                "message": f"Variable '{name}' is assigned but never used",
            })

    issues.extend(collector.unreachable)
    issues.sort(key=lambda x: x["line"])

    return {
        "total_issues": len(issues),
        "issues": issues,
        "clean": len(issues) == 0,
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
