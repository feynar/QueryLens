"""
QueryLens — Runtime Behavior Summary Generator (Week 15)

Analyzes execution plan operators across the expanded workload
and produces distribution statistics for research reporting.
"""

import os
import json
from collections import Counter

from src.analysis.static_analyzer import analyze_sql
from src.analysis.prototype_plan_analyzer import parse_plan
from src.correlation.correlator import correlate


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

PLAN_DIR = os.path.join(PROJECT_ROOT, "plans_expanded")
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "artifacts", "eval", "runtime_behavior_summary.json")


# -------------------------------------------------
# Extract operators from plan
# -------------------------------------------------
def extract_operator_stats(plan_findings):
    operators = [op.get("operator", "Unknown") for op in plan_findings]

    stats = {
        "has_index_scan": any(o in ["Index Scan", "Clustered Index Scan"] for o in operators),
        "has_index_seek": "Index Seek" in operators,
        "has_hash_join": any("Hash" in o for o in operators),
        "has_sort": "Sort" in operators,
        "operator_list": operators
    }

    return stats


# -------------------------------------------------
# Analyze one query
# -------------------------------------------------
def analyze_query(sql_path):
    static_findings = analyze_sql(sql_path)

    plan_path = os.path.splitext(sql_path)[0] + ".sqlplan"
    plan_findings = parse_plan(plan_path) if os.path.exists(plan_path) else []

    operator_stats = extract_operator_stats(plan_findings)
    correlations = correlate(static_findings, plan_findings)

    confirmed = [c for c in correlations if c["confirmed"]]

    return {
        "query": os.path.basename(sql_path),
        "static_warning_count": len(static_findings),
        "confirmed_count": len(confirmed),
        "operators": operator_stats["operator_list"],
        "has_index_scan": operator_stats["has_index_scan"],
        "has_index_seek": operator_stats["has_index_seek"],
        "has_hash_join": operator_stats["has_hash_join"],
        "has_sort": operator_stats["has_sort"]
    }


# -------------------------------------------------
# Aggregate statistics across workload
# -------------------------------------------------
def compute_global_summary(rows):
    operator_counter = Counter()

    total_queries = len(rows)
    total_static = sum(r["static_warning_count"] for r in rows)
    total_confirmed = sum(r["confirmed_count"] for r in rows)

    for row in rows:
        operator_counter.update(row["operators"])

    summary = {
        "total_queries": total_queries,
        "total_static_warnings": total_static,
        "total_confirmed_warnings": total_confirmed,
        "confirmation_rate": round(total_confirmed / total_static, 3) if total_static else 0,
        "operator_distribution": dict(operator_counter)
    }

    return summary


# -------------------------------------------------
# Main execution
# -------------------------------------------------
def run_summary():
    results = []

    for file in os.listdir(PLAN_DIR):
        if file.endswith(".sql"):
            sql_path = os.path.join(PLAN_DIR, file)
            results.append(analyze_query(sql_path))

    summary = compute_global_summary(results)

    output = {
        "per_query": results,
        "global_summary": summary
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=4)

    print("✔ Runtime behavior summary generated")
    print(json.dumps(summary, indent=4))


if __name__ == "__main__":
    run_summary()