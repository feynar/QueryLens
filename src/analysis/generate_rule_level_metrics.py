"""
QueryLens — Rule Level Metrics Generator (Week 16)

Computes precision per static rule using runtime validation results.

Input:
    artifacts/eval/expanded_runtime_report.json

Output:
    artifacts/eval/rule_level_metrics.json
"""

import os
import json
from collections import defaultdict


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

INPUT_PATH = os.path.join(
    PROJECT_ROOT,
    "artifacts",
    "eval",
    "expanded_runtime_report.json"
)

OUTPUT_PATH = os.path.join(
    PROJECT_ROOT,
    "artifacts",
    "eval",
    "rule_level_metrics.json"
)


def generate_metrics():

    if not os.path.exists(INPUT_PATH):
        raise FileNotFoundError("expanded_runtime_report.json not found")

    with open(INPUT_PATH, "r") as f:
        data = json.load(f)

    rule_stats = defaultdict(lambda: {"static": 0, "confirmed": 0})

    for query in data["per_query_results"]:

        static = query["static_warnings"]
        confirmed = query["confirmed_warnings"]

        # NOTE:
        # expanded report does not store rule names per query,
        # so we approximate by rule type embedded in filename

        name = query["query"].lower()

        if "selectstar" in name:
            rule = "SELECT_STAR"
        elif "nonsargable" in name or "functionpredicate" in name:
            rule = "NON_SARGABLE_PREDICATE"
        elif "join" in name:
            rule = "COMPLEX_JOIN"
        elif "sort" in name:
            rule = "ORDER_BY_NO_INDEX"
        else:
            rule = "OTHER"

        rule_stats[rule]["static"] += static
        rule_stats[rule]["confirmed"] += confirmed

    results = {}

    for rule, stats in rule_stats.items():

        static = stats["static"]
        confirmed = stats["confirmed"]

        precision = confirmed / static if static else 0

        results[rule] = {
            "static_detections": static,
            "confirmed_runtime": confirmed,
            "precision": round(precision, 3)
        }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    with open(OUTPUT_PATH, "w") as f:
        json.dump(results, f, indent=4)

    print("✔ Rule-level metrics generated")
    print(json.dumps(results, indent=4))


if __name__ == "__main__":
    generate_metrics()