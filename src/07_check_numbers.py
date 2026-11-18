"""
07_check_numbers.py - Final QA: does every number in the documents match the analysis?

It collects every value in results/metrics.json and results/tables/*.csv
(rounded to 0, 1 and 2 decimals), then scans each document for numbers with a
decimal point or a thousands comma (for example 6.79 or 1,413) and lists any
number it cannot find. Plain whole numbers like 2018 or 300 are skipped because
they are years, thresholds or counts written in words.

Documents checked: README.md, every docs/*.md, docs/case_study.docx and the
visible text of dashboard/dashboard.html.

Run from the project root (last step):   python src/07_check_numbers.py
Exit code 0 = everything matched, 1 = at least one unexplained number.
"""

import json
import re
import sys
from pathlib import Path

import pandas as pd
from docx import Document

ROOT = Path(__file__).resolve().parent.parent

# Numbers that are allowed although they are not data results, with the reason
ALLOWED = {
    "94.5": "BRD target (proposal, labelled as such)",
    "12.2": "BRD target (proposal, labelled as such)",
    "7.0": "BRD target (proposal, labelled as such)",
    "0.0679": "Power BI rule: 6.79% written as a decimal",
    "0.9321": "Power BI constant line: 93.21% written as a decimal",
    "1.0": "document version number",
    "0.1": "NFR-03 reconciliation tolerance",
    "100.0": "SQL example: 100.0 forces decimal division",
    "0.20": "SQL example: top 20% cut-off",
    "3.10": "README: Python version",
    "4.0": "CC BY-NC-SA 4.0 licence version",
    "96,000": "60-second pitch: 96,203 rounded for speaking",
}

# docs/data_validation_report.md is not checked: 01_clean.py writes it directly from the
# data (monthly counts, null counts, row counts), so its numbers come from code by construction.
SKIP_DOCS = {"data_validation_report.md"}


# ---------------------------------------------------------------------------
# 1. Every value the analysis produced
# ---------------------------------------------------------------------------
known = set()


def add(value):
    """Store a number in the formats a document might use (0, 1, 2 decimals, with/without commas)."""
    if isinstance(value, bool):
        return
    if isinstance(value, (int, float)):
        for d in (0, 1, 2):
            known.add(f"{value:,.{d}f}")
            known.add(f"{value:.{d}f}")
    elif isinstance(value, dict):
        for v in value.values():
            add(v)
    elif isinstance(value, list):
        for v in value:
            add(v)


add(json.loads((ROOT / "results" / "metrics.json").read_text(encoding="utf-8")))
for csv in (ROOT / "results" / "tables").glob("*.csv"):
    for col in pd.read_csv(csv).select_dtypes("number").columns:
        for v in pd.read_csv(csv)[col].dropna():
            add(float(v))


# ---------------------------------------------------------------------------
# 2. Read each document as plain text
# ---------------------------------------------------------------------------
def read_docx(path):
    doc = Document(path)
    parts = [p.text for p in doc.paragraphs]
    for table in doc.tables:
        for row in table.rows:
            parts.extend(cell.text for cell in row.cells)
    return "\n".join(parts)


def read_html(path):
    html = path.read_text(encoding="utf-8")
    html = re.sub(r"<script.*?</script>", " ", html, flags=re.S)   # drop Plotly code and chart data
    html = re.sub(r"<style.*?</style>", " ", html, flags=re.S)
    return re.sub(r"<[^>]+>", " ", html)


documents = {"README.md": (ROOT / "README.md").read_text(encoding="utf-8")}
for md in sorted((ROOT / "docs").glob("*.md")):
    if md.name in SKIP_DOCS:
        continue
    text = md.read_text(encoding="utf-8")
    documents[f"docs/{md.name}"] = re.sub(r"```mermaid.*?```", " ", text, flags=re.S)
documents["docs/case_study.docx"] = read_docx(ROOT / "docs" / "case_study.docx")
documents["dashboard/dashboard.html"] = read_html(ROOT / "dashboard" / "dashboard.html")

# ---------------------------------------------------------------------------
# 3. Compare
# ---------------------------------------------------------------------------
NUMBER = re.compile(r"(?<![\w.,-])\d{1,3}(?:,\d{3})+(?:\.\d+)?(?![\w])|(?<![\w.,-])\d+\.\d+(?![\w.])")
problems = 0
print(f"{'Document':<32} {'numbers':>8}  unexplained")
for name, text in documents.items():
    found = set(NUMBER.findall(text))
    unexplained = sorted(n for n in found if n not in known and n not in ALLOWED)
    allowed_hits = sorted(n for n in found if n in ALLOWED)
    problems += len(unexplained)
    print(f"{name:<32} {len(found):>8}  {', '.join(unexplained) if unexplained else 'none'}"
          + (f"   (allowed: {', '.join(allowed_hits)})" if allowed_hits else ""))

print("\nAll numbers match results/metrics.json and results/tables." if problems == 0
      else f"\n{problems} number(s) need checking.")
sys.exit(0 if problems == 0 else 1)
