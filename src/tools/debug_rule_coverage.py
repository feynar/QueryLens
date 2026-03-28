"""
QueryLens Debug Tool

Prints a table showing which rules were detected for each query.
Useful for verifying workload coverage.
"""

import os

from src.analysis.static_analyzer import analyze_sql
from src.correlation.correlator import normalize_static


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
QUERY_DIR = os.path.join(PROJECT_ROOT, "plans")


def run_debug():

    print("\nQUERY RULE COVERAGE\n")
    print(f"{'QUERY':40} RULES DETECTED")
    print("-" * 65)

    for file in sorted(os.listdir(QUERY_DIR)):

        if not file.endswith(".sql"):
            continue

        path = os.path.join(QUERY_DIR, file)

        findings = analyze_sql(path)
        rules = [normalize_static(f) for f in findings]

        if rules:
            rule_string = ", ".join(rules)
        else:
            rule_string = "-"

        print(f"{file:40} {rule_string}")


if __name__ == "__main__":
    run_debug()