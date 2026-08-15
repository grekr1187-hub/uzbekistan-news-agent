from __future__ import annotations

import re
from urllib.parse import urlsplit, urlunsplit


def canonical_url(url: str) -> str:
    p = urlsplit(url.strip())
    return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path.rstrip("/"), "", ""))


def _tokens(text: str) -> set[str]:
    return {x for x in re.findall(r"[\w\u0400-\u04ff\u0500-\u052f]+", text.lower()) if len(x) > 2}


def is_duplicate(title: str, url: str, recent_titles: list[str]) -> bool:
    normalized = canonical_url(url)
    if any(normalized == canonical_url(t) for t in recent_titles if t.startswith("http")):
        return True
    tokens = _tokens(title)
    if not tokens:
        return False
    return any(len(tokens & _tokens(old)) / len(tokens | _tokens(old) or {"_"}) >= 0.72 for old in recent_titles)
