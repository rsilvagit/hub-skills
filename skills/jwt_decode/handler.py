import base64
import json
from datetime import datetime, timezone


def _decode_part(part):
    padding = 4 - len(part) % 4
    part += "=" * padding
    decoded = base64.urlsafe_b64decode(part)
    return json.loads(decoded)


def _format_ts(ts):
    try:
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
    except Exception:
        return None


def handler(input_data):
    token = input_data["token"].strip()
    parts = token.split(".")

    if len(parts) != 3:
        return {"error": "Invalid JWT: expected 3 parts (header.payload.signature)"}

    header = _decode_part(parts[0])
    payload = _decode_part(parts[1])

    result = {
        "header": header,
        "payload": payload,
    }

    if "exp" in payload:
        exp_dt = _format_ts(payload["exp"])
        now = datetime.now(tz=timezone.utc)
        expired = now.timestamp() > payload["exp"]
        result["expiration"] = {"exp_utc": exp_dt, "expired": expired}

    if "iat" in payload:
        result["issued_at"] = _format_ts(payload["iat"])

    return result
