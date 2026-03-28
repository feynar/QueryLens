"""
QueryLens Expanded Runtime Validation Evaluator (Week 14)

Runs runtime validation on the expanded workload.
"""

import os
import json

from src.analysis.static_analyzer import analyze_sql
from src.analysis.prototype_plan_analyzer import parse_plan
from src.correlation.correlator import correlate, normalize_static


# ✅ Only rules that can be validated from execution plans
RUNTIME_VERIFIABLE_RULES = {
    "select_star",
    "non_sargable_predicate",
    "complex_join",
    "order_by_no_index",
    "cross_join",
    "exists_subquery",
    "not_exists_subquery",
    "window_function",
    "having_clause",
    "cartesian_join"
}

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

PLAN_DIR = os.path.join(PROJECT_ROOT, "plans")
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "artifacts", "evaluation", "expanded_runtime_report.json")


def find_plan_file(sql_path):
    base = os.path.splitext(sql_path)[0]
    plan_path = base + ".sqlplan"
    return plan_path if os.path.exists(plan_path) else None


def evaluate_query(sql_path):
    sql_name = os.path.basename(sql_path)

    # ----------------------------
    # Static analysis
    # ----------------------------
    static_findings = analyze_sql(sql_path)

    # ----------------------------
    # Runtime analysis
    # ----------------------------
    plan_path = find_plan_file(sql_path)

    if plan_path:
        runtime_findings = parse_plan(plan_path)
    else:
        runtime_findings = []

    # ----------------------------
    # Correlation
    # ----------------------------
    correlations = correlate(static_findings, runtime_findings)

    correlation_map = {
            c["rule"]: {
                "confirmed": c["confirmed"],
                "confidence": c["confidence"],
                "evidence": c["evidence"]
            }
            for c in correlations
        }

    # ----------------------------
    # Build rule instances
    # ----------------------------
    rule_instances = []

    for finding in static_findings:
        rule = normalize_static(finding)
        is_verifiable = rule in RUNTIME_VERIFIABLE_RULES

        corr = correlation_map.get(rule, {})

        rule_instances.append({
            "rule": rule,
            "confirmed": corr.get("confirmed", False),
            "confidence": corr.get("confidence", "low"),
            "evidence": corr.get("evidence", []),
            "runtime_verifiable": is_verifiable
        })

    # ----------------------------
    # Metrics (ONLY verifiable rules)
    # ----------------------------
    verifiable_instances = [
        r for r in rule_instances if r["runtime_verifiable"]
    ]

    static_count = len(verifiable_instances)
    confirmed_count = sum(1 for r in verifiable_instances if r["confirmed"])

    return {
        "query": sql_name,
        "rule_instances": rule_instances,
        "static_warnings": static_count,
        "confirmed_warnings": confirmed_count,
        "confirmation_rate": round(confirmed_count / static_count if static_count else 0, 3)
    }


def run_evaluation():
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

    print("✔ Expanded runtime validation complete")


if __name__ == "__main__":
    run_evaluation()