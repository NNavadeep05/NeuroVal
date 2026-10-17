"""
Static HTML validation report.
"""

import html
import math
from pathlib import Path

from neuroval.validation.comparison import PASS_THRESHOLD


STYLE = """
body { font-family: sans-serif; margin: 24px; color: #222; }
table { border-collapse: collapse; margin-bottom: 16px; }
th, td { border: 1px solid #ccc; padding: 4px 8px; text-align: right; }
th:first-child, td:first-child { text-align: left; }
.fail { color: #b00020; }
img { max-width: 100%; }
"""


def write_html(
    file_path: Path,
    protocols: dict,
    summary: dict,
    metadata: dict,
) -> None:
    """Write a self-contained HTML report next to the plots/ folder."""

    parts = [
        "<!doctype html>",
        "<html><head><meta charset='utf-8'>",
        "<title>NeuroVal Report</title>",
        f"<style>{STYLE}</style></head><body>",
        "<h1>NeuroVal Validation Report</h1>",
        _metadata_table(metadata),
        "<h2>Summary</h2>",
        _summary_table(summary),
        "<h2>Features</h2>",
    ]

    for name, result in protocols.items():
        parts.append(f"<h3>{html.escape(name)}</h3>")

        if "error" in result:
            parts.append(
                f"<p class='fail'>Simulation failed: {html.escape(result['error'])}</p>"
            )
        parts.append(_feature_table(result["comparison"]))

    parts += [
        "<h2>z-scores</h2>",
        "<img src='plots/z_scores.png' alt='z-scores per feature'>",
        "<h2>Voltage traces</h2>",
        "<img src='plots/traces.png' alt='voltage traces'>",
        "</body></html>",
    ]

    Path(file_path).write_text("\n".join(parts), encoding="utf-8")


def _metadata_table(metadata: dict) -> str:
    if not metadata:
        return ""

    rows = "".join(
        f"<tr><td>{html.escape(str(key))}</td><td>{html.escape(str(value))}</td></tr>"
        for key, value in metadata.items()
    )
    return f"<table>{rows}</table>"


def _summary_table(summary: dict) -> str:
    passed = summary["passed"]
    verdict = "Passed" if passed else "Failed"
    css = "" if passed else " class='fail'"
    problems = ", ".join(summary["problem_features"]) or "none"

    rows = [
        ("Mean |z|", _number(summary["mean_abs_z"])),
        ("Max z", _number(summary["max_z"])),
        (f"Max z &lt; {PASS_THRESHOLD}", f"<span{css}>{verdict}</span>"),
        ("Problem features", html.escape(problems)),
    ]
    body = "".join(f"<tr><td>{label}</td><td>{value}</td></tr>" for label, value in rows)
    return f"<table>{body}</table>"


def _feature_table(comparison: dict) -> str:
    header = (
        "<tr><th>Feature</th><th>Exp. mean</th><th>Exp. std</th>"
        "<th>Model</th><th>z</th><th>Status</th></tr>"
    )
    rows = []

    for feature, values in comparison.items():
        z_score = values["z_score"]
        css = "" if math.isfinite(z_score) and z_score < PASS_THRESHOLD else " class='fail'"
        rows.append(
            f"<tr{css}><td>{html.escape(feature)}</td>"
            f"<td>{_number(values['experimental_mean'])}</td>"
            f"<td>{_number(values['experimental_std'])}</td>"
            f"<td>{_number(values['simulated'])}</td>"
            f"<td>{_number(z_score)}</td>"
            f"<td>{html.escape(values['status'])}</td></tr>"
        )

    return f"<table>{header}{''.join(rows)}</table>"


def _number(value) -> str:
    if value is None:
        return "none"

    if not math.isfinite(value):
        return "inf" if value > 0 else "nan"

    return f"{value:.3f}"
