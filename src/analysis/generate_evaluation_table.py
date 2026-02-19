"""
QueryLens — Evaluation Table Generator (Week 9)

Creates CSV table for research report.
"""

import csv
import json
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

INPUT_PATH = os.path.join(PROJECT_ROOT, "artifacts", "eval", "static_accuracy_report.json")
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "artifacts", "reports", "static_evaluation_table.csv")


def generate_table():
    with open(INPUT_PATH, "r") as f:
        report = json.load(f)

    rows = report["per_query_results"]

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    with open(OUTPUT_PATH, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)

        writer.writerow([
            "query",
            "expected",
            "detected",
            "true_positive",
            "false_positive",
            "false_negative"
        ])

        for r in rows:
            writer.writerow([
                r["query"],
                ";".join(r["expected"]),
                ";".join(r["detected"]),
                r["true_positive"],
                r["false_positive"],
                r["false_negative"]
            ])

    print("✔ Evaluation table generated")


if __name__ == "__main__":
    generate_table()
