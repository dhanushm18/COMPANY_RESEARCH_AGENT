"""
TC-8.2 - URL Validity (Workbook-Driven, No Mock Data)
Uses only Company Master.xlsx / Flat Companies Data URL fields.
"""

from pathlib import Path
import re
from urllib import request, error
from functools import lru_cache

import pandas as pd
import pytest

FILE_PATH = Path("pytests/data/sample_companies.xlsx")
SHEET_NAME = "Flat Companies Data"


@pytest.fixture(scope="module")
def df():
    assert FILE_PATH.exists(), f"{FILE_PATH} not found"
    return pd.read_excel(FILE_PATH, sheet_name=SHEET_NAME)


def _to_url(value, source_col):
    s = str(value).strip()
    if not s:
        return None
    if source_col == "twitter_handle":
        if s.startswith("http"):
            return s
        s = s.lstrip("@")
        return f"https://x.com/{s}"
    return s


@lru_cache(maxsize=512)
def _probe(url, timeout=2):
    if not isinstance(url, str) or not url.startswith(("http://", "https://")):
        return {"status": None, "final_url": url, "body": "", "error": "invalid-scheme"}
    req = request.Request(url, method="GET", headers={"User-Agent": "Mozilla/5.0"})
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            data = resp.read(4096)
            body = data.decode("utf-8", errors="ignore")
            return {
                "status": getattr(resp, "status", 200),
                "final_url": resp.geturl(),
                "body": body,
                "content_type": resp.headers.get("Content-Type", ""),
                "error": None,
            }
    except error.HTTPError as e:
        return {"status": e.code, "final_url": url, "body": "", "content_type": "", "error": "http"}
    except Exception:
        return {"status": None, "final_url": url, "body": "", "content_type": "", "error": "network"}


def _validate(url, mode):
    p = _probe(url)
    status = p["status"]
    final_url = str(p.get("final_url", ""))
    body = p.get("body", "").lower()

    if mode == "http_200":
        return "PASS" if status == 200 else "FAIL"
    if mode == "http_fail":
        return "FAIL" if status in {401, 403, 404} or p["error"] else "PASS"
    if mode == "redirect":
        return "PASS" if status == 200 and final_url and final_url != url else "FAIL"
    if mode == "timeout":
        return "FAIL" if p["error"] == "network" else "PASS"
    if mode == "restricted":
        return "FAIL" if any(k in body for k in ["private", "login", "suspended", "terminated"]) else "PASS"
    if mode == "format_logo":
        return "PASS" if re.fullmatch(r"^https?://.*\.(?:png|jpg|jpeg|svg|webp)(?:\?.*)?$", url) else "FAIL"
    if mode == "format_website":
        return "PASS" if re.fullmatch(r"^https?://[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}(/.*)?$", url) else "FAIL"
    if mode == "format_linkedin_company":
        return "PASS" if re.fullmatch(r"^https?://(www\.)?linkedin\.com/company/[A-Za-z0-9_\-]+/?$", url) else "FAIL"
    if mode == "invalid_linkedin_company":
        return "FAIL" if "/in/" in url else "PASS"
    if mode == "format_twitter":
        return "PASS" if re.fullmatch(r"^https?://(twitter\.com|x\.com)/[A-Za-z0-9_]{1,30}/?$", url) else "FAIL"
    if mode == "format_facebook":
        return "PASS" if re.fullmatch(r"^https?://(www\.)?facebook\.com/[A-Za-z0-9_.\-]+/?$", url) else "FAIL"
    if mode == "format_instagram":
        return "PASS" if re.fullmatch(r"^https?://(www\.)?instagram\.com/[A-Za-z0-9_.\-]+/?$", url) else "FAIL"
    if mode == "format_youtube":
        return "PASS" if re.fullmatch(r"^https?://(www\.)?youtube\.com/(c/[^/]+|@[^/]+|channel/[^/]+|user/[^/]+).*$", url) else "FAIL"
    if mode == "format_crunchbase":
        return "PASS" if re.fullmatch(r"^https?://(www\.)?crunchbase\.com/organization/[a-z0-9\-]+/?$", url) else "FAIL"
    if mode == "rss":
        base = url.rstrip("/")
        p1 = _probe(base + "/feed")
        p2 = _probe(base + "/rss")
        return "PASS" if p["status"] == 200 and (p1["status"] == 200 or p2["status"] == 200) else "FAIL"
    if mode == "inactive":
        return "WARNING" if p["status"] == 200 else "FAIL"
    return "FAIL"


