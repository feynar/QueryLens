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

RULE_METADATA = {
    "select_star": {"runtime_verifiable": True},
    "non_sargable_predicate": {"runtime_verifiable": True},
    "complex_join": {"runtime_verifiable": True},
    "order_by_no_index": {"runtime_verifiable": True},
    "cross_join": {"runtime_verifiable": True},
    "exists_subquery": {"runtime_verifiable": True},
    "window_function": {"runtime_verifiable": True},
    "missing_index": {"runtime_verifiable": True},
    
    "missing_where": {"runtime_verifiable": False},
    "derived_table": {"runtime_verifiable": False},
    "basic_join": {"runtime_verifiable": False},
    "correlated_subquery": {"runtime_verifiable": False},
}


def build_rule(rule_name, confidence="medium"):
    meta = RULE_METADATA.get(rule_name, {})

    return {
        "rule": rule_name,
        "confidence": confidence,
        "runtime_verifiable": meta.get("runtime_verifiable", False)
    }


def evaluate_rules(features):

    rules = []

    if features["has_select_star"]:
        rules.append(build_rule("select_star", "high"))

    if not features["has_where"] and not features["has_group_by"]:
        rules.append(build_rule("missing_where", "low"))

    if features["non_sargable_functions"]:
        rules.append(build_rule("non_sargable_predicate", "high"))

    if features["join_count"] >= 3:
        rules.append(build_rule("complex_join", "high"))
    elif features["join_count"] > 0:
        rules.append(build_rule("basic_join", "low"))

    if features["has_cross_join"]:
        rules.append(build_rule("cross_join", "medium"))

    if features["has_order_by"] and not features["has_where"]:
        rules.append(build_rule("order_by_no_index", "medium"))

    if features["has_exists"]:
        rules.append(build_rule("exists_subquery", "medium"))

    if features["has_not_exists"]:
        rules.append(build_rule("not_exists_subquery", "medium"))

    if features["has_correlated_subquery"]:
        rules.append(build_rule("correlated_subquery", "medium"))

    if features["has_derived_table"]:
        rules.append(build_rule("derived_table", "low"))

    if features["has_window_function"]:
        rules.append(build_rule("window_function", "medium"))
        
    if features["join_count"] > 0:

        # Case 0: CROSS JOIN → not an index issue
        if features["has_cross_join"]:
            pass

        # Case 1: No join predicate → true cartesian / bad join
        elif not features["has_join_predicate"]:
            rules.append(build_rule("missing_index", "high"))

        # Case 2: Join + WHERE → only flag if weak filtering on join columns
        elif features["has_where"]:

            where_text = " ".join(features["where_columns"])
            join_text = " ".join(features["join_columns"])

            # Only trigger if WHERE does NOT reference join columns
            # (suggests poor filtering/index usage)
            if not any(jc in where_text for jc in features["join_columns"]):

                if not features["has_selective_predicate"] and not features["has_range_predicate"]:
                    rules.append(build_rule("missing_index", "medium"))

                elif features["has_range_predicate"] and not features["has_selective_predicate"]:
                    rules.append(build_rule("missing_index", "low"))

        # Case 3: JOIN without WHERE → don't assume missing index
        else:
            pass
    
    return rules