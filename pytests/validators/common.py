from pathlib import Path
import re


def extract_first_number(value):
    m = re.search(r"[-+]?\d[\d,]*(?:\.\d+)?", str(value))
    if not m:
        return None
    return float(m.group().replace(",", ""))


def pick_matching(series, predicate):
    for v in series.dropna().astype(str):
        s = v.strip()
        if s and predicate(s):
            return s
    return None


def assert_columns_exist(df, columns):
    missing = [c for c in columns if c not in df.columns]
    return missing


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]
