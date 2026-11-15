"""Discover a page's resources and measure their transfer size.

Works on local build output (e.g. ``dist/``) without any network access,
or on live URLs using only the standard library.
"""

from __future__ import annotations

import gzip
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

USER_AGENT = "greenpage (+https://github.com/greenpage-dev/greenpage)"
TIMEOUT = 15

_LINK_RELS = {"stylesheet", "icon", "preload", "modulepreload", "manifest", "apple-touch-icon"}


@dataclass
class Resource:
    url: str
    bytes: int
    kind: str
    error: str | None = None


@dataclass
class PageScan:
    page: str
    resources: list[Resource] = field(default_factory=list)

    @property
    def total_bytes(self) -> int:
        return sum(r.bytes for r in self.resources)

    @property
    def errors(self) -> list[Resource]:
        return [r for r in self.resources if r.error]


class _ResourceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.refs: list[tuple[str, str]] = []

    def _add(self, url: str | None, kind: str) -> None:
        if url and not url.startswith(("data:", "javascript:", "#", "mailto:")):
            self.refs.append((url.strip(), kind))

    def _add_srcset(self, srcset: str | None, kind: str) -> None:
        # Browsers fetch one candidate; count the first as a fair approximation.
        if srcset:
            self._add(srcset.split(",")[0].strip().split(" ")[0], kind)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        if tag == "script":
            self._add(a.get("src"), "script")
        elif tag == "link":
            rels = set((a.get("rel") or "").lower().split())
            if rels & _LINK_RELS:
                kind = "style" if "stylesheet" in rels else _kind_from_ext(a.get("href") or "")
                self._add(a.get("href"), kind)
        elif tag == "img":
            if a.get("src"):
                self._add(a.get("src"), "image")
            else:
                self._add_srcset(a.get("srcset"), "image")
        elif tag == "source":
            if a.get("src"):
                self._add(a.get("src"), "media")
            else:
                self._add_srcset(a.get("srcset"), "image")
        elif tag in ("video", "audio"):
            self._add(a.get("poster"), "image")
            if a.get("preload") != "none":
                self._add(a.get("src"), "media")
        elif tag in ("iframe", "embed"):
            self._add(a.get("src"), "document")


def extract_resources(html: str) -> list[tuple[str, str]]:
    """Return de-duplicated ``(url, kind)`` pairs referenced by ``html``."""
    parser = _ResourceParser()
    parser.feed(html)
    seen: set[str] = set()
    unique = []
    for url, kind in parser.refs:
        if url not in seen:
            seen.add(url)
            unique.append((url, kind))
    return unique


def _kind_from_ext(url: str) -> str:
    ext = Path(urlparse(url).path).suffix.lower()
    if ext in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif", ".svg", ".ico"}:
        return "image"
    if ext in {".woff", ".woff2", ".ttf", ".otf", ".eot"}:
        return "font"
    if ext in {".js", ".mjs"}:
        return "script"
    if ext == ".css":
        return "style"
    if ext in {".mp4", ".webm", ".mp3", ".ogg"}:
        return "media"
    return "other"


def _gzip_size(data: bytes) -> int:
    """Approximate transfer size for text assets, which servers compress."""
    return len(gzip.compress(data, compresslevel=6))


_COMPRESSIBLE = {".html", ".htm", ".css", ".js", ".mjs", ".svg", ".json", ".txt", ".xml"}


def _local_size(path: Path) -> int:
    data = path.read_bytes()
    return _gzip_size(data) if path.suffix.lower() in _COMPRESSIBLE else len(data)


def scan_file(html_path: Path, site_root: Path) -> PageScan:
    """Scan a local HTML file, resolving resources relative to ``site_root``."""
    html_path = html_path.resolve()
    site_root = site_root.resolve()
    scan = PageScan(page=str(html_path.relative_to(site_root)))
    scan.resources.append(Resource(scan.page, _local_size(html_path), "document"))
    counted: set[Path] = {html_path}

    for ref, kind in extract_resources(html_path.read_text(encoding="utf-8", errors="replace")):
        parsed = urlparse(ref)
        if parsed.scheme in ("http", "https") or ref.startswith("//"):
            scan.resources.append(Resource(ref, 0, kind, "external (use URL mode to measure)"))
            continue
        rel = unquote(parsed.path)
        target = (site_root / rel.lstrip("/")) if rel.startswith("/") else (html_path.parent / rel)
        target = target.resolve()
        if not target.is_relative_to(site_root) or not target.is_file():
            scan.resources.append(Resource(ref, 0, kind, "not found"))
            continue
        if target in counted:  # same file referenced via a different path
            continue
        counted.add(target)
        scan.resources.append(Resource(ref, _local_size(target), kind if kind != "other" else _kind_from_ext(ref)))
    return scan


def scan_directory(root: Path) -> list[PageScan]:
    root = root.resolve()
    pages = sorted(p for p in root.rglob("*") if p.suffix.lower() in (".html", ".htm") and p.is_file())
    return [scan_file(p, root) for p in pages]


def _fetch(url: str) -> tuple[bytes, int, str]:
    """Fetch ``url`` and return (body, bytes on the wire, content type)."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Encoding": "gzip"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:  # noqa: S310 - user-supplied http(s) URL
        raw = resp.read()
        ctype = resp.headers.get("Content-Type", "")
        if resp.headers.get("Content-Encoding") == "gzip":
            return gzip.decompress(raw), len(raw), ctype
        return raw, len(raw), ctype


def scan_url(url: str) -> PageScan:
    """Scan a live page over HTTP(S)."""
    if urlparse(url).scheme not in ("http", "https"):
        raise ValueError(f"unsupported URL scheme: {url}")
    body, wire, _ = _fetch(url)
    scan = PageScan(page=url)
    scan.resources.append(Resource(url, wire, "document"))
    for ref, kind in extract_resources(body.decode("utf-8", errors="replace")):
        absolute = urljoin(url, ref)
        if urlparse(absolute).scheme not in ("http", "https"):
            continue
        try:
            _, size, ctype = _fetch(absolute)
            if kind == "other":
                kind = _kind_from_ext(absolute)
            scan.resources.append(Resource(absolute, size, kind))
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            scan.resources.append(Resource(absolute, 0, kind, str(exc)))
    return scan
