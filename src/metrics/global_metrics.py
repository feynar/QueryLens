"""
Computes global confirmation metrics from correlation output.

Definitions:
    static_warnings = total detected issues
    confirmed = issues supported by runtime evidence
    suppressed = static warnings not confirmed
    confirmation_rate = confirmed / static_warnings

Used for:
    - system evaluation
    - research reporting
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

WEIGHTS = {
    "high": 1.0,
    "medium": 0.6,
    "low": 0.3
}


def generate_metrics(correlation_file, output_file):
    with open(correlation_file) as f:
        results = json.load(f)

    total = len(results)

    confirmed = sum(1 for r in results if r["confirmed"])

    weighted = sum(
        WEIGHTS.get(r["confidence"], 0)
        for r in results if r["confirmed"]
    )

    metrics = {
        "static_warnings": total,
        "confirmed": confirmed,
        "weighted_confirmed": round(weighted, 2),
        "confirmation_rate": round(confirmed / total if total else 0, 3),
        "weighted_confirmation_rate": round(weighted / total if total else 0, 3)
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(metrics, f, indent=4)

    print("✔ Evaluation metrics saved")

if __name__ == "__main__":
    generate_metrics(
        "artifacts/correlation_output.json",
        "artifacts/evaluation_metrics.json"
    )