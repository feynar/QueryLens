"""
QueryLens — Rule Level Metrics

Aggregates runtime-validation results into per-rule summary metrics.

Outputs, for each rule:
    - total static detections
    - runtime-verifiable detections
    - confirmed detections
    - precision
    - coverage
    - confidence distribution
"""

import os
import json
from collections import defaultdict

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

INPUT = os.path.join(PROJECT_ROOT, "artifacts", "evaluation", "expanded_runtime_report.json")
OUTPUT = os.path.join(PROJECT_ROOT, "artifacts", "evaluation", "rule_level_metrics.json")


def generate_rule_level_metrics():
    """
    Aggregates per-query runtime validation results into rule-level metrics.

    Computes:
        - total_static: total number of times a rule was detected statically
        - runtime_verifiable_static: subset eligible for runtime validation
        - confirmed: runtime-confirmed instances
        - precision: confirmed / runtime-verifiable static
        - coverage: runtime-verifiable static / total static
        - confidence distribution: high / medium / low breakdown
    """
    with open(INPUT) as f:
        data = json.load(f)

    # Aggregates metrics per rule across all queries.
    stats = defaultdict(lambda: {
        "total_static": 0,               # All static occurrences of the rule
        "runtime_verifiable_static": 0,  # Only occurrences eligible for runtime validation
        "confirmed": 0,
        "high": 0,
        "medium": 0,
        "low": 0
    })

    # Expected input structure:
    # data["per_query_results"] -> list of queries
    # each query contains "rule_instances" with runtime validation results
    for query in data["per_query_results"]:
        for r in query["rule_instances"]:
            rule = r["rule"]

            # Count every static occurrence of the rule.
            stats[rule]["total_static"] += 1

            # Only include rules that can be validated against runtime evidence.
            if not r["runtime_verifiable"]:
                continue

            stats[rule]["runtime_verifiable_static"] += 1

            if r["confirmed"]:
                stats[rule]["confirmed"] += 1

                if r["confidence"] == "high":
                    stats[rule]["high"] += 1
                elif r["confidence"] == "medium":
                    stats[rule]["medium"] += 1
                else:
                    stats[rule]["low"] += 1

    results = {}

    for rule, s in stats.items():
        # Precision: how often runtime confirms the static detection.
        precision = s["confirmed"] / s["runtime_verifiable_static"] if s["runtime_verifiable_static"] else None
        
        # Coverage: how many static detections are eligible for runtime validation.
        coverage = s["runtime_verifiable_static"] / s["total_static"] if s["total_static"] else 0

        results[rule] = {
            "total_static": s["total_static"],
            "runtime_verifiable_static": s["runtime_verifiable_static"],
            "confirmed": s["confirmed"],
            "precision": round(precision, 3) if precision is not None else None,
            "coverage": round(coverage, 3),
            "confidence_distribution": {
                "high": s["high"],
                "medium": s["medium"],
                "low": s["low"]
            }
        }

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

    with open(OUTPUT, "w") as f:
        json.dump(results, f, indent=4)

    print(f"✔ Rule-level metrics generated: {OUTPUT}")
    
if __name__ == "__main__":
    generate_rule_level_metrics()