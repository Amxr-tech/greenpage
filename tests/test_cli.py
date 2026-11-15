import json
from pathlib import Path

from greenpage.cli import main

SITE = str(Path(__file__).parent / "fixtures" / "site")


def test_text_output(capsys):
    assert main(["scan", SITE]) == 0
    out = capsys.readouterr().out
    assert "index.html" in out and "g CO2e/view" in out


def test_budget_failure_exit_code(capsys):
    assert main(["scan", SITE, "--budget", "0.0001"]) == 1
    assert "OVER BUDGET" in capsys.readouterr().out


def test_budget_pass(capsys):
    assert main(["scan", SITE, "--budget", "10"]) == 0


def test_json_output(capsys):
    main(["scan", SITE, "--format", "json", "--views", "10000"])
    data = json.loads(capsys.readouterr().out)
    assert {d["page"] for d in data} == {"index.html", "about/index.html"}
    assert all(d["yearly_kg_co2e"] is not None for d in data)


def test_markdown_output(capsys):
    main(["scan", SITE, "--format", "markdown", "--budget", "1"])
    out = capsys.readouterr().out
    assert out.startswith("## 🌱 greenpage carbon report")
    assert "| `index.html` |" in out


def test_suggestion_for_large_png(capsys):
    main(["scan", SITE])
    assert "AVIF or WebP" in capsys.readouterr().out


def test_missing_target(capsys):
    assert main(["scan", "/definitely/not/here"]) == 2
