import re


FLAG_MAP = {
    "i": re.IGNORECASE,
    "m": re.MULTILINE,
    "s": re.DOTALL,
}


def handler(input_data):
    pattern = input_data["pattern"]
    text = input_data["text"]
    flags_str = input_data.get("flags", "")

    flags = 0
    for ch in flags_str:
        if ch in FLAG_MAP:
            flags |= FLAG_MAP[ch]

    compiled = re.compile(pattern, flags)
    matches = []

    for m in compiled.finditer(text):
        match_info = {
            "match": m.group(),
            "start": m.start(),
            "end": m.end(),
        }
        if m.groups():
            match_info["groups"] = list(m.groups())
        if m.groupdict():
            match_info["named_groups"] = m.groupdict()
        matches.append(match_info)

    return {
        "pattern": pattern,
        "matches_found": len(matches),
        "matches": matches,
    }
