"""
QueryLens — Runtime Validation Evaluator (Week 10)

Evaluates whether detected SQL anti-patterns
are confirmed by execution plan evidence.

Dataset:
Runtime workload = plans/
"""

import os
import json

from src.analysis.static_analyzer import analyze_sql
from src.analysis.plan_analyzer import parse_plan
from src.correlation.correlator import correlate


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

RUNTIME_WORKLOAD_DIR = os.path.join(PROJECT_ROOT, "plans")

OUTPUT_PATH = os.path.join(PROJECT_ROOT, "artifacts", "evaluation", "full_pipeline_report.json")

def evaluate_query(sql_path):
    static_findings = analyze_sql(sql_path)
    plan_path = sql_path.replace(".sql", ".sqlplan")

    runtime_findings = parse_plan(plan_path) if os.path.exists(plan_path) else []

    correlations = correlate(static_findings, runtime_findings)

    confirmed = [c for c in correlations if c["confirmed"]]
    high_conf = [c for c in confirmed if c["confidence"] == "high"]

    return {
        "query": os.path.basename(sql_path),
        "static_warnings": len(static_findings),
        "confirmed_warnings": len(confirmed),
        "high_confidence_confirmations": len(high_conf),
        "confirmation_rate": round(len(confirmed) / len(static_findings) if static_findings else 0, 3)
    }

def run_full_evaluation():
    results = []

    for file in os.listdir(PLAN_DIR):
        if file.endswith(".sql"):
            results.append(evaluate_query(os.path.join(PLAN_DIR, file)))

    total_static = sum(r["static_warnings"] for r in results)
    total_confirmed = sum(r["confirmed_warnings"] for r in results)

    report = {
        "per_query_results": results,
        "global_metrics": {
            "total_static_warnings": total_static,
            "total_confirmed_warnings": total_confirmed,
            "confirmation_rate": round(total_confirmed / total_static if total_static else 0, 3)
        }
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    with open(OUTPUT_PATH, "w") as f:
        json.dump(report, f, indent=4)

    print("✔ Runtime validation complete")


if __name__ == "__main__":
    run_full_evaluation()