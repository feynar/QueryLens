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


def evaluate_rules(features):
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
        
    # Join-heavy queries may also trigger missing-index heuristics.        
    if features["join_count"] > 0:
        
        # Case 0: CROSS JOIN is handled separately and is not treated as an index issue.
        if features["has_cross_join"]:
            pass

        # Case 1: JOIN without an ON predicate suggests a true cartesian join
        # or malformed join structure, so missing_index is flagged strongly.
        elif not features["has_join_predicate"]:
            rules.append(build_rule("missing_index", "high"))

        # Case 2: JOIN with WHERE clause uses additional heuristics based on
        # whether filtering appears selective and whether WHERE references join columns.
        elif features["has_where"]:

            where_text = " ".join(features["where_columns"])
            join_text = " ".join(features["join_columns"])

            # Only trigger if the WHERE clause does not reference the stored join columns,
            # which may suggest weaker filtering or indexing support.
            if not any(jc in where_text for jc in features["join_columns"]):

                if not features["has_selective_predicate"] and not features["has_range_predicate"]:
                    rules.append(build_rule("missing_index", "medium"))

                elif features["has_range_predicate"] and not features["has_selective_predicate"]:
                    rules.append(build_rule("missing_index", "low"))

        # Case 3: JOIN without WHERE is left unflagged for missing_index here.
        else:
            pass
    
    return rules