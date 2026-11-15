# Contributing to greenpage

Thanks for helping make the web lighter! All contributions are welcome: code, docs, bug reports and methodology reviews.

## Development setup

```bash
git clone https://github.com/OWNER/greenpage && cd greenpage
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
pytest
ruff check .
```

## Guidelines

- **No runtime dependencies.** greenpage uses only the standard library so it installs anywhere, including CI.
- **Tests required.** Every behaviour change needs a test. Local-mode tests use `tests/fixtures/site`; avoid network calls in tests.
- **Methodology changes** (anything in `model.py`) must cite a source in the PR description.
- Keep pull requests focused. Open an issue first for large changes.

## Good first issues

Look for the `good first issue` label, or pick an item from the README roadmap.

## Code of Conduct

By participating you agree to follow our [Code of Conduct](CODE_OF_CONDUCT.md).
