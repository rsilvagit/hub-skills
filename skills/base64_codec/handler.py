import base64


def handler(input_data):
    text = input_data["text"]
    action = input_data.get("action", "encode")

    if action == "encode":
        result = base64.b64encode(text.encode("utf-8")).decode("ascii")
        return {"output": result}
    elif action == "decode":
        result = base64.b64decode(text).decode("utf-8")
        return {"output": result}
    else:
        return {"error": f"Unknown action: {action}. Use 'encode' or 'decode'"}
