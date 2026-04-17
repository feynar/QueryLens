"""
QueryLens — Global Validation Metrics

Computes validation-aware summary metrics from correlation output.

IMPORTANT:
These metrics do NOT measure true correctness.
They measure agreement between static analysis and runtime evidence.

Terminology:
    total_static_warnings = all detected issues
    validated_warnings = rules that can be runtime-validated
    runtime_confirmed = validated rules supported by runtime evidence
    runtime_suppressed = validated rules not supported by runtime
    agreement_rate = runtime_confirmed / validated_warnings

This avoids falsely claiming "precision" or "accuracy".
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

WEIGHTS = {
    "high": 1.0,
    "medium": 0.6,
    "low": 0.3
}


def generate_global_metrics(correlation_file, output_file):
    """
    Computes dataset-level validation-aware metrics from correlation results.

    Produces:
        - counts for total, validated, and static-only warnings
        - runtime-confirmed and runtime-suppressed counts
        - agreement_rate across runtime-verifiable rules
        - weighted_agreement_rate using confidence-based weights
    """    
    correlation_file = Path(correlation_file)
    output_file = Path(output_file)
    
    with open(correlation_file) as f:
        results = json.load(f)

    # Split all results into runtime-validatable findings and static-only findings.
    validated = [r for r in results if r.get("validated")]
    static_only = [r for r in results if not r.get("validated")]

    total_static = len(results)
    total_validated = len(validated)

    # Runtime agreement counts across rules eligible for validation.
    runtime_confirmed = sum(1 for r in validated if r.get("confirmed"))
    runtime_suppressed = sum(1 for r in validated if r.get("suppressed"))


    # Weighted agreement gives stronger credit to higher-confidence confirmations.
    weighted_confirmed = sum(
        WEIGHTS.get(r.get("confidence"), 0)
        for r in validated if r.get("confirmed")
    )

    # -----------------------------
    # FINAL METRICS
    # -----------------------------
    metrics = {
        # Dataset composition
        "total_static_warnings": total_static,
        "validated_warnings": total_validated,
        "static_only_warnings": len(static_only),

        # Runtime agreement (not true accuracy)
        "runtime_confirmed": runtime_confirmed,
        "runtime_suppressed": runtime_suppressed,

        # Agreement rates (not precision)
        "agreement_rate": round(runtime_confirmed / total_validated, 3) if total_validated else 0,
        "weighted_agreement_rate": round(weighted_confirmed / total_validated, 3) if total_validated else 0,

        # Transparency note for interpretation
        "notes": {
            "definition": "Agreement between static analysis and runtime execution plans",
            "limitation": "Does NOT represent true correctness due to lack of labeled ground truth"
        }
    }

    # Save the metrics output to disk.
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(metrics, f, indent=4)

    print("✔ Validation-aware metrics saved")


if __name__ == "__main__":
    generate_global_metrics(
        "artifacts/analysis/correlation_output.json",
        "artifacts/evaluation/evaluation_metrics.json"
    )