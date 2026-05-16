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
    effective_rows = []
    estimated_rows = []
    actual_rows = []

    actual_operator_count = 0
    actual_executed = False
    
    for op in plan_findings:
        physical = op.get("operator", "")
        logical = op.get("logical_op", "")
   
        est = float(op.get("estimated_rows") or 0)
        actual = float(op.get("actual_rows") or 0)
        actual_execs = float(op.get("actual_executions") or 0)
        has_actual = bool(op.get("has_actual_runtime_stats"))
        
        operators.append(physical)
        logical_ops.append(logical)
        estimated_rows.append(est)
        actual_rows.append(actual)
        
        if actual_execs > 0:
            actual_executed = True

        if has_actual:
            actual_operator_count += 1
            effective_rows.append(actual)
        else:
            effective_rows.append(est)

    max_rows = max(effective_rows, default=0)
    max_estimated_rows = max(estimated_rows, default=0)
    max_actual_rows = max(actual_rows, default=0)
    
    scan_count = sum(
        "SCAN" in (o or "").upper()
        for o in operators
    )
    
    has_actual_stats = actual_operator_count > 0
    actual_is_large = max_actual_rows > HIGH_ROW_THRESHOLD if has_actual_stats else False
    estimate_is_large = max_estimated_rows > HIGH_ROW_THRESHOLD
    
    features = {
        "operators": operators,
        "logical_ops": logical_ops,

        # Effective row count prefers actual rows, falls back to estimated rows.
        "max_rows": max_rows,
        "max_estimated_rows": max_estimated_rows,
        "max_actual_rows": max_actual_rows,


        "has_actual_stats": has_actual_stats,
        "actual_rows_available": has_actual_stats,
        "actual_operator_count": actual_operator_count,
        "actual_stats_coverage": round(
            actual_operator_count / len(plan_findings), 3
        ) if plan_findings else 0,

        "actual_executed": actual_executed,
        "actual_is_large": actual_is_large,
        "estimate_is_large": estimate_is_large,

        "scan_count": scan_count,
        "has_scan": scan_count > 0,
        "has_seek": any("SEEK" in (o or "").upper() for o in operators),
        "has_sort": any("SORT" in (o or "").upper() for o in operators),
        "has_hash_join": any("HASH MATCH" in (o or "").upper() for o in operators),
        "has_hash_agg": any("AGGREGATE" in (l or "").upper() for l in logical_ops),
        "has_nested_loop": any("NESTED LOOPS" in (o or "").upper() for o in operators),
        "has_merge_join": any("MERGE JOIN" in (o or "").upper() for o in operators),
        "has_window": any(
            (o or "").upper() in ["SEGMENT", "SEQUENCE PROJECT", "WINDOW AGGREGATE"]
            for o in operators
        ),

        "is_large": max_rows > HIGH_ROW_THRESHOLD,

        "has_key_lookup": any("KEY LOOKUP" in (o or "").upper() for o in operators),

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


def add_row_volume_reason(runtime, reasons, estimated_message, actual_message):
    """
    Adds a row-volume explanation that distinguishes actual runtime evidence
    from estimated-plan fallback evidence.
    """
    if runtime["has_actual_stats"]:
        reasons.append(actual_message)
    else:
        reasons.append(estimated_message)
        
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
                reasons.append("Scan detected, which is expected for a non-sargable predicate")

                if runtime["is_large"]:
                    score += 0.2
                    add_row_volume_reason(
                        runtime,
                        reasons,
                        "High estimated row count amplifies non-sargable predicate impact",
                        "High actual row count amplifies non-sargable predicate impact"
                    )

            if runtime["has_seek"]:
                score -= 0.6
                reasons.append("Index Seek contradicts non-sargable scan expectation")

        # ---------------------------------
        # SELECT *
        # ---------------------------------
        elif rule == "select_star":

            if runtime["has_scan"]:
                score += 0.5
                reasons.append("Scan suggests broad row retrieval")

                if runtime["is_large"]:
                    score += 0.2
                    add_row_volume_reason(
                        runtime,
                        reasons,
                        "High estimated row count increases SELECT * impact",
                        "High actual row count increases SELECT * impact"
                    )

        # ---------------------------------
        # COMPLEX JOIN
        # ---------------------------------
        elif rule == "complex_join":

            if runtime["has_hash_join"] or runtime["has_merge_join"]:
                score += 0.5
                reasons.append("Join operator confirms multi-table runtime complexity")

                if runtime["is_large"]:
                    score += 0.2
                    add_row_volume_reason(
                        runtime,
                        reasons,
                        "High estimated row count amplifies join cost",
                        "High actual row count amplifies join cost"
                    )

        # ---------------------------------
        # ORDER BY NO INDEX
        # ---------------------------------
        elif rule == "order_by_no_index":

            if runtime["has_sort"]:
                score += 0.5
                reasons.append("Sort operator detected")

                if runtime["has_actual_stats"] and runtime["actual_is_large"]:
                    score += 0.2
                    reasons.append("Sort processed high actual row volume")
                elif runtime["estimate_is_large"]:
                    score += 0.1
                    reasons.append("Sort estimated high row volume")

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
                add_row_volume_reason(
                    runtime,
                    reasons,
                    "High estimated row count increases subquery impact",
                    "High actual row count increases subquery impact"
                )

        # ---------------------------------
        # WINDOW FUNCTION
        # ---------------------------------
        elif rule == "window_function":

            if runtime["has_window"] or runtime["has_sort"]:
                score += 0.5
                reasons.append("Window operator or sort detected")

                if runtime["has_actual_stats"] and runtime["actual_is_large"]:
                    score += 0.1
                    reasons.append("Window processing involved high actual row volume")
                    
        # ---------------------------------
        # HAVING
        # ---------------------------------
        elif rule == "having_clause":

            if runtime["has_hash_agg"]:
                score += 0.5
                reasons.append("Aggregate operator confirms HAVING-related runtime work")

                if runtime["has_actual_stats"] and runtime["actual_is_large"]:
                    score += 0.1
                    reasons.append("Aggregation processed high actual row volume")


        # ---------------------------------
        # CROSS / CARTESIAN JOIN
        # ---------------------------------
        elif rule in ["cross_join", "cartesian_join"]:

            if runtime["has_hash_join"] or runtime["has_nested_loop"]:
                score += 0.4
                reasons.append("Join operator confirms cross/cartesian join execution")

                if runtime["has_actual_stats"] and runtime["actual_is_large"]:
                    score += 0.2
                    reasons.append("Cross/cartesian join produced high actual row volume")

        # ---------------------------------
        # CORRELATED SUBQUERY
        # ---------------------------------
        elif rule == "correlated_subquery":

            if runtime["has_nested_loop"]:
                score += 0.6
                reasons.append("Nested Loop indicates row-by-row correlated execution")

            if runtime["is_large"]:
                score += 0.2
                add_row_volume_reason(
                    runtime,
                    reasons,
                    "High estimated row count amplifies correlated subquery cost",
                    "High actual row count amplifies correlated subquery cost"
                )

        # ---------------------------------
        # KEY LOOKUP (HIGH IMPACT)
        # ---------------------------------
        elif rule == "key_lookup":

            if runtime["has_key_lookup"]:
                score += 0.8
                reasons.append("Key Lookup detected, indicating row-by-row lookup behavior")

                if runtime["is_large"]:
                    score += 0.2
                    add_row_volume_reason(
                        runtime,
                        reasons,
                        "High estimated row count amplifies lookup cost",
                        "High actual row count amplifies lookup cost"
                    )

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
                reasons.append("Key Lookup suggests a possible missing covering index")
                
                if runtime["max_rows"] > HIGH_ROW_THRESHOLD:
                    score += 0.2
                    add_row_volume_reason(
                        runtime,
                        reasons,
                        "High estimated row volume strengthens missing-index evidence",
                        "High actual row volume strengthens missing-index evidence"
                    )

            if runtime["scan_count"] >= MIN_SCAN_COUNT and not runtime["has_seek"]:
                score += 0.4
                reasons.append("Multiple scans without seek suggest missing index opportunity")

            # Hard negative: a seek without a lookup usually indicates healthy index usage.
            if runtime["has_seek"] and not runtime["has_key_lookup"]:
                score -= 0.4
                reasons.append("Efficient index usage detected without key lookup")

            # Only amplify if strong evidence already exists.
            if score >= 0.6 and runtime["is_large"]:
                score += 0.2
                add_row_volume_reason(
                    runtime,
                    reasons,
                    "Large estimated dataset increases possible index benefit",
                    "Large actual dataset increases possible index benefit"
                )

        # ---------------------------------
        # Actual runtime suppression / boost
        # ---------------------------------
        if runtime["has_actual_stats"]:

            if runtime["actual_executed"] and not runtime["actual_is_large"]:
                if score < 0.5:
                    score -= 0.1
                    reasons.append(
                        "Actual runtime rows were low, slightly reducing confirmation strength"
                    )

            if runtime["actual_is_large"] and score > 0:
                score += 0.1
                reasons.append(
                    f"Actual runtime row evidence supports impact; max actual rows = {runtime['max_actual_rows']}"
                )
            
        # ---------------------------------
        # Final classification
        # ---------------------------------

        score = max(0.0, min(score, 1.0))

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
                "max_rows": runtime["max_rows"],
                "max_estimated_rows": runtime["max_estimated_rows"],
                "max_actual_rows": runtime["max_actual_rows"],
                "scan_count": runtime["scan_count"],
                "has_actual_stats": runtime["has_actual_stats"],
                "actual_operator_count": runtime["actual_operator_count"],
                "actual_stats_coverage": runtime["actual_stats_coverage"],
                "actual_executed": runtime["actual_executed"],
                "actual_is_large": runtime["actual_is_large"],
                "estimate_is_large": runtime["estimate_is_large"]                
            },
            "reason": "; ".join(reasons)
        })
        
    return results