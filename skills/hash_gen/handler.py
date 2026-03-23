import hashlib


SUPPORTED = {"md5", "sha1", "sha256", "sha512"}


def handler(input_data):
    text = input_data["text"]
    algo = input_data.get("algorithm", "sha256").lower()

    if algo not in SUPPORTED:
        return {"error": f"Unsupported algorithm: {algo}. Use: {', '.join(sorted(SUPPORTED))}"}

    h = hashlib.new(algo, text.encode("utf-8"))
    return {
        "algorithm": algo,
        "hash": h.hexdigest(),
        "length": len(h.hexdigest()),
    }
