from pathlib import Path

from greenpage.scan import extract_resources, scan_directory, scan_file

SITE = Path(__file__).parent / "fixtures" / "site"


def test_extract_resources_skips_data_uris_and_dedupes():
    html = '<img src="a.png"><img src="a.png"><img src="data:x"><script src="b.js"></script>'
    assert extract_resources(html) == [("a.png", "image"), ("b.js", "script")]


def test_extract_srcset_takes_first_candidate():
    assert extract_resources('<img srcset="small.webp 480w, big.webp 1200w">') == [("small.webp", "image")]


def test_ignores_non_resource_links():
    assert extract_resources('<link rel="canonical" href="/x"><a href="y.html">y</a>') == []


def test_scan_file_measures_local_assets():
    scan = scan_file(SITE / "index.html", SITE)
    by_url = {r.url: r for r in scan.resources}
    assert by_url["assets/hero.png"].bytes == 150_000
    assert by_url["assets/hero.png"].kind == "image"
    # Text assets are measured gzip-compressed, so they shrink.
    css = SITE / "assets" / "style.css"
    assert 0 < by_url["assets/style.css"].bytes < css.stat().st_size
    assert by_url["/assets/logo.svg"].bytes > 0
    assert by_url["assets/missing.jpg"].error == "not found"
    assert "external" in by_url["https://cdn.example.com/lib.js"].error


def test_scan_does_not_escape_site_root():
    scan = scan_file(SITE / "about" / "index.html", SITE)
    escaped = [r for r in scan.resources if "secret" in r.url]
    assert escaped and escaped[0].error == "not found" and escaped[0].bytes == 0


def test_scan_directory_finds_all_pages():
    pages = [s.page for s in scan_directory(SITE)]
    assert pages == ["about/index.html", "index.html"]


def test_same_file_via_different_paths_counted_once():
    scan = scan_file(SITE / "index.html", SITE)
    svg_hits = [r for r in scan.resources if r.url.endswith("logo.svg")]
    assert len(svg_hits) == 1
