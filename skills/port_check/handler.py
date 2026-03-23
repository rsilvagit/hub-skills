import socket


def _check_port(host, port, timeout=2):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (ConnectionRefusedError, TimeoutError, OSError):
        return False


def handler(input_data):
    action = input_data.get("action", "check")
    host = input_data.get("host", "localhost")

    if action == "check":
        port = input_data.get("port")
        if port is None:
            return {"error": "Missing 'port' parameter"}
        is_open = _check_port(host, port)
        return {"host": host, "port": port, "open": is_open}

    elif action == "scan":
        ports = input_data.get("ports", [80, 443, 3000, 3100, 5000, 5432, 6379, 8000, 8080, 27017])
        results = []
        for port in ports[:50]:
            results.append({"port": port, "open": _check_port(host, port, timeout=1)})
        open_ports = [r["port"] for r in results if r["open"]]
        return {"host": host, "scanned": len(results), "open_ports": open_ports, "details": results}

    else:
        return {"error": f"Unknown action: {action}. Use: check, scan"}
