import re


def suggest_rewrites(sql_text, triggered_rules, features):
    """
    Returns a list of rewrite suggestions based on triggered rules.
    Each suggestion contains:
    - rule
    - original snippet (optional)
    - rewritten suggestion
    """

    suggestions = []
    sql_upper = sql_text.upper()

    rules = {r["rule"] for r in triggered_rules}

    # ---------------------------------
    # SELECT *
    # ---------------------------------
    if "select_star" in rules:
        suggestions.append({
            "rule": "select_star",
            "issue": "Using SELECT *",
            "suggestion": "Replace SELECT * with explicit column names",
            "example": "SELECT col1, col2 FROM table_name"
        })

    # ---------------------------------
    # NON-SARGABLE PREDICATE
    # ---------------------------------
    if "non_sargable_predicate" in rules:
        suggestions.append({
            "rule": "non_sargable_predicate",
            "issue": "Function applied to indexed column",
            "suggestion": "Rewrite predicate to be sargable",
            "example": "WHERE OrderDate >= '2023-01-01' AND OrderDate < '2024-01-01'"
        })

    # ---------------------------------
    # CORRELATED SUBQUERY → JOIN rewrite
    # ---------------------------------
    if "correlated_subquery" in rules:
        suggestions.append({
            "rule": "correlated_subquery",
            "issue": "Correlated subquery detected",
            "suggestion": "Rewrite as JOIN for better performance",
            "example": (
                "SELECT c.* FROM Customers c "
                "JOIN Orders o ON c.CustomerID = o.CustomerID"
            )
        })

    # ---------------------------------
    # CROSS JOIN
    # ---------------------------------
    if "cross_join" in rules:
        suggestions.append({
            "rule": "cross_join",
            "issue": "Cartesian product",
            "suggestion": "Add join condition or convert to INNER JOIN",
            "example": "FROM A JOIN B ON A.id = B.id"
        })

    # ---------------------------------
    # ORDER BY without index
    # ---------------------------------
    if "order_by_no_index" in rules:
        suggestions.append({
            "rule": "order_by_no_index",
            "issue": "Sorting without index",
            "suggestion": "Add index on ORDER BY column",
            "example": "CREATE INDEX idx_orders_date ON Orders(OrderDate)"
        })

    # ---------------------------------
    # COMPLEX JOIN
    # ---------------------------------
    if "complex_join" in rules:
        suggestions.append({
            "rule": "complex_join",
            "issue": "Too many joins",
            "suggestion": "Break query into smaller parts or use temp tables",
            "example": "Use intermediate #temp tables for large joins"
        })

    return suggestions