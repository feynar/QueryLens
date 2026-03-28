"""
QueryLens — Correlation Accuracy Matrix Generator (Week 11)

Produces a rule-level correlation matrix showing how often
runtime execution plans confirm static analysis warnings.
"""

import os
import csv
import json

from src.analysis.static_analyzer import analyze_sql
from src.analysis.prototype_plan_analyzer import analyze_plan_file
from src.correlation.correlator import correlate


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PLAN_DIR = os.path.join(PROJECT_ROOT, "plans")
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "artifacts", "correlation_matrix.csv")


def find_plan_file(sql_path):
    base = os.path.splitext(sql_path)[0]
    plan_path = base + ".sqlplan"
    return plan_path if os.path.exists(plan_path) else None


def collect_correlations():
    rows = []

    for file in os.listdir(PLAN_DIR):
        if not file.endswith(".sql"):
            continue

        sql_path = os.path.join(PLAN_DIR, file)
        plan_path = find_plan_file(sql_path)

        static_findings = analyze_sql(sql_path)
        runtime_findings = analyze_plan_file(plan_path) if plan_path else []

        correlations = correlate(static_findings, runtime_findings)

        rows.extend(correlations)

    return rows


def aggregate_by_rule(correlations):
    stats = {}

    for c in correlations:
        rule = c["rule"]

        if rule not in stats:
            stats[rule] = {
                "rule": rule,
                "total": 0,
                "confirmed": 0
            }

        stats[rule]["total"] += 1
        if c["confirmed"]:
            stats[rule]["confirmed"] += 1

    for rule in stats.values():
        total = rule["total"]
        confirmed = rule["confirmed"]
        rule["confirmation_rate"] = round(confirmed / total, 3) if total else 0

    return list(stats.values())


def save_csv(rows):
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    with open(OUTPUT_PATH, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["rule", "total", "confirmed", "confirmation_rate"]
        )
        writer.writeheader()
        writer.writerows(rows)

    print("✔ Correlation matrix saved")
    print(f"→ {OUTPUT_PATH}")


def generate_matrix():
    correlations = collect_correlations()
    aggregated = aggregate_by_rule(correlations)
    save_csv(aggregated)


if __name__ == "__main__":
    generate_matrix()