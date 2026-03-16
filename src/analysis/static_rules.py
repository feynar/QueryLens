"""
QueryLens – Static Rule Detection
Week 16 Expansion: EXISTS, Window Functions, HAVING, CROSS JOIN
"""

def detect_issues_from_features(features, query_id):

    findings = []

    # -----------------------------
    # EXISTING RULES
    # -----------------------------

    # SELECT *
    if features.get("has_select_star", False):
        findings.append({
            "query_id": query_id,
            "issue_type": "SELECT_STAR"
        })

    # NON-SARGABLE
    if len(features.get("non_sargable_functions", [])) > 0:
        findings.append({
            "query_id": query_id,
            "issue_type": "NON_SARGABLE_PREDICATE"
        })

    # COMPLEX JOIN
    if features.get("join_count", 0) >= 2:
        findings.append({
            "query_id": query_id,
            "issue_type": "COMPLEX_JOIN"
        })

    # CARTESIAN JOIN
    if features.get("has_cartesian_join"):
        findings.append({
            "query_id": query_id,
            "issue_type": "CARTESIAN_JOIN"
        })

    # ORDER BY
    if features.get("has_order_by", False):
        findings.append({
            "query_id": query_id,
            "issue_type": "ORDER_BY_NO_INDEX"
        })

    # AGGREGATE WITHOUT GROUP
    if (
        features.get("has_aggregation") and
        not features.get("has_group_by")
    ):
        findings.append({
            "query_id": query_id,
            "issue_type": "AGGREGATE_FUNCTION"
        })
        
    # GROUP BY
    if features.get("has_group_by", False):
        findings.append({
            "query_id": query_id,
            "issue_type": "GROUP_BY_AGGREGATION"
        })
        
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

    # CROSS JOIN
    if features.get("has_cross_join", False):
        findings.append({
            "query_id": query_id,
            "issue_type": "CROSS_JOIN"
        })

    # HAVING clause
    if features.get("has_having", False):
        findings.append({
            "query_id": query_id,
            "issue_type": "HAVING_CLAUSE"
        })

    # WINDOW function
    if features.get("has_window_function", False):
        findings.append({
            "query_id": query_id,
            "issue_type": "WINDOW_FUNCTION"
        })

    # SUBQUERY 
    if features.get("has_subquery", False):
        findings.append({
            "query_id": query_id,
            "issue_type": "SUBQUERY_USAGE"
        })

    # DERIVED TABLE
    if features.get("has_derived_table", False):
        findings.append({
            "query_id": query_id,
            "issue_type": "DERIVED_TABLE"
        })
        
    # DISTINCT
    if features.get("has_distinct", False):
        findings.append({
            "query_id": query_id,
            "issue_type": "DISTINCT_USAGE"
        })

    # Missing WHERE clause (possible full table scan)
    if (
            not features.get("has_where") and
            not features.get("has_group_by") and
            not features.get("has_aggregation")
        ):
        findings.append({
            "query_id": query_id,
            "issue_type": "MISSING_WHERE"
        })
        
    # CORRELATED SUBQUERY
    if features.get("has_correlated_subquery", False):
        findings.append({
            "query_id": query_id,
            "issue_type": "CORRELATED_SUBQUERY"
        })
    
    return findings