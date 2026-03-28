"""
QueryLens — Research Results Table Generator (Week 10)

Formats evaluation outputs into report-ready tables.
"""

import os
import json

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

STATIC_EVAL_PATH = os.path.join(PROJECT_ROOT, "artifacts", "eval", "static_accuracy_report.json")
PIPELINE_EVAL_PATH = os.path.join(PROJECT_ROOT, "artifacts", "eval", "full_pipeline_report.json")

OUTPUT_PATH = os.path.join(PROJECT_ROOT, "artifacts", "eval", "research_summary.txt")


def generate_summary():
    with open(STATIC_EVAL_PATH, "r") as f:
        static_eval = json.load(f)

    with open(PIPELINE_EVAL_PATH, "r") as f:
        pipeline_eval = json.load(f)

    static_metrics = static_eval["global_metrics"]
    pipeline_metrics = pipeline_eval["global_metrics"]

    lines = []
    lines.append("QueryLens Experimental Results\n")
    lines.append("================================\n")

    lines.append("Static Detection Accuracy\n")
    lines.append(f"Precision: {static_metrics['precision']}\n")
    lines.append(f"Recall: {static_metrics['recall']}\n")
    lines.append(f"F1 Score: {static_metrics['f1_score']}\n\n")

    lines.append("Runtime Validation Effectiveness\n")
    lines.append(f"Total Static Warnings: {pipeline_metrics['total_static_warnings']}\n")
    lines.append(f"Confirmed Warnings: {pipeline_metrics['total_confirmed_warnings']}\n")
    lines.append(f"Confirmation Rate: {pipeline_metrics['confirmation_rate']}\n")

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    with open(OUTPUT_PATH, "w") as f:
        f.writelines(lines)

    print("✔ Research summary generated")


if __name__ == "__main__":
    generate_summary()
