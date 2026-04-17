"""
QueryLens — Expanded Runtime Validation Evaluator

Runs runtime validation over the expanded workload by comparing
static rule detections against execution plan evidence.

Outputs:
    - per-query rule instances with confirmation / confidence
    - per-query confirmation metrics
    - global confirmation metrics
"""

import os
import json

from src.config.runtime_rules import RUNTIME_VERIFIABLE_RULES
from src.analysis.static_analyzer import analyze_sql
from src.analysis.plan_analyzer import parse_plan
from src.correlation.correlator import correlate, normalize_static

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

PLAN_DIR = os.path.join(PROJECT_ROOT, "plans")
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "artifacts", "evaluation", "expanded_runtime_report.json")


def find_plan_file(sql_path):
    """Returns the matching .sqlplan path for a SQL file if it exists."""    
    base = os.path.splitext(sql_path)[0]
    plan_path = base + ".sqlplan"
    return plan_path if os.path.exists(plan_path) else None


def evaluate_query(sql_path):
    """
    Evaluates one SQL query by combining:
        - static analysis
        - runtime plan parsing
        - correlation between static and runtime evidence

    Returns a per-query summary including rule instances and confirmation metrics.
    """    
    sql_name = os.path.basename(sql_path)

    # ----------------------------
    # Static analysis
    # ----------------------------
    static_findings = analyze_sql(sql_path)

    # ----------------------------
    # Runtime analysis
    # ----------------------------
    # Use the matching execution plan when available; otherwise treat
    # runtime evidence as absent for this query.    
    plan_path = find_plan_file(sql_path)

    if plan_path:
        runtime_findings = parse_plan(plan_path)
    else:
        runtime_findings = []

    # ----------------------------
    # Correlation
    # ----------------------------
    # Correlate static detections with runtime evidence and capture
    # confirmation / confidence at the rule level.    
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
    # Construct a normalized per-rule view so reporting can distinguish
    # runtime-verifiable rules from static-only rules.    
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
    # Confirmation metrics are computed only over rules that are eligible
    # for runtime validation.    
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
    """
    Runs expanded runtime validation across the full workload and writes
    the resulting report to the evaluation artifacts directory.
    """    
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