"""
QueryLens — Rule Level Metrics Generator (Week 17)

Computes:
- Precision
- Confirmation rate
- False positives

Input:
    artifacts/eval/expanded_runtime_report.json

Output:
    artifacts/eval/rule_level_metrics.json
"""

import os
import json
from collections import defaultdict

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

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

    rule_stats = defaultdict(lambda: {
        "queries": set(),
        "static": 0,
        "confirmed": 0
    })

    for query in data["per_query_results"]:

        query_name = query["query"]

        for instance in query["rule_instances"]:

            rule = instance["rule"].upper()

            rule_stats[rule]["static"] += 1
            rule_stats[rule]["queries"].add(query_name)

            if instance["confirmed"]:
                rule_stats[rule]["confirmed"] += 1

    results = {}

    for rule, stats in rule_stats.items():

        static = stats["static"]
        confirmed = stats["confirmed"]
        queries = len(stats["queries"])

        precision = confirmed / static if static else 0
        confirmation_rate = confirmed / static if static else 0
        false_positives = static - confirmed

        results[rule] = {
            "queries_with_rule": queries,
            "static_detections": static,
            "confirmed_runtime": confirmed,
            "false_positives": false_positives,
            "precision": round(precision, 3),
            "confirmation_rate": round(confirmation_rate, 3)
        }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    with open(OUTPUT_PATH, "w") as f:
        json.dump(results, f, indent=4)

    print("✔ Rule-level metrics generated\n")
    print(json.dumps(results, indent=4))


if __name__ == "__main__":
    generate_metrics()