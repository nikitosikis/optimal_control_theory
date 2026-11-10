"""Rebuild the LaTeX report. Run MATLAB first, then python build_report.py.

Requires Python 3 and pdflatex. No Python packages.
Use --source-only to update tables without compiling.
"""
from pathlib import Path
import csv
import json
import re
import shutil
import subprocess
import sys

BASE = Path(__file__).resolve().parent
SOURCE = BASE / "report.tex"
RESULTS = BASE / "results"


def iteration_rows(filename):
    with (RESULTS / filename).open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    lines = []
    d = "$"
    for r in rows:
        k = int(float(r["k"]))
        x, u, j, norm = [float(r[key]) for key in ("x", "u", "J", "grad_norm")]
        mantissa, exponent = f"{norm:.6e}".split("e")
        norm_tex = rf"{mantissa}\cdot10^{{{int(exponent)}}}" if norm else "0"
        lines.append(rf"{k} & {d}{x:.9f}{d} & {d}{u:.9f}{d} & {d}{j:.12f}{d} & {d}{norm_tex}{d} \\")
    return "\n".join(lines)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    result = json.loads((RESULTS / "results.json").read_text(encoding="utf-8"))
    if not result.get("all_checks_passed") or result["variant"] != 11:
        raise RuntimeError("Run and verify lab1_variant11.m first.")
    source = SOURCE.read_text(encoding="utf-8")
    for label, filename in [("NEWTON", "newton.csv"), ("AP", "descent_005.csv"),
                            ("OSC", "descent_009.csv")]:
        pattern = rf"(% BEGIN {label}\n).*?(% END {label})"
        source, count = re.subn(
            pattern, lambda m: m[1] + iteration_rows(filename) + "\n" + m[2],
            source, flags=re.S)
        if count != 1:
            raise RuntimeError(f"Expected one generated table: {label}")
    SOURCE.write_text(source, encoding="utf-8")
    if "--source-only" in sys.argv:
        print(SOURCE)
        return
    compiler = shutil.which("pdflatex")
    if compiler is None:
        raise FileNotFoundError("pdflatex is not on PATH. Install TeX Live or MiKTeX.")
    build = RESULTS / "tex_build"
    build.mkdir(parents=True, exist_ok=True)
    command = [compiler, "-disable-installer", "-interaction=nonstopmode",
               "-halt-on-error", "-file-line-error",
               f"-output-directory={build}", SOURCE.name]
    for attempt in range(2):
        completed = subprocess.run(command, cwd=BASE, capture_output=True, timeout=120)
        log = completed.stdout + completed.stderr
        (build / f"run-{attempt+1}.txt").write_bytes(log)
        if completed.returncode:
            print(log.decode("utf-8", errors="replace")[-10000:])
            raise RuntimeError(f"LaTeX failed; see {build}")
    target = BASE / "Лабораторная_1_Вариант_11.pdf"
    shutil.copy2(build / "report.pdf", target)
    print(target)


if __name__ == "__main__":
    main()
