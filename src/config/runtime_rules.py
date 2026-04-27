"""
QueryLens — Runtime-Verifiable Rule Configuration

Defines the subset of static analysis rules that can be validated
using execution plan evidence.

Purpose:
    - separate rules that support runtime validation from purely static heuristics
    - ensure the correlation engine only attempts validation where evidence exists
    - support accurate reporting of validated vs static-only findings

Notes:
    - rules not included here are treated as static-only
    - duplicate entries are preserved as-is to avoid altering behavior
"""
# Only rules that can be validated from execution plans
RUNTIME_VERIFIABLE_RULES = {
    "select_star",
    "non_sargable_predicate",
    "complex_join",
    "order_by_no_index",
    "cross_join",
    "exists_subquery",
    "not_exists_subquery",
    "window_function",
    "having_clause",
    "cartesian_join",
    "missing_index"
}