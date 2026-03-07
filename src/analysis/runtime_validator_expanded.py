"""
QueryLens Expanded Runtime Validation Evaluator (Week 14)

Runs runtime validation on the 20-query expanded workload.
"""

import os
import json

from src.analysis.static_analyzer import analyze_sql
from src.analysis.prototype_plan_analyzer import parse_plan
from src.correlation.correlator import correlate

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

PLAN_DIR = os.path.join(PROJECT_ROOT, "plans_expanded")
OUTPUT_PATH = os.path.join(
    PROJECT_ROOT,
    "artifacts",
    "eval",
    "expanded_runtime_report.json"
)


def find_plan_file(sql_path):
    base = os.path.splitext(sql_path)[0]
    plan_path = base + ".sqlplan"
    return plan_path if os.path.exists(plan_path) else None


def evaluate_query(sql_path):
    sql_name = os.path.basename(sql_path)

    static_findings = analyze_sql(sql_path)

    plan_path = find_plan_file(sql_path)
    if plan_path:
        print(f"Parsing plan: {plan_path}")
        runtime_findings = parse_plan(plan_path)
    else:
        runtime_findings = []

    correlations = correlate(static_findings, runtime_findings)
    confirmed = [c for c in correlations if c["confirmed"]]

    static_count = len(static_findings)
    confirmed_count = len(confirmed)

    rate = confirmed_count / static_count if static_count else 0

    return {
        "query": sql_name,
        "static_warnings": static_count,
        "confirmed_warnings": confirmed_count,
        "confirmation_rate": round(rate, 3)
    }


def compute_global_metrics(rows):
    total_static = sum(r["static_warnings"] for r in rows)
    total_confirmed = sum(r["confirmed_warnings"] for r in rows)

    rate = total_confirmed / total_static if total_static else 0

    return {
        "total_static_warnings": total_static,
        "total_confirmed_warnings": total_confirmed,
        "confirmation_rate": round(rate, 3)
    }


def run_evaluation():
    results = []

    for file in os.listdir(PLAN_DIR):
        if file.endswith(".sql"):
            sql_path = os.path.join(PLAN_DIR, file)
            results.append(evaluate_query(sql_path))

    metrics = compute_global_metrics(results)

    report = {
        "per_query_results": results,
        "global_metrics": metrics
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    with open(OUTPUT_PATH, "w") as f:
        json.dump(report, f, indent=4)

    print("? Expanded runtime validation complete")
    print(json.dumps(metrics, indent=4))


if __name__ == "__main__":
    run_evaluation()