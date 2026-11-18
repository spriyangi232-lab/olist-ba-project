"""
run_all.py - Rebuild the whole project with one command:   python run_all.py

What it does:
  1. Installs any missing Python packages from requirements.txt.
  2. Runs every script in src/ in order (clean -> SQL -> impact -> charts ->
     dashboard -> case study -> number check).
  3. Re-runs the notebook so its saved outputs match the new results.
  4. Prints where to find each output.

The raw data is already in data/raw, so nothing needs to be downloaded.
"""

import importlib.util
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Package name used by pip -> module name used by import
PACKAGES = {
    "pandas": "pandas",
    "numpy": "numpy",
    "matplotlib": "matplotlib",
    "plotly": "plotly",
    "python-docx": "docx",
    "nbformat": "nbformat",
    "nbconvert": "nbconvert",
    "ipykernel": "ipykernel",
}

STEPS = [
    ("01_clean.py", "Load, clean and validate data; build SQLite database"),
    ("02_run_sql.py", "Run 15 SQL business queries; write metrics.json"),
    ("03_impact.py", "Impact estimate (conservative / expected)"),
    ("04_charts.py", "10 report charts"),
    ("05_dashboard.py", "Interactive dashboard"),
    ("06_case_study.py", "Case study Word + PDF"),
    ("07_website.py", "Project website (index.html)"),
    ("08_check_numbers.py", "QA: check every number in the documents"),
]


def install_missing_packages():
    missing = [pip_name for pip_name, module in PACKAGES.items() if importlib.util.find_spec(module) is None]
    if sys.platform == "win32" and importlib.util.find_spec("docx2pdf") is None:
        missing.append("docx2pdf")          # PDF export via Microsoft Word (Windows only)
    if missing:
        print(f"Installing missing packages: {', '.join(missing)}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", *missing])
    else:
        print("All required packages are installed.")


def run_notebook():
    """Execute notebooks/analysis.ipynb in place so its outputs are up to date."""
    import nbformat
    from nbconvert.preprocessors import ExecutePreprocessor

    path = ROOT / "notebooks" / "analysis.ipynb"
    nb = nbformat.read(path, as_version=4)
    ExecutePreprocessor(timeout=300, kernel_name="python3").preprocess(
        nb, {"metadata": {"path": str(path.parent)}})
    nbformat.write(nb, path)


def main():
    sys.stdout.reconfigure(line_buffering=True)   # print progress in order with the scripts' own output
    if not (ROOT / "data" / "raw" / "olist_orders_dataset.csv").exists():
        sys.exit("data/raw is missing the Olist CSVs. See data/README.md.")

    print("=" * 70)
    print("Olist delivery delay case study - full rebuild")
    print("=" * 70)
    install_missing_packages()

    for i, (script, label) in enumerate(STEPS, start=1):
        print(f"\n[{i}/{len(STEPS) + 1}] {label}  (src/{script})")
        start = time.time()
        result = subprocess.run([sys.executable, str(ROOT / "src" / script)], cwd=ROOT)
        if result.returncode != 0:
            sys.exit(f"\nStopped: src/{script} failed (exit code {result.returncode}).")
        print(f"      done in {time.time() - start:.0f}s")

    print(f"\n[{len(STEPS) + 1}/{len(STEPS) + 1}] Re-run the notebook (notebooks/analysis.ipynb)")
    try:
        run_notebook()
        print("      done")
    except Exception as err:      # the analysis itself is complete even if Jupyter is unavailable
        print(f"      skipped ({err})")

    print("\n" + "=" * 70)
    print("Finished. Open these:")
    print("  Website (all outputs)   index.html")
    print("  Dashboard               dashboard/dashboard.html")
    print("  Case study              docs/case_study.pdf")
    print("  Headline numbers        results/metrics.json")
    print("=" * 70)


if __name__ == "__main__":
    main()
