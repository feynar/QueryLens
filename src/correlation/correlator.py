"""
QueryLens — Static/Runtime Correlation Engine
Links SQL anti-patterns to execution plan operators.
"""

import json
from pathlib import Path

HIGH_ROW_THRESHOLD = 5000


# ----------------------------
# Normalization helpers
# ----------------------------

def normalize_static(finding):
    if "rule" in finding:
        return finding["rule"].lower()
    if "issue_type" in finding:
        return finding["issue_type"].lower()
    return "unknown"


def normalize_operator(op):
    """Standardize operator naming across sources"""
    if "operator" in op:
        return op["operator"]

    if "physical_op" in op:
        return op["physical_op"]

    if "plan_issue" in op:
        mapping = {
            "INDEX_SCAN": "Index Scan",
            "CLUSTERED_INDEX_SCAN": "Clustered Index Scan",
            "INDEX_SEEK": "Index Seek",
            "HASH_JOIN": "Hash Match",
            "MERGE_JOIN": "Merge Join",
            "SORT": "Sort"
        }
        return mapping.get(op["plan_issue"], op["plan_issue"])

    return "Unknown"


# ----------------------------
# Core correlation logic
# ----------------------------

def correlate(static_findings, plan_findings):
    results = []

    operators = [normalize_operator(op) for op in plan_findings]
    rows = [op.get("estimated_rows", 0) for op in plan_findings]

    has_scan = any(o in ["Index Scan", "Clustered Index Scan"] for o in operators)
    has_seek = "Index Seek" in operators
    has_hash_join = any("Hash" in o for o in operators)
    has_sort = "Sort" in operators
    max_rows = max(rows, default=0)

    for finding in static_findings:
        rule = normalize_static(finding)
        query_id = finding.get("query_id", "unknown")

        confirmed = False
        confidence = "low"
        reason = "No runtime evidence supporting static warning"

        # ----------------------------
        # Rule correlations
        # ----------------------------

        if rule == "non_sargable_predicate":
            if has_scan and max_rows > HIGH_ROW_THRESHOLD:
                confirmed = True
                confidence = "high"
                reason = "Large scan confirms non-sargable filter"
            elif has_seek:
                confidence = "low"
                reason = "Optimizer used seek despite predicate"

        elif rule == "select_star":
            if has_scan and max_rows > HIGH_ROW_THRESHOLD:
                confirmed = True
                confidence = "medium"
                reason = "Wide data retrieval causing scan"

        elif rule == "complex_join":
            if has_hash_join:
                confirmed = True
                confidence = "medium"
                reason = "Hash join indicates expensive join"

        # Future extensibility
        elif rule == "order_by_no_index":
            if has_sort:
                confirmed = True
                confidence = "medium"
                reason = "Sort operator indicates missing index"

        results.append({
            "query_id": query_id,
            "rule": rule,
            "confirmed": confirmed,
            "confidence": confidence,
            "max_estimated_rows": max_rows,
            "operators_observed": operators,
            "reason": reason
        })

    return results


# ----------------------------
# Optional standalone run
# ----------------------------

if __name__ == "__main__":
    print("Correlation module ready.")
