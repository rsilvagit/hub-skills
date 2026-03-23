import re

FILE_HEADER = re.compile(r'^diff --git a/(.+?) b/(.+?)$')
HUNK_HEADER = re.compile(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$')

RISKY_PATTERNS = [
    (re.compile(r'(?i)(password|secret|api_?key|token)\s*='), "Possible hardcoded secret"),
    (re.compile(r'(?i)TODO|FIXME|HACK|XXX'), "TODO/FIXME marker"),
    (re.compile(r'console\.log|print\(|debugger'), "Debug statement"),
    (re.compile(r'\.env'), "Environment file reference"),
]


def handler(input_data):
    diff_text = input_data["diff"]
    max_add = input_data.get("max_additions_warning", 100)

    files = []
    current_file = None
    warnings = []

    for line in diff_text.splitlines():
        file_match = FILE_HEADER.match(line)
        if file_match:
            if current_file:
                files.append(current_file)
            current_file = {
                "file": file_match.group(2),
                "additions": 0,
                "deletions": 0,
                "hunks": 0,
                "changed_lines": [],
            }
            continue

        hunk_match = HUNK_HEADER.match(line)
        if hunk_match and current_file:
            current_file["hunks"] += 1
            continue

        if current_file is None:
            continue

        if line.startswith("+") and not line.startswith("+++"):
            current_file["additions"] += 1
            content = line[1:]
            for pattern, msg in RISKY_PATTERNS:
                if pattern.search(content):
                    warnings.append({
                        "file": current_file["file"],
                        "content": content.strip()[:80],
                        "warning": msg,
                    })
        elif line.startswith("-") and not line.startswith("---"):
            current_file["deletions"] += 1

    if current_file:
        files.append(current_file)

    # Remove changed_lines from output (too verbose)
    for f in files:
        del f["changed_lines"]
        if f["additions"] > max_add:
            warnings.append({
                "file": f["file"],
                "warning": f"Large change: {f['additions']} additions",
            })

    total_add = sum(f["additions"] for f in files)
    total_del = sum(f["deletions"] for f in files)

    return {
        "files_changed": len(files),
        "total_additions": total_add,
        "total_deletions": total_del,
        "files": files,
        "warnings": warnings,
        "summary": f"{len(files)} file(s), +{total_add} -{total_del}",
    }
