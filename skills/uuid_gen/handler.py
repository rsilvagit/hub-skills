import uuid


def handler(input_data):
    action = input_data.get("action", "generate")

    if action == "generate":
        count = min(int(input_data.get("count", 1)), 50)
        uuids = [str(uuid.uuid4()) for _ in range(count)]
        return {"uuids": uuids} if count > 1 else {"uuid": uuids[0]}

    elif action == "validate":
        value = input_data.get("value", "")
        try:
            parsed = uuid.UUID(value)
            return {
                "valid": True,
                "uuid": str(parsed),
                "version": parsed.version,
                "variant": str(parsed.variant),
            }
        except ValueError:
            return {"valid": False, "error": "Invalid UUID format"}

    else:
        return {"error": f"Unknown action: {action}. Use: generate, validate"}
