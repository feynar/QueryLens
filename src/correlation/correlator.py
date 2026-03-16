"""
QueryLens — Static/Runtime Correlation Engine
Links SQL anti-patterns to execution plan operators.
"""

import json
from pathlib import Path

from src.analysis.threshold_config import (
    HIGH_ROW_THRESHOLD,
    MIN_SCAN_COUNT,
    ALLOW_HASH_JOIN_CONFIRMATION,
    ALLOW_SORT_CONFIRMATION
)


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
    
    """
    Extended Week 16 to support EXISTS, WINDOW, HAVING, CROSS JOIN.
    """
    operators = [normalize_operator(op) for op in plan_findings]
    rows = [op.get("estimated_rows", 0) for op in plan_findings]

    has_scan = any(o in ["Index Scan", "Clustered Index Scan"] for o in operators)
    has_seek = "Index Seek" in operators
    has_hash_join = any("Hash" in o for o in operators)
    has_sort = "Sort" in operators
    has_nested_loop = any("Nested Loops" in o for o in operators)
    has_merge_join = any("Merge Join" in o for o in operators)
    has_window_operator = any(
        o in ["Segment", "Sequence Project"] for o in operators
    )
    has_aggregation = any(
        o in ["Stream Aggregate", "Hash Match"] for o in operators
    )

    max_rows = max(rows, default=0)

    scan_count = sum(o in ["Index Scan", "Clustered Index Scan"] for o in operators)

    is_large_query = max_rows > HIGH_ROW_THRESHOLD

    has_large_scan = (
        scan_count >= MIN_SCAN_COUNT
        and max_rows > HIGH_ROW_THRESHOLD
    )

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

            if has_scan:
                confirmed = True
                confidence = "high"
                reason = "Index/Table scan confirms non-sargable predicate"


        elif rule == "select_star":

            if has_scan:
                confirmed = True
                confidence = "medium"
                reason = "Scan caused by wide column retrieval"


        elif rule == "complex_join":

            if has_hash_join or has_merge_join:
                confirmed = True
                confidence = "medium"
                reason = "Complex join operator detected"


        elif rule == "order_by_no_index":

            if has_sort:
                confirmed = True
                confidence = "medium"
                reason = "Sort operator confirms missing index"


        elif rule == "exists_subquery":

            if has_nested_loop:
                confirmed = True
                confidence = "medium"
                reason = "Nested loop join confirms EXISTS evaluation"


        elif rule == "not_exists_subquery":

            if has_nested_loop:
                confirmed = True
                confidence = "medium"
                reason = "Nested loop join confirms NOT EXISTS evaluation"


        elif rule == "window_function":

            if has_window_operator:
                confirmed = True
                confidence = "high"
                reason = "Segment/Sequence Project confirms window function"


        elif rule == "having_clause":

            if has_aggregation:
                confirmed = True
                confidence = "medium"
                reason = "Aggregation operator confirms HAVING"


        elif rule == "cross_join":

            if has_hash_join or has_nested_loop:
                confirmed = True
                confidence = "medium"
                reason = "Join operator confirms cross join"      
 
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
