def apply_runtime_confidence(rule_instances):

    for r in rule_instances:

        if not r.get("runtime_verifiable", False):
            r["confidence"] = "static-only"
            continue

        if r.get("confirmed"):
            r["confidence"] = "high"

        elif r.get("runtime_verifiable"):
            r["confidence"] = "medium"

        else:
            r["confidence"] = "low"

    return rule_instances