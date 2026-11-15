"""Command-line interface: ``greenpage scan <path-or-url>``."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .advice import suggestions
from .model import GLOBAL_GRID_INTENSITY, estimate
from .scan import PageScan, scan_directory, scan_file, scan_url


def _human(n: int) -> str:
    for unit in ("B", "kB", "MB"):
        if n < 1000:
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1000
    return f"{n:.1f} GB"


def _grams(g: float) -> str:
    return "<0.001" if 0 < g < 0.001 else f"{g:.3f}"


def _collect(target: str) -> list[PageScan]:
    if target.startswith(("http://", "https://")):
        return [scan_url(target)]
    path = Path(target)
    if path.is_dir():
        return scan_directory(path)
    if path.is_file():
        return [scan_file(path, path.parent)]
    raise FileNotFoundError(f"no such file, directory or URL: {target}")


def _results(scans: list[PageScan], args: argparse.Namespace) -> list[dict]:
    out = []
    for s in scans:
        est = estimate(s.total_bytes, green_hosting=args.green_host, grid_intensity=args.grid_intensity)
        out.append({
            "page": s.page,
            "bytes": s.total_bytes,
            "grams_co2e": round(est.grams_co2e, 6),
            "rating": est.rating,
            "over_budget": args.budget is not None and est.grams_co2e > args.budget,
            "yearly_kg_co2e": round(est.grams_co2e * args.views * 12 / 1000, 2) if args.views else None,
            "resources": [
                {"url": r.url, "kind": r.kind, "bytes": r.bytes, **({"error": r.error} if r.error else {})}
                for r in sorted(s.resources, key=lambda r: -r.bytes)
            ],
            "suggestions": suggestions(s),
        })
    return out


def _print_text(results: list[dict], args: argparse.Namespace) -> None:
    for r in results:
        flag = "  OVER BUDGET" if r["over_budget"] else ""
        print(f"\n{r['page']}")
        print(f"  {_human(r['bytes'])} transferred · {_grams(r['grams_co2e'])} g CO2e/view · rating {r['rating']}{flag}")
        if r["yearly_kg_co2e"] is not None:
            print(f"  ≈ {r['yearly_kg_co2e']} kg CO2e/year at {args.views:,} views/month")
        heaviest = [x for x in r["resources"] if x["bytes"]][: args.top]
        if heaviest:
            print("  Heaviest resources:")
            for x in heaviest:
                print(f"    {_human(x['bytes']):>9}  {x['kind']:<8} {x['url']}")
        for x in r["resources"]:
            if "error" in x:
                print(f"    {'?':>9}  {x['kind']:<8} {x['url']} ({x['error']})")
        for tip in r["suggestions"]:
            print(f"  → {tip}")


def _print_markdown(results: list[dict], args: argparse.Namespace) -> None:
    print("## 🌱 greenpage carbon report\n")
    if args.budget is not None:
        print(f"Budget: **{args.budget} g CO2e** per page view\n")
    print("| Page | Size | g CO2e/view | Rating | Status |")
    print("|---|---:|---:|:---:|:---:|")
    for r in results:
        status = "❌ over" if r["over_budget"] else "✅"
        print(f"| `{r['page']}` | {_human(r['bytes'])} | {_grams(r['grams_co2e'])} | {r['rating']} | {status} |")
    tips = [t for r in results for t in r["suggestions"]]
    if tips:
        print("\n<details><summary>Suggestions</summary>\n")
        for t in dict.fromkeys(tips):
            print(f"- {t}")
        print("\n</details>")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="greenpage", description="Estimate and budget the carbon footprint of web pages.")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("scan", help="scan an HTML file, a build directory, or a URL")
    s.add_argument("target", help="path to an .html file, a site build directory, or an http(s) URL")
    s.add_argument("--budget", type=float, help="fail (exit 1) if any page exceeds this many grams CO2e per view")
    s.add_argument("--green-host", action="store_true", help="site is hosted on renewable energy")
    s.add_argument("--grid-intensity", type=float, default=GLOBAL_GRID_INTENSITY,
                   help=f"grid carbon intensity in gCO2e/kWh (default: global average {GLOBAL_GRID_INTENSITY})")
    s.add_argument("--views", type=int, help="monthly page views, to project yearly emissions")
    s.add_argument("--top", type=int, default=5, help="number of heaviest resources to list (default: 5)")
    s.add_argument("--format", choices=("text", "json", "markdown"), default="text")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        scans = _collect(args.target)
    except (OSError, ValueError) as exc:
        print(f"greenpage: error: {exc}", file=sys.stderr)
        return 2
    if not scans:
        print(f"greenpage: error: no HTML pages found in {args.target}", file=sys.stderr)
        return 2

    results = _results(scans, args)
    if args.format == "json":
        print(json.dumps(results, indent=2))
    elif args.format == "markdown":
        _print_markdown(results, args)
    else:
        _print_text(results, args)

    return 1 if any(r["over_budget"] for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