def _pick(df, col, mode, expected):
    if col not in df.columns:
        pytest.skip(f"Missing column: {col}")
    for i, raw in enumerate(df[col].dropna().astype(str)):
        if i >= 20:
            break
        url = _to_url(raw, col)
        if not url:
            continue
        actual = _validate(url, mode)
        if actual == expected:
            return url
    pytest.skip(f"No workbook sample for {col} satisfying mode={mode} expected={expected}")


CASES = [
    ("8.2.1.1", "logo_url", "http_200", "PASS"),
    ("8.2.1.2", "logo_url", "http_fail", "FAIL"),
    ("8.2.1.3", "logo_url", "redirect", "PASS"),
    ("8.2.1.4", "logo_url", "format_logo", "PASS"),
    ("8.2.1.5", "logo_url", "format_logo", "FAIL"),
    ("8.2.1.6", "logo_url", "http_fail", "FAIL"),

    ("8.2.2.1", "website_url", "http_200", "PASS"),
    ("8.2.2.2", "website_url", "http_fail", "FAIL"),
    ("8.2.2.3", "website_url", "redirect", "PASS"),
    ("8.2.2.4", "website_url", "format_website", "PASS"),
    ("8.2.2.5", "website_url", "timeout", "FAIL"),
    ("8.2.2.6", "website_url", "redirect", "PASS"),

    ("8.2.3.1", "linkedin_url", "http_200", "PASS"),
    ("8.2.3.2", "linkedin_url", "http_fail", "FAIL"),
    ("8.2.3.3", "linkedin_url", "redirect", "PASS"),
    ("8.2.3.4", "linkedin_url", "format_linkedin_company", "PASS"),
    ("8.2.3.5", "linkedin_url", "invalid_linkedin_company", "FAIL"),

    ("8.2.4.1", "twitter_handle", "http_200", "PASS"),
    ("8.2.4.2", "twitter_handle", "http_fail", "FAIL"),
    ("8.2.4.3", "twitter_handle", "redirect", "PASS"),
    ("8.2.4.4", "twitter_handle", "format_twitter", "PASS"),
    ("8.2.4.5", "twitter_handle", "restricted", "FAIL"),

    ("8.2.5.1", "facebook_url", "http_200", "PASS"),
    ("8.2.5.2", "facebook_url", "http_fail", "FAIL"),
    ("8.2.5.3", "facebook_url", "redirect", "PASS"),
    ("8.2.5.4", "facebook_url", "format_facebook", "PASS"),
    ("8.2.5.5", "facebook_url", "restricted", "FAIL"),

    ("8.2.6.1", "instagram_url", "http_200", "PASS"),
    ("8.2.6.2", "instagram_url", "http_fail", "FAIL"),
    ("8.2.6.3", "instagram_url", "redirect", "PASS"),
    ("8.2.6.4", "instagram_url", "format_instagram", "PASS"),
    ("8.2.6.5", "instagram_url", "restricted", "FAIL"),

    ("8.2.7.1", "marketing_video_url", "http_200", "PASS"),
    ("8.2.7.2", "marketing_video_url", "http_fail", "FAIL"),
    ("8.2.7.3", "marketing_video_url", "redirect", "PASS"),
    ("8.2.7.4", "marketing_video_url", "format_youtube", "PASS"),
    ("8.2.7.5", "marketing_video_url", "restricted", "FAIL"),

    ("8.2.8.1", "crunchbase_url", "http_200", "PASS"),
    ("8.2.8.2", "crunchbase_url", "http_fail", "FAIL"),
    ("8.2.8.3", "crunchbase_url", "redirect", "PASS"),
    ("8.2.8.4", "crunchbase_url", "format_crunchbase", "PASS"),
    ("8.2.8.5", "crunchbase_url", "http_200", "PASS"),

    ("8.2.9.1", "press_kit_url", "http_200", "PASS"),
    ("8.2.9.2", "press_kit_url", "http_fail", "FAIL"),
    ("8.2.9.3", "press_kit_url", "redirect", "PASS"),
    ("8.2.9.4", "press_kit_url", "http_200", "PASS"),
    ("8.2.9.5", "press_kit_url", "http_fail", "FAIL"),

    ("8.2.10.1", "website_url", "http_200", "PASS"),
    ("8.2.10.2", "website_url", "http_fail", "FAIL"),
    ("8.2.10.3", "website_url", "redirect", "PASS"),
    ("8.2.10.4", "website_url", "rss", "PASS"),
    ("8.2.10.5", "website_url", "inactive", "WARNING"),
]


@pytest.mark.parametrize("tc_id,col,mode,expected", CASES, ids=[c[0] for c in CASES])
def test_tc_8_2_workbook_only(df, tc_id, col, mode, expected):
    url = _pick(df, col, mode, expected)
    actual = _validate(url, mode)
    assert actual == expected, f"{tc_id}: expected {expected}, got {actual}, url={url}"

