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
    with open(REPORT_PATH) as f:
        data = json.load(f)

    metrics = data["global_metrics"]

    lines = []
    lines.append("QueryLens Expanded Runtime Evaluation")
    lines.append("====================================")
    lines.append(f"Total Static Warnings: {metrics['total_static_warnings']}")
    lines.append(f"Confirmed Warnings: {metrics['total_confirmed_warnings']}")
    lines.append(f"Confirmation Rate: {metrics['confirmation_rate']}")

    with open(OUTPUT_PATH, "w") as f:
        f.write("\n".join(lines))

    print("✔ Expanded research summary generated")


if __name__ == "__main__":
    run()