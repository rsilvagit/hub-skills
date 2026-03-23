from datetime import datetime, timezone


def handler(input_data):
    action = input_data.get("action", "now")

    if action == "now":
        now = datetime.now(tz=timezone.utc)
        return {
            "unix": int(now.timestamp()),
            "unix_ms": int(now.timestamp() * 1000),
            "iso": now.isoformat(),
        }

    value = input_data.get("value", "")

    if action == "to_iso":
        ts = float(value)
        if ts > 1e12:
            ts = ts / 1000
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        return {"iso": dt.isoformat(), "unix": int(ts)}

    elif action == "to_unix":
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return {"unix": int(dt.timestamp()), "unix_ms": int(dt.timestamp() * 1000), "iso": dt.isoformat()}

    else:
        return {"error": f"Unknown action: {action}. Use: now, to_iso, to_unix"}
