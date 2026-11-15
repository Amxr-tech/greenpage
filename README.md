# 🌱 greenpage

**Estimate and budget the carbon footprint of web pages, locally or in CI.**

[![CI](https://github.com/OWNER/greenpage/actions/workflows/ci.yml/badge.svg)](https://github.com/OWNER/greenpage/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen)

The internet accounts for an estimated 3–4% of global greenhouse gas emissions,
about the same as the aviation industry. Every byte a page sends uses energy in data
centres, networks and on the visitor's device. Teams already set **performance budgets**;
greenpage adds a **carbon budget** that stops pages from quietly getting heavier.

- 📏 **Measures** every page in a static build (`dist/`, `public/`, `_site/`) offline, or any live URL
- 🧮 **Estimates** grams of CO₂e per page view using the open [Sustainable Web Design Model v4](https://sustainablewebdesign.org/estimating-digital-emissions/)
- 🏷️ **Rates** each page A+ to F on the SWD digital carbon rating scale
- 🚦 **Enforces** a budget: exits non-zero when a page goes over, so CI fails
- 💡 **Suggests** fixes: oversized images, legacy font formats, autoplaying media, heavy JS
- 📦 **No dependencies**: pure Python standard library

## Install

```bash
pip install greenpage        # once published to PyPI
# or from source
pip install git+https://github.com/OWNER/greenpage
```

## Usage

```bash
# A whole static-site build
greenpage scan ./dist

# A single live page
greenpage scan https://example.com

# Fail if any page emits more than 0.2 g CO2e per view
greenpage scan ./dist --budget 0.2

# Site runs on renewable energy, 50k views/month: project yearly impact
greenpage scan ./dist --green-host --views 50000

# Machine-readable or PR-comment-ready output
greenpage scan ./dist --format json
greenpage scan ./dist --format markdown
```

Example output:

```
index.html
  150.5 kB transferred · 0.022 g CO2e/view · rating A+
  ≈ 2.68 kg CO2e/year at 10,000 views/month
  Heaviest resources:
     150.0 kB  image    assets/hero.png
        280 B  document index.html
  → assets/hero.png is 150 kB; serving it as AVIF or WebP typically saves 30-50%.
```

| Exit code | Meaning |
|---|---|
| `0` | All pages are within budget (or no budget set) |
| `1` | At least one page is over budget |
| `2` | Usage error, e.g. the target was not found |

## GitHub Action

```yaml
- uses: actions/checkout@v4
- run: npm ci && npm run build
- uses: OWNER/greenpage@v0
  with:
    target: dist
    budget: "0.2"
```

The action writes a Markdown report to the job summary and fails the job when a page is over budget.

## Python API

```python
from greenpage import estimate, scan_directory

for page in scan_directory("dist"):
    e = estimate(page.total_bytes, green_hosting=True)
    print(page.page, f"{e.grams_co2e:.3f} g", e.rating)
```

## Methodology

greenpage implements the **Sustainable Web Design Model v4**:

1. **Bytes.** Every resource a page references (HTML, CSS, JS, images, fonts, media, iframes) is counted.
   Text assets are measured gzip-compressed, which is how servers deliver them.
2. **Energy.** Bytes are converted to energy at 0.194 kWh/GB operational and 0.106 kWh/GB embodied,
   split across data centres, networks and user devices.
3. **Carbon.** Energy is multiplied by grid intensity: 494 gCO₂e/kWh global average by default, configurable
   with `--grid-intensity`. With `--green-host`, data-centre operational energy uses 50 gCO₂e/kWh.

All constants live in [`src/greenpage/model.py`](src/greenpage/model.py).

**Limitations.** These are estimates, not measurements. Local mode doesn't count resources loaded
at runtime by JavaScript, or external URLs (it flags them instead). The model assumes a first-time
visit with no caching. Use the numbers to compare pages and spot regressions, not as audited figures.

## Roadmap

- [ ] Count CSS `url()` references (background images, `@font-face`)
- [ ] Automatic green-host lookup via the Green Web Foundation API
- [ ] Headless-browser mode to capture runtime-loaded resources
- [ ] Per-country grid intensity presets
- [ ] Track history and chart trends across commits

Want to work on one of these? See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
