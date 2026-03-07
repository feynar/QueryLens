"""
QueryLens – Static Rule Detection
Week 16 Expansion: EXISTS, Window Functions, HAVING, CROSS JOIN
"""


def detect_issues_from_features(features, query_id):
    findings = []

    # -----------------------------
    # EXISTING RULES
    # -----------------------------

    if features.get("has_select_star", False):
        findings.append({
            "query_id": query_id,
            "issue_type": "SELECT_STAR"
        })

    if features.get("non_sargable_functions", False):
        findings.append({
            "query_id": query_id,
            "issue_type": "NON_SARGABLE_PREDICATE"
        })

    if features.get("join_count", 0) >= 2:
        findings.append({
            "query_id": query_id,
            "issue_type": "COMPLEX_JOIN"
        })

    # -----------------------------
    # NEW WEEK 16 RULES
    # -----------------------------

    # EXISTS
    if features.get("has_exists", False):
        findings.append({
            "query_id": query_id,
            "issue_type": "EXISTS_SUBQUERY"
        })

    # NOT EXISTS
    if features.get("has_not_exists", False):
        findings.append({
            "query_id": query_id,
            "issue_type": "NOT_EXISTS_SUBQUERY"
        })

    # HAVING clause
    if features.get("has_having", False):
        findings.append({
            "query_id": query_id,
            "issue_type": "HAVING_CLAUSE"
        })

    # Window function
    if features.get("has_window_function", False):
        findings.append({
            "query_id": query_id,
            "issue_type": "WINDOW_FUNCTION"
        })

    # CROSS JOIN
    if features.get("has_cross_join", False):
        findings.append({
            "query_id": query_id,
            "issue_type": "CROSS_JOIN"
        })

    # ORDER BY
    if features.get("has_order_by", False):
        findings.append({
            "query_id": query_id,
            "issue_type": "ORDER_BY"
        })

    return findings