"""
QueryLens — Expanded Runtime Evaluation Summary Generator

Produces a concise text summary of global runtime evaluation metrics
from the expanded workload report.

Purpose:
    - provide a lightweight, human-readable summary for research reports
    - highlight key aggregate metrics from runtime validation
    - complement detailed JSON evaluation outputs

Outputs:
    - total static warnings
    - total confirmed warnings
    - overall confirmation rate
"""

import json
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

REPORT_PATH = os.path.join(
    PROJECT_ROOT,
    "artifacts",
    "eval",
    "expanded_runtime_report.json"
)

OUTPUT_PATH = os.path.join(
    PROJECT_ROOT,
    "artifacts",
    "eval",
    "expanded_research_summary.txt"
)


def run():
    """
    Loads global runtime evaluation metrics and writes a formatted
    summary text file for reporting purposes.
    """
    with open(REPORT_PATH) as f:
        data = json.load(f)

    metrics = data["global_metrics"]


    # Build human-readable summary lines.
    lines = []
    lines.append("QueryLens Expanded Runtime Evaluation")
    lines.append("====================================")
    lines.append(f"Total Static Warnings: {metrics['total_static_warnings']}")
    lines.append(f"Confirmed Warnings: {metrics['total_confirmed_warnings']}")
    lines.append(f"Confirmation Rate: {metrics['confirmation_rate']}")

    # Write summary to output file.
    with open(OUTPUT_PATH, "w") as f:
        f.write("\n".join(lines))

    print("Expanded research summary generated")


if __name__ == "__main__":
    run()