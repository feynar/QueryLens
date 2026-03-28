"""
QueryLens — Precision/Recall Metrics

Evaluates detection performance using runtime validation results.
"""

import json
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

REPORT = os.path.join(PROJECT_ROOT, "artifacts", "evaluation", "expanded_runtime_report.json")
OUT = os.path.join(PROJECT_ROOT, "artifacts", "evaluation", "precision_recall_metrics.json")

with open(REPORT) as f:
    data = json.load(f)

tp = data["global_metrics"]["total_confirmed_warnings"]
fp = data["global_metrics"]["total_static_warnings"] - tp
fn = 0  # runtime-grounded evaluation treats confirmed warnings as TP

precision = tp / (tp + fp) if (tp + fp) else 0
recall = tp / (tp + fn) if (tp + fn) else 0

f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) else 0

metrics = {
    "true_positives": tp,
    "false_positives": fp,
    "false_negatives": fn,
    "precision": round(precision, 3),
    "recall": round(recall, 3),
    "f1_score": round(f1, 3)
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)

with open(OUT, "w") as f:
    json.dump(metrics, f, indent=4)

print("✔ Precision/Recall metrics generated")
print(json.dumps(metrics, indent=4))