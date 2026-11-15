"""Actionable suggestions for reducing a page's footprint."""

from __future__ import annotations

from pathlib import PurePosixPath
from urllib.parse import urlparse

from .scan import PageScan

KB = 1000


def suggestions(scan: PageScan) -> list[str]:
    tips: list[str] = []
    by_kind: dict[str, int] = {}
    for r in scan.resources:
        by_kind[r.kind] = by_kind.get(r.kind, 0) + r.bytes

    for r in scan.resources:
        ext = PurePosixPath(urlparse(r.url).path).suffix.lower()
        if r.kind == "image" and ext in {".png", ".jpg", ".jpeg", ".gif"} and r.bytes > 100 * KB:
            tips.append(f"{r.url} is {r.bytes // KB} kB; serving it as AVIF or WebP typically saves 30-50%.")
        elif r.kind == "font" and ext in {".ttf", ".otf"}:
            tips.append(f"{r.url} uses {ext}; WOFF2 is much smaller and universally supported.")
        elif r.kind == "media" and r.bytes > 1000 * KB:
            tips.append(f"{r.url} is {r.bytes // KB} kB; use preload=\"none\" or a poster so it only loads on demand.")

    if by_kind.get("script", 0) > 300 * KB:
        tips.append(f"JavaScript totals {by_kind['script'] // KB} kB; consider code-splitting or removing unused libraries.")
    if by_kind.get("font", 0) > 150 * KB:
        tips.append(f"Web fonts total {by_kind['font'] // KB} kB; subset them or prefer system fonts.")
    return tips
