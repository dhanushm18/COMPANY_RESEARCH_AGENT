from functools import lru_cache
from urllib import error, request


@lru_cache(maxsize=512)
def probe_url(url: str, timeout: int = 2):
    if not isinstance(url, str) or not url.startswith(("http://", "https://")):
        return {"status": None, "error": "invalid-scheme", "final_url": url, "body": ""}

    req = request.Request(url, method="GET", headers={"User-Agent": "Mozilla/5.0"})
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read(4096)
            return {
                "status": getattr(resp, "status", 200),
                "final_url": resp.geturl(),
                "content_type": resp.headers.get("Content-Type", ""),
                "body": raw.decode("utf-8", errors="ignore"),
                "error": None,
            }
    except error.HTTPError as e:
        return {"status": e.code, "error": "http", "final_url": url, "content_type": "", "body": ""}
    except Exception:
        return {"status": None, "error": "network", "final_url": url, "content_type": "", "body": ""}
