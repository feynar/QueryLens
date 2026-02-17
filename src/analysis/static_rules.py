def detect_issues_from_features(features, query_id):
    findings = []

    if features["has_select_star"]:
        findings.append({
            "query_id": query_id,
            "issue_type": "SELECT_STAR"
        })

    if features["non_sargable_functions"]:
        findings.append({
            "query_id": query_id,
            "issue_type": "NON_SARGABLE_PREDICATE"
        })

    if features["join_count"] >= 2:
        findings.append({
            "query_id": query_id,
            "issue_type": "COMPLEX_JOIN"
        })

    return findings
