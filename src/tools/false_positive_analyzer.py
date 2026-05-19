"""
QueryLens — False Positive Diagnostic Tool

Generates an explanatory report for static warnings that were not
confirmed by execution plan evidence.

Purpose:
    - identify static detections lacking runtime support
    - provide rule-level reasons and evidence for each case
    - summarize overall false-positive volume across the workload
"""

import os
from src.analysis.static_analyzer import analyze_sql
from src.analysis.plan_analyzer import parse_plan
from src.correlation.correlator import correlate
from src.db.index_metadata_loader import load_index_metadata

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PLAN_DIR = os.path.join(PROJECT_ROOT, "plans")
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "artifacts", "validation_log.txt")


def find_plan(sql_path):
    """Returns the matching .sqlplan path for a SQL file if it exists."""    
    base = os.path.splitext(sql_path)[0]
    plan_path = base + ".sqlplan"
    return plan_path if os.path.exists(plan_path) else None


def analyze_query(sql_path, index_metadata=None):
    """
    Runs static analysis, runtime parsing, and correlation for one query,
    then returns the subset of findings that were not confirmed at runtime.
    """    
    static_findings = analyze_sql(sql_path, index_metadata=index_metadata)

    plan_path = find_plan(sql_path)
    runtime_findings = parse_plan(plan_path) if plan_path else []

    correlations = correlate(static_findings, runtime_findings)
    
    # Unconfirmed findings are treated here as false-positive candidates.
    unconfirmed = [
        c for c in correlations
        if c.get("validation_type") == "runtime" and not c.get("confirmed")
    ]

    return unconfirmed


def run_analysis(index_metadata=None):
    """
    Evaluates all SQL files in the workload and writes a diagnostic log
    describing static findings that were not confirmed by runtime evidence.
    """
    lines = []
    lines.append("QueryLens False Positive Analysis")
    lines.append("================================\n")

    total_static = 0
    total_false_positives = 0

    if index_metadata is None:
        try:
            index_metadata = load_index_metadata(save_to_file=True)
        except Exception:
            index_metadata = {}
        
    for file in os.listdir(PLAN_DIR):
        if not file.endswith(".sql"):
            continue

        sql_path = os.path.join(PLAN_DIR, file)

        # Count static warnings separately for summary statistics.
        static_findings = analyze_sql(sql_path, index_metadata=index_metadata)
        total_static += len(static_findings)

        unconfirmed = analyze_query(sql_path, index_metadata=index_metadata)

        if not unconfirmed:
            continue

        total_false_positives += len(unconfirmed)

        lines.append(f"Query: {file}")

        for item in unconfirmed:
            lines.append(f"  Rule: {item['rule']}")
            lines.append(f"  Confidence: {item['confidence']}")
            lines.append(f"  Evidence: {item['evidence']}")
            lines.append(f"  Reason: {item['reason']}\n")

    # Always write a summary section, even when no false positives are found.
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