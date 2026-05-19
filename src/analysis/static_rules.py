"""
QueryLens — Static Rule Detection

Maps extracted SQL features to static anti-pattern detections.

Design principles:
    - each rule is evaluated independently
    - each detection produces a structured finding
    - each finding includes a confidence label
    - some rules are marked as runtime-verifiable for later validation

Confidence levels:
    high   -> strong evidence of inefficiency
    medium -> likely issue depending on query shape or data distribution
    low    -> heuristic or context-dependent signal
"""

RULE_METADATA = {
    "select_star": {"runtime_verifiable": True},
    "non_sargable_predicate": {"runtime_verifiable": True},
    "complex_join": {"runtime_verifiable": True},
    "order_by_no_index": {"runtime_verifiable": True},
    "cross_join": {"runtime_verifiable": True},
    "exists_subquery": {"runtime_verifiable": True},
    "not_exists_subquery": {"runtime_verifiable": True},
    "window_function": {"runtime_verifiable": True},
    "missing_index": {"runtime_verifiable": True},
    "having_clause": {"runtime_verifiable": True},
    
    "missing_where": {"runtime_verifiable": False},
    "derived_table": {"runtime_verifiable": False},
    "basic_join": {"runtime_verifiable": False},
    "correlated_subquery": {"runtime_verifiable": False},
}

def normalize_name(value):
    if not value:
        return ""
    return str(value).replace("[", "").replace("]", "").lower()


def is_indexed_column(index_metadata, table_name, column_name):
    """
    Returns True if column_name is indexed on table_name.
    """
    if not index_metadata:
        return False

    table = normalize_name(table_name)
    column = normalize_name(column_name)

    return column in index_metadata.get(table, set())

def any_unindexed_column(index_metadata, table_name, columns):
    """
    Returns True if at least one candidate column is not indexed
    on the table being analyzed.
    """
    if not index_metadata or not table_name or not columns:
        return False

    for column in columns:
        if not is_indexed_column(index_metadata, table_name, column):
            return True

    return False
    
def build_rule(rule_name, confidence="medium"):
    """
    Builds a normalized rule object using shared metadata.

    Returns:
        dict: rule label, confidence, and runtime-verifiable flag
    """    
    meta = RULE_METADATA.get(rule_name, {})

    return {
        "rule": rule_name,
        "confidence": confidence,
        "runtime_verifiable": meta.get("runtime_verifiable", False)
    }

def evaluate_rules(features, index_metadata=None):
    """
    Evaluates static anti-pattern rules from extracted SQL features.

    Parameters:
        features (dict): feature flags and structural information extracted
        from the SQL parse tree

    Returns:
        list: structured rule findings
    """
    rules = []

    if features["has_select_star"]:
        rules.append(build_rule("select_star", "high"))
        
    # Queries with neither WHERE nor GROUP BY are treated as broad retrieval
    # candidates and flagged as low-confidence static-only warnings.
    if not features["has_where"] and not features["has_group_by"]:
        rules.append(build_rule("missing_where", "low"))

    if features["non_sargable_functions"]:
        rules.append(build_rule("non_sargable_predicate", "high"))

    # Distinguish larger multi-join queries from simpler join structures.
    if features["join_count"] >= 3:
        rules.append(build_rule("complex_join", "high"))
    elif features["join_count"] > 0:
        rules.append(build_rule("basic_join", "low"))

    if features["has_cross_join"]:
        rules.append(build_rule("cross_join", "medium"))

    # ORDER BY without filtering is treated as a likely sort-cost issue.
    if features["has_order_by"] and not features["has_where"]:
        table_name = features.get("primary_table")
        order_by_columns = features.get("order_by_columns", [])

        indexed_order_by = any(
            is_indexed_column(index_metadata, table_name, col)
            for col in order_by_columns
        )

        if not indexed_order_by:
            rules.append(build_rule("order_by_no_index", "medium"))

    # NOT EXISTS is checked before EXISTS so the two rules remain mutually exclusive.
    if features["has_not_exists"]:
        rules.append(build_rule("not_exists_subquery", "medium"))
    elif features["has_exists"]:
        rules.append(build_rule("exists_subquery", "medium"))

    if features["has_correlated_subquery"]:
        rules.append(build_rule("correlated_subquery", "medium"))

    if features["has_derived_table"]:
        rules.append(build_rule("derived_table", "low"))

    if features["has_window_function"]:
        rules.append(build_rule("window_function", "medium"))
        
    if features["has_having"]:
        rules.append(build_rule("having_clause", "medium"))
        
    # Missing index heuristic using live SQL Server index metadata.
    # This avoids treating every large join/scan as a missing-index issue.
    if features["join_count"] > 0 and not features["has_cross_join"]:
        table_name = features.get("primary_table")

        candidate_columns = []
        candidate_columns.extend(features.get("join_column_names", []))
        candidate_columns.extend(features.get("where_column_names", []))

        if index_metadata:
            if any_unindexed_column(index_metadata, table_name, candidate_columns):
                rules.append(build_rule("missing_index", "medium"))

        else:
            # Offline fallback when SQL Server metadata is unavailable.
            if not features["has_join_predicate"]:
                rules.append(build_rule("missing_index", "high"))
    
    return rules