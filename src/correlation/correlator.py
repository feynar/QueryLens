"""
QueryLens — Static/Runtime Correlation Engine

Links SQL anti-patterns detected during static analysis to execution plan
evidence observed at runtime.

Correlation engine logic:
    static SQL anti-patterns -> execution plan evidence

Examples:
    SELECT * -> Index Scan
    Non-sargable predicate -> Table Scan
    ORDER BY without index -> Sort operator

Produces:
    - confirmation flag
    - confidence level
    - explanation (reason)
"""

from src.config.runtime_rules import RUNTIME_VERIFIABLE_RULES

from src.config.threshold_config import (
    HIGH_ROW_THRESHOLD,
    MIN_SCAN_COUNT
)


# ----------------------------
# Normalization
# ----------------------------

def normalize_static(finding):
    if "rule" in finding:
        return finding["rule"].lower()
    if "issue_type" in finding:
        return finding["issue_type"].lower()
    return "unknown"


# ----------------------------
# Runtime feature extraction
# ----------------------------

def extract_runtime_features(plan_findings):
    """Summarizes raw execution plan operators into correlation-ready runtime features."""

    # Collapse raw plan operators into boolean signals used by the scoring rules.
    operators = []
    logical_ops = []
    rows = []

    for op in plan_findings:
        physical = op.get("operator", "")
        logical = op.get("logical_op", "")

        operators.append(physical)
        logical_ops.append(logical)
        rows.append(op.get("estimated_rows", 0))

    max_rows = max(rows, default=0)
    scan_count = sum(o in ["Index Scan", "Clustered Index Scan"] for o in operators)

    features = {
        "operators": operators,
        "logical_ops": logical_ops,
        "max_rows": max_rows,
        "scan_count": scan_count,
        "has_scan": scan_count > 0,
        "has_seek": "Index Seek" in operators,
        "has_sort": "Sort" in operators,
        "has_hash_join": any("HASH MATCH" in o.upper() for o in operators),
        "has_hash_agg": any("AGGREGATE" in (l or "").upper() for l in logical_ops),
        "has_nested_loop": any("Nested Loops" in o for o in operators),
        "has_merge_join": any("Merge Join" in o for o in operators),
        "has_window": any(o in ["Segment", "Sequence Project"] for o in operators),
        "is_large": max_rows > HIGH_ROW_THRESHOLD,
        
        "has_key_lookup": any("KEY LOOKUP" in o.upper() for o in operators),

        # Missing-index evidence can also come from SQL Server plan warnings.
        "has_missing_index": any(
            "MISSING INDEX" in (op.get("operator", "") or "").upper()
            for op in plan_findings
        ),
    }

    return features


# ----------------------------
# Confidence mapping
# ----------------------------

def score_to_confidence(score):
    if score >= 0.6:
        return "high"
    elif score >= 0.3:
        return "medium"
    elif score > 0:
        return "low"
    return "none"


# ----------------------------
# Correlation logic
# ----------------------------

