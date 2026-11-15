# Changelog

All notable changes to this project are documented here, following [Keep a Changelog](https://keepachangelog.com/).

## [0.1.1] - 2026-11-15

### Fixed
- Green hosting now follows SWD v4: data-centre operational emissions are scaled by
  `1 - green hosting factor` instead of using a 50 g/kWh renewable intensity (a v3 carry-over).

### Added
- `green_hosting_factor` parameter (0–1) in the Python API.
- Release workflow that publishes to PyPI via Trusted Publishing.

## [0.1.0] - 2026-11-15

### Added
- `greenpage scan` for HTML files, static build directories and live URLs.
- Sustainable Web Design Model v4 carbon estimates with A+–F ratings.
- `--budget` option with CI-friendly exit codes.
- Text, JSON and Markdown output formats.
- Optimisation suggestions for images, fonts, media and JavaScript.
- Composite GitHub Action.
