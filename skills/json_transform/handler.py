import json


def _resolve_path(data, path):
    keys = path.split(".")
    current = data
    for key in keys:
        if isinstance(current, list):
            try:
                current = current[int(key)]
            except (ValueError, IndexError):
                return None
        elif isinstance(current, dict):
            current = current.get(key)
        else:
            return None
        if current is None:
            return None
    return current


def _flatten(data, prefix=""):
    items = {}
    if isinstance(data, dict):
        for k, v in data.items():
            new_key = f"{prefix}.{k}" if prefix else k
            items.update(_flatten(v, new_key))
    elif isinstance(data, list):
        for i, v in enumerate(data):
            new_key = f"{prefix}.{i}" if prefix else str(i)
            items.update(_flatten(v, new_key))
    else:
        items[prefix] = data
    return items


def handler(input_data):
    data = input_data["data"]
    if isinstance(data, str):
        data = json.loads(data)

    action = input_data.get("action", "pretty")

    if action == "pretty":
        return {"output": json.dumps(data, indent=2, ensure_ascii=False)}
    elif action == "minify":
        return {"output": json.dumps(data, separators=(",", ":"), ensure_ascii=False)}
    elif action == "query":
        path = input_data.get("path", "")
        result = _resolve_path(data, path)
        return {"output": result}
    elif action == "keys":
        if isinstance(data, dict):
            return {"output": list(data.keys())}
        return {"output": [], "error": "Data is not an object"}
    elif action == "flatten":
        return {"output": _flatten(data)}
    else:
        return {"error": f"Unknown action: {action}"}
