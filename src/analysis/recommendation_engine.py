def generate_recommendation(rule, confidence):

    if rule == "select_star":
        return {
            "issue": "SELECT * used",
            "impact": "May cause unnecessary I/O and prevent index usage",
            "recommendation": "Select only required columns instead of using SELECT *"
        }

    if rule == "non_sargable_predicate":
        return {
            "issue": "Non-SARGable predicate",
            "impact": "Prevents index seeks and forces scans",
            "recommendation": "Avoid functions on indexed columns"
        }

    if rule == "complex_join":
        return {
            "issue": "Multiple joins detected",
            "impact": "High memory and CPU usage",
            "recommendation": "Ensure join columns are indexed"
        }

    if rule == "basic_join":
        return {
            "issue": "Join detected",
            "impact": "May produce large intermediate results",
            "recommendation": "Ensure joins are selective and indexed"
        }

    if rule == "cross_join":
        return {
            "issue": "CROSS JOIN detected",
            "impact": "Produces very large result sets",
            "recommendation": "Ensure this is intentional"
        }

    if rule == "order_by_no_index":
        return {
            "issue": "ORDER BY without filtering",
            "impact": "Expensive sort operation",
            "recommendation": "Add index or filter rows before sorting"
        }

    if rule == "window_function":
        return {
            "issue": "Window function used",
            "impact": "Requires sorting and memory",
            "recommendation": "Ensure proper indexing"
        }

    if rule == "exists_subquery":
        return {
            "issue": "EXISTS subquery used",
            "impact": "May affect performance",
            "recommendation": "Ensure subquery is efficient"
        }

    if rule == "correlated_subquery":
        return {
            "issue": "Correlated subquery detected",
            "impact": "Executed per row, can be slow",
            "recommendation": "Rewrite as JOIN if possible"
        }

    if rule == "derived_table":
        return {
            "issue": "Derived table used",
            "impact": "May reduce optimizer efficiency",
            "recommendation": "Simplify query if possible"
        }

    if rule == "missing_where":
        return {
            "issue": "No WHERE clause",
            "impact": "Full table scan possible",
            "recommendation": "Add filtering conditions"
        }

    if rule == "key_lookup":
        return {
            "issue": "Key Lookup detected",
            "impact": "Causes repeated lookups, high I/O cost",
            "recommendation": "Add covering index with included columns"
        }

    if rule == "missing_index":
        return {
            "issue": "Missing index",
            "impact": "Query uses scans or inefficient access paths",
            "recommendation": "Create index on filter/join columns"
        }

    return {
        "issue": "Unknown",
        "impact": "N/A",
        "recommendation": "No recommendation available"
    }