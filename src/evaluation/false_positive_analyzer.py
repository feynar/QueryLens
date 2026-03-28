# src/analysis/false_positive_analyzer.py

"""
QueryLens — False Positive Diagnostic Tool (Week 12)

Generates an explanatory report for static warnings that were not
confirmed by execution plan evidence.
"""

import os
from src.analysis.static_analyzer import analyze_sql
from src.analysis.prototype_plan_analyzer import parse_plan
from src.correlation.correlator import correlate

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PLAN_DIR = os.path.join(PROJECT_ROOT, "plans")
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "artifacts", "analysis", "validation_log.txt")


def find_plan(sql_path):
    base = os.path.splitext(sql_path)[0]
    plan_path = base + ".sqlplan"
    return plan_path if os.path.exists(plan_path) else None


def analyze_query(sql_path):
    static_findings = analyze_sql(sql_path)

    plan_path = find_plan(sql_path)
    runtime_findings = parse_plan(plan_path) if plan_path else []

    correlations = correlate(static_findings, runtime_findings)

    unconfirmed = [c for c in correlations if not c["confirmed"]]

    return unconfirmed


def run_analysis():
    lines = []
    lines.append("QueryLens False Positive Analysis")
    lines.append("================================\n")

    total_static = 0
    total_false_positives = 0

    for file in os.listdir(PLAN_DIR):
        if not file.endswith(".sql"):
            continue

        sql_path = os.path.join(PLAN_DIR, file)

        # count static warnings for summary stats
        static_findings = analyze_sql(sql_path)
        total_static += len(static_findings)

        unconfirmed = analyze_query(sql_path)

        if not unconfirmed:
            continue

        total_false_positives += len(unconfirmed)

        lines.append(f"Query: {file}")

        for item in unconfirmed:
            lines.append(f"  Rule: {item['rule']}")
            lines.append(f"  Confidence: {item['confidence']}")
            lines.append(f"  Evidence: {item['evidence']}")
            lines.append(f"  Reason: {item['reason']}\n")

    # ---- Always write summary ----
    lines.append("\nSummary")
    lines.append("-------")
    lines.append(f"Total static warnings evaluated: {total_static}")
    lines.append(f"False positives detected: {total_false_positives}\n")

    if total_false_positives == 0:
        lines.append("No false positives observed. All warnings supported by runtime evidence.")

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    with open(OUTPUT_PATH, "w") as f:
        f.write("\n".join(lines))

    print("✔ False positive analysis complete")


if __name__ == "__main__":
    run_analysis()