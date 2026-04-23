"""
QueryLens — Static Analysis Accuracy Evaluator

Compares AST-based static detections against ground-truth labels
and computes quantitative evaluation metrics.

Outputs:
    - per-query expected vs detected issues
    - true positives, false positives, and false negatives
    - global precision, recall, and F1 score
"""

import os
import json
from src.analysis.static_analyzer import analyze_sql

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

PLANS_DIR = os.path.join(PROJECT_ROOT, "plans")
DATASET_DIR = os.path.join(PROJECT_ROOT, "datasets")
GROUND_TRUTH_PATH = os.path.join(DATASET_DIR, "ground_truth_static.json")
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "artifacts", "detection_results.json")

# Only evaluate the rules intentionally included in the labeled ground truth.
EVALUATED_RULES = {
    "select_star",
    "non_sargable_predicate",
    "complex_join",
    "order_by_no_index",
    "exists_subquery",
    "not_exists_subquery",
    "correlated_subquery",
    "cross_join",
    "having_clause",
    "derived_table",
    "window_function",
}


def load_ground_truth():
    """Loads the ground-truth label file used for static accuracy evaluation."""
    with open(GROUND_TRUTH_PATH, "r") as f:
        return json.load(f)


def evaluate_query(sql_path, expected_issues):
    """
    Evaluates one SQL file against its expected ground-truth issue labels.

    Returns:
        dict: expected issues, detected issues, and per-query TP / FP / FN counts
    """
    results = analyze_sql(sql_path)

    # Normalize detected issue labels into a sorted list for comparison.
    detected = sorted(
        r["rule"] for r in results
        if r["rule"] in EVALUATED_RULES
    )

    expected = sorted(
        rule for rule in expected_issues
        if rule in EVALUATED_RULES
    )

    tp = len(set(detected) & set(expected))
    fp = len(set(detected) - set(expected))
    fn = len(set(expected) - set(detected))

    return {
        "query": os.path.basename(sql_path),
        "expected": expected,
        "detected": detected,
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn
    }


def compute_global_metrics(rows):
    """
    Aggregates per-query counts into dataset-level precision, recall, and F1.
    """
    total_tp = sum(r["true_positive"] for r in rows)
    total_fp = sum(r["false_positive"] for r in rows)
    total_fn = sum(r["false_negative"] for r in rows)

    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) else 0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) else 0

    if precision + recall:
        f1 = 2 * precision * recall / (precision + recall)
    else:
        f1 = 0

    return {
        "total_true_positive": total_tp,
        "total_false_positive": total_fp,
        "total_false_negative": total_fn,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1_score": round(f1, 3)
    }


def run_static_accuracy_evaluation():
    """
    Runs static accuracy evaluation across the labeled dataset and writes
    the resulting report to the evaluation artifacts directory.
    """
    ground_truth = load_ground_truth()

    results = []

    for file_name, expected in ground_truth.items():
        sql_path = os.path.join(PLANS_DIR, file_name)

        # Skip ground-truth entries whose SQL files are missing.
        if not os.path.exists(sql_path):
            print(f"Skipping missing file: {file_name}")
            continue

        results.append(evaluate_query(sql_path, expected))

    metrics = compute_global_metrics(results)

    report = {
        "evaluated_rules": sorted(EVALUATED_RULES),
        "per_query_results": results,
        "global_metrics": metrics
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    with open(OUTPUT_PATH, "w") as f:
        json.dump(report, f, indent=4)

    print("Static accuracy evaluation complete")
    print(json.dumps(metrics, indent=4))


if __name__ == "__main__":
    run_static_accuracy_evaluation()