def correlate(static_findings, plan_findings):
    """Correlates static findings against runtime plan evidence and returns scored results."""
    
    runtime = extract_runtime_features(plan_findings)
    results = []

    for finding in static_findings:
        rule = normalize_static(finding)
        query_id = finding.get("query_id", "unknown")

        score = 0.0
        reasons = []

        # ---------------------------------
        # NON-SARGABLE
        # ---------------------------------
        if rule == "non_sargable_predicate":

            if runtime["has_scan"]:
                score += 0.7
                reasons.append("Scan detected (expected for non-sargable predicate)")

                if runtime["is_large"]:
                    score += 0.2
                    reasons.append("Large row count amplifies inefficiency")

            if runtime["has_seek"]:
                score -= 0.6
                reasons.append("Index Seek contradicts non-sargable expectation")

        # ---------------------------------
        # SELECT *
        # ---------------------------------
        elif rule == "select_star":

            if runtime["has_scan"]:
                score += 0.5
                reasons.append("Scan suggests wide row retrieval")

                if runtime["is_large"]:
                    score += 0.2
                    reasons.append("Large dataset increases impact")

        # ---------------------------------
        # COMPLEX JOIN
        # ---------------------------------
        elif rule == "complex_join":

            if runtime["has_hash_join"] or runtime["has_merge_join"]:
                score += 0.5
                reasons.append("Join operator confirms complexity")

                if runtime["is_large"]:
                    score += 0.2
                    reasons.append("Join cost amplified by dataset size")

        # ---------------------------------
        # ORDER BY NO INDEX
        # ---------------------------------
        elif rule == "order_by_no_index":

            if runtime["has_sort"]:
                score += 0.6
                reasons.append("Sort operator confirms missing index")

        # ---------------------------------
        # EXISTS / NOT EXISTS
        # ---------------------------------
        elif rule in ["exists_subquery", "not_exists_subquery"]:

            # Hash Join is a common implementation strategy for subquery logic.
            if runtime["has_hash_join"]:
                score += 0.5
                reasons.append("Hash Join suggests efficient subquery execution")

            # Nested Loops often reflect row-by-row subquery evaluation.
            if runtime["has_nested_loop"]:
                score += 0.4
                reasons.append("Nested Loop suggests row-by-row subquery evaluation")

            # Merge Join can also support efficient subquery execution.
            if runtime["has_merge_join"]:
                score += 0.4
                reasons.append("Merge Join can implement subquery logic efficiently")

            # Aggregation can indicate semi-join or deduplication behavior.
            if runtime["has_hash_agg"]:
                score += 0.2
                reasons.append("Aggregation suggests semi-join or deduplication behavior")

            if runtime["is_large"]:
                score += 0.1
                reasons.append("Large dataset increases subquery impact")

        # ---------------------------------
        # WINDOW FUNCTION
        # ---------------------------------
        elif rule == "window_function":

            if runtime["has_window"] or runtime["has_sort"]:
                score += 0.5
                reasons.append("Window operator or sort detected")

        # ---------------------------------
        # HAVING
        # ---------------------------------
        elif rule == "having_clause":

            if runtime["has_hash_agg"]:
                score += 0.5
                reasons.append("Hash Aggregate confirms HAVING")

        # ---------------------------------
        # CROSS / CARTESIAN JOIN
        # ---------------------------------
        elif rule in ["cross_join", "cartesian_join"]:

            if runtime["has_hash_join"] or runtime["has_nested_loop"]:
                score += 0.4
                reasons.append("Join operator confirms cross/cartesian join")

        # ---------------------------------
        # CORRELATED SUBQUERY
        # ---------------------------------
        elif rule == "correlated_subquery":

            if runtime["has_nested_loop"]:
                score += 0.6
                reasons.append("Nested Loop indicates row-by-row correlated execution")

            if runtime["is_large"]:
                score += 0.2
                reasons.append("High row count amplifies correlated subquery cost")

        # ---------------------------------
        # KEY LOOKUP (HIGH IMPACT)
        # ---------------------------------
        elif rule == "key_lookup":

            if runtime["has_key_lookup"]:
                score += 0.8
                reasons.append("Key Lookup detected (expensive row-by-row lookup)")

                if runtime["is_large"]:
                    score += 0.2
                    reasons.append("High row count amplifies lookup cost")

        # ---------------------------------
        # MISSING INDEX (IMPROVED — HIGH PRECISION)
        # ---------------------------------
        elif rule == "missing_index":

            # Strong signal 1: SQL Server explicitly recommends an index.
            if runtime["has_missing_index"]:
                score += 0.9
                reasons.append("SQL Server missing index recommendation detected")

            # Strong signal 2: Key Lookup often implies a missing covering index.
            if runtime["has_key_lookup"]:
                score += 0.7

                if runtime["max_rows"] > HIGH_ROW_THRESHOLD:
                    score += 0.2
                    reasons.append("High-volume key lookup strongly indicates missing covering index")

            if runtime["scan_count"] >= MIN_SCAN_COUNT and not runtime["has_seek"]:
                score += 0.4
                reasons.append("Multiple scans without seek suggests missing index")

            # Hard negative: a seek without a lookup usually indicates healthy index usage.
            if runtime["has_seek"] and not runtime["has_key_lookup"]:
                score -= 0.4
                reasons.append("Efficient index usage detected (no missing index)")

            # Only amplify if strong evidence already exists.
            if score >= 0.6 and runtime["is_large"]:
                score += 0.2
                reasons.append("Large dataset increases index benefit")
                
        # ---------------------------------
        # Final classification
        # ---------------------------------

        score = min(score, 1.0)

        # Weak scores are suppressed so low-evidence matches do not count as confirmed.
        suppressed = score < 0.3
        
        if suppressed:
            score = 0
            reasons = ["Insufficient runtime evidence"]
            
        confirmed = score > 0.3
        confidence = score_to_confidence(score)

        if not reasons:
            reasons.append("No significant runtime evidence")
            
        # Only some rules are eligible for runtime validation.
        is_validated = rule in RUNTIME_VERIFIABLE_RULES

        results.append({
            "query_id": query_id,
            "rule": rule,
            "confirmed": confirmed,
            "suppressed": suppressed,
            "validated": is_validated,
            "validation_type": "runtime" if is_validated else "static",
            "confidence": confidence,
            "score": round(score, 2),
            "evidence": {
                "operators": runtime["operators"],
                "max_estimated_rows": runtime["max_rows"],
                "scan_count": runtime["scan_count"]
            },
            "reason": "; ".join(reasons)
        })
        
    return results