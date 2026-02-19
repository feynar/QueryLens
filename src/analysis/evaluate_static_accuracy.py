"""
QueryLens — Static Analysis Accuracy Evaluator (Week 9)

Compares AST-based detections against ground truth labels.
Produces quantitative accuracy metrics for research evaluation.
"""

import os
import json
from src.analysis.static_analyzer import analyze_sql

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

DATASET_DIR = os.path.join(PROJECT_ROOT, "datasets")
GROUND_TRUTH_PATH = os.path.join(DATASET_DIR, "ground_truth_static.json")
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "artifacts", "eval", "static_accuracy_report.json")


def load_ground_truth():
    with open(GROUND_TRUTH_PATH, "r") as f:
        return json.load(f)


def evaluate_query(sql_path, expected_issues):
    results = analyze_sql(sql_path)
    detected = sorted(r["issue_type"] for r in results)

    expected = sorted(expected_issues)

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


def run_evaluation():
    ground_truth = load_ground_truth()

    results = []

    for file_name, expected in ground_truth.items():
        sql_path = os.path.join(DATASET_DIR, file_name)

        if not os.path.exists(sql_path):
            print(f"⚠ Skipping missing file: {file_name}")
            continue

        results.append(evaluate_query(sql_path, expected))

    metrics = compute_global_metrics(results)

    report = {
        "per_query_results": results,
        "global_metrics": metrics
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    with open(OUTPUT_PATH, "w") as f:
        json.dump(report, f, indent=4)

    print("✔ Static accuracy evaluation complete")
    print(json.dumps(metrics, indent=4))


if __name__ == "__main__":
    run_evaluation()
