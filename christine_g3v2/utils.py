from __future__ import annotations

import hashlib
import math
import re
import urllib.parse
from typing import Iterable


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def tokens(text: str) -> set[str]:
    text = clean(text).casefold()
    out = set(re.findall(r"[a-z0-9_+\-]{2,}|[\u3400-\u9fff]{2,}", text))
    for block in re.findall(r"[\u3400-\u9fff]+", text):
        for n in (2, 3, 4):
            for i in range(max(0, len(block) - n + 1)):
                out.add(block[i:i+n])
    return out


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / max(1, len(a | b))


def prob_union(values: Iterable[float]) -> float:
    p_not = 1.0
    for v in values:
        p_not *= 1.0 - clamp01(v)
    return clamp01(1.0 - p_not)


def stable_id(*parts: str) -> str:
    h = hashlib.blake2b(digest_size=16)
    for part in parts:
        h.update(str(part).encode("utf-8", "replace"))
        h.update(b"\0")
    return h.hexdigest()


def host(url: str) -> str:
    try:
        return urllib.parse.urlparse(url).netloc.casefold().removeprefix("www.")
    except Exception:
        return ""


def semantic_normalize(text: str) -> str:
    s = clean(text).casefold()
    replacements = (
        ("一名", "一位"), ("大約", "約"), ("大概", "約"),
        ("而且", "並"), ("並且", "並"), ("目前的", "目前"),
        ("是一名", "是"), ("是一位", "是"), ("具有", "有"),
    )
    for a, b in replacements:
        s = s.replace(a, b)
    return re.sub(r"[，。！？、；：,.!?;:()（）\[\]「」『』\s]", "", s)


def hierarchy_counts(total_tokens: int, leaf_tokens: int = 1024, fanout: int = 64) -> tuple[int, ...]:
    counts = [math.ceil(total_tokens / leaf_tokens)]
    while counts[-1] > 1:
        counts.append(math.ceil(counts[-1] / fanout))
    return tuple(counts)
