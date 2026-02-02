"""
QueryLens Prototype — Correlation Engine (Week 5)
"""

import json

HIGH_ROW_THRESHOLD = 5000


def normalize_static(f):
    """Convert different static formats into canonical structure"""
    if "rule" in f:
        return f["rule"].lower()
    if "issue_type" in f:
        return f["issue_type"].lower()
    return "unknown"


def normalize_operator(op):
    """Convert different runtime formats into operator names"""
    if "operator" in op:
        return op["operator"]
    if "physical_op" in op:
        return op["physical_op"]
    if "plan_issue" in op:
        # Map abstract labels → real operator concepts
        mapping = {
            "INDEX_SCAN": "Index Scan",
            "CLUSTERED_INDEX_SCAN": "Clustered Index Scan",
            "INDEX_SEEK": "Index Seek",
            "HASH_JOIN": "Hash Match"
        }
        return mapping.get(op["plan_issue"], op["plan_issue"])
    return "Unknown"


def correlate(static_findings, plan_findings):
    results = []

    # Normalize runtime info
    operators = [normalize_operator(op) for op in plan_findings]
    rows = [op.get("estimated_rows", 0) for op in plan_findings]

    has_scan = any(o in ["Index Scan", "Clustered Index Scan"] for o in operators)
    has_seek = "Index Seek" in operators
    has_hash_join = any("Hash" in o for o in operators)
    max_rows = max(rows, default=0)

    for finding in static_findings:
        rule = normalize_static(finding)
        query_id = finding.get("query_id", "unknown")

        confirmed = False
        confidence = "low"
        reason = ""

        if rule == "non_sargable_predicate":
            if has_scan and max_rows > HIGH_ROW_THRESHOLD:
                confirmed = True
                confidence = "high"
                reason = "Scan with high row count confirms filter inefficiency"
            elif has_seek:
                reason = "Index Seek suggests SQL Server optimized predicate"

        elif rule == "select_star":
            if has_scan:
                confirmed = True
                confidence = "medium"
                reason = "Scan suggests large data retrieval"
            else:
                reason = "No heavy scan detected"

        elif rule == "complex_join":
            if has_hash_join:
                confirmed = True
                confidence = "medium"
                reason = "Hash Join indicates possible missing index or large join"
            else:
                reason = "No high-cost join operator detected"

        results.append({
            "query_id": query_id,
            "rule": rule,
            "confirmed": confirmed,
            "confidence": confidence,
            "reason": reason
        })

    return results


if __name__ == "__main__":
    print("Standalone test run")