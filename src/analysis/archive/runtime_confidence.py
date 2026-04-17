"""
QueryLens — Runtime Confidence Assignment

Assigns confidence labels to rule instances based on their runtime
validation status.

Confidence mapping:
    - static-only: rule is not eligible for runtime validation
    - high: runtime-verifiable rule confirmed by runtime evidence
    - medium: runtime-verifiable rule not confirmed, but still eligible
    - low: fallback label for any remaining unmatched case
"""


def apply_runtime_confidence(rule_instances):
    """
    Assigns confidence labels in place for a list of rule instances.

    Parameters:
        rule_instances (list): Rule dictionaries containing runtime validation fields

    Returns:
        list: The same list with updated confidence labels
    """

    for r in rule_instances:

        # Rules that cannot be checked against runtime evidence are labeled separately.
        if not r.get("runtime_verifiable", False):
            r["confidence"] = "static-only"
            continue

        # Confirmed runtime-verifiable rules receive the highest confidence.
        if r.get("confirmed"):
            r["confidence"] = "high"

        # Runtime-verifiable but unconfirmed rules are treated as medium confidence.
        elif r.get("runtime_verifiable"):
            r["confidence"] = "medium"

        # Fallback label for any unexpected or incomplete case.
        else:
            r["confidence"] = "low"

    return rule_instances