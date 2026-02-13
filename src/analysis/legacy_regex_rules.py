"""
QueryLens Prototype — Static SQL Analyzer (Week 5)

Detects basic inefficient SQL patterns using rule-based inspection.
Outputs structured findings for correlation stage.
"""

import json
import os
import re
import sys


def analyze_with_regex(file_path):
    with open(file_path, "r") as f:
        sql = f.read().lower()

    findings = []
    query_id = os.path.splitext(os.path.basename(file_path))[0]

    # Rule 1: SELECT *
    if re.search(r"select\s+\*", sql):
        findings.append({"query_id": query_id, "issue_type": "SELECT_STAR"})

    # Rule 2: Non-sargable predicate (function on column)
    if re.search(r"where\s+.*(year|month|day)\s*\(", sql):
        findings.append({"query_id": query_id, "issue_type": "NON_SARGABLE_PREDICATE"})

    # Rule 3: Complex join (2+ joins)
    if sql.count(" join ") >= 2:
        findings.append({"query_id": query_id, "issue_type": "COMPLEX_JOIN"})

    return findings


def save_results(results):
    out_dir = ARTIFACTS / "analyzer"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "static_results.json"

    with open(out_path, "w") as f:
        json.dump(results, f, indent=4)

    print(f"Static results saved to {out_path}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python static_analyzer.py <query.sql>")
        sys.exit(1)

    sql_file = sys.argv[1]
    results = analyze_sql(sql_file)
    save_results(results)