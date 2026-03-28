"""
QueryLens – Static Rule Detection
Rule Engine Design:

Maps extracted SQL features → static anti-pattern detections.

Each rule:
    - is independent
    - produces a structured finding
    - includes a confidence level

Confidence Levels:
    high   → strong evidence of inefficiency
    medium → likely issue depending on data distribution
    low    → heuristic / context-dependent
"""

def detect_issues_from_features(features, query_id):

    findings = []

    # SELECT *
    if features.get("has_select_star", False):
        findings.append({
            "query_id": query_id,
            "issue_type": "SELECT_STAR",
            "confidence": "high"
        })

    # NON-SARGABLE
    if len(features.get("non_sargable_functions", [])) > 0:
        findings.append({
            "query_id": query_id,
            "issue_type": "NON_SARGABLE_PREDICATE",
            "confidence": "high"
        })

    # COMPLEX JOIN
    if features.get("join_count", 0) >= 2:
        findings.append({
            "query_id": query_id,
            "issue_type": "COMPLEX_JOIN",
            "confidence": "medium"
        })

    # CARTESIAN vs CROSS JOIN (avoid duplication)
    if features.get("has_cartesian_join"):
        findings.append({
            "query_id": query_id,
            "issue_type": "CARTESIAN_JOIN",
            "confidence": "high"
        })
    elif features.get("has_cross_join"):
        findings.append({
            "query_id": query_id,
            "issue_type": "CROSS_JOIN",
            "confidence": "medium"
        })

    # ORDER BY (refined to reduce false positives)
    if (
        features.get("has_order_by", False)
        and features.get("join_count", 0) > 0
    ):
        findings.append({
            "query_id": query_id,
            "issue_type": "ORDER_BY_NO_INDEX",
            "confidence": "medium"
        })

    # AGGREGATE WITHOUT GROUP
    if (
        features.get("has_aggregation")
        and not features.get("has_group_by")
    ):
        findings.append({
            "query_id": query_id,
            "issue_type": "AGGREGATE_FUNCTION",
            "confidence": "low"
        })

    # GROUP BY (refined)
    if (
        features.get("has_group_by")
        and features.get("join_count", 0) > 1
    ):
        findings.append({
            "query_id": query_id,
            "issue_type": "GROUP_BY_AGGREGATION",
            "confidence": "low"
        })

    # EXISTS
    if features.get("has_exists", False):
        findings.append({
            "query_id": query_id,
            "issue_type": "EXISTS_SUBQUERY",
            "confidence": "medium"
        })

    # NOT EXISTS
    if features.get("has_not_exists", False):
        findings.append({
            "query_id": query_id,
            "issue_type": "NOT_EXISTS_SUBQUERY",
            "confidence": "medium"
        })

    # HAVING
    if features.get("has_having", False):
        findings.append({
            "query_id": query_id,
            "issue_type": "HAVING_CLAUSE",
            "confidence": "medium"
        })

    # WINDOW FUNCTION
    if features.get("has_window_function", False):
        findings.append({
            "query_id": query_id,
            "issue_type": "WINDOW_FUNCTION",
            "confidence": "medium"
        })

    # SUBQUERY (avoid duplication with EXISTS)
    if (
        features.get("has_subquery", False)
        and not features.get("has_exists")
        and not features.get("has_not_exists")
    ):
        findings.append({
            "query_id": query_id,
            "issue_type": "SUBQUERY_USAGE",
            "confidence": "low"
        })

    # DERIVED TABLE
    if features.get("has_derived_table", False):
        findings.append({
            "query_id": query_id,
            "issue_type": "DERIVED_TABLE",
            "confidence": "low"
        })

    # DISTINCT
    if features.get("has_distinct", False):
        findings.append({
            "query_id": query_id,
            "issue_type": "DISTINCT_USAGE",
            "confidence": "low"
        })

    # MISSING WHERE (refined)
    if (
        not features.get("has_where")
        and not features.get("has_group_by")
        and not features.get("has_aggregation")
        and not features.get("has_exists")
        and not features.get("has_not_exists")
        and not features.get("has_subquery")
    ):
        findings.append({
            "query_id": query_id,
            "issue_type": "MISSING_WHERE",
            "confidence": "low"
        })

    # CORRELATED SUBQUERY
    if features.get("has_correlated_subquery", False):
        findings.append({
            "query_id": query_id,
            "issue_type": "CORRELATED_SUBQUERY",
            "confidence": "medium"
        })

    return findings