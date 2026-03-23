from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError


def handler(input_data):
    url = input_data["url"]
    method = input_data.get("method", "GET").upper()
    headers = input_data.get("headers", {})
    body = input_data.get("body")

    data = body.encode("utf-8") if body else None
    req = Request(url, data=data, headers=headers, method=method)

    try:
        with urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8", errors="replace")
            return {
                "status": resp.status,
                "headers": dict(resp.headers),
                "body": content[:5000],
            }
    except HTTPError as e:
        return {
            "status": e.code,
            "error": str(e.reason),
            "body": e.read().decode("utf-8", errors="replace")[:5000],
        }
    except URLError as e:
        return {"status": 0, "error": str(e.reason)}
