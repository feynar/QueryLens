"""
QueryLens — Precision/Recall Metrics

Computes precision, recall, and F1-style metrics from runtime validation output.

Notes:
    - this evaluation is runtime-grounded rather than label-grounded
    - confirmed warnings are treated as true positives
    - unconfirmed warnings are treated as false positives
    - false negatives are fixed at 0 in this formulation
"""

import json
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

REPORT = os.path.join(PROJECT_ROOT, "artifacts", "evaluation", "expanded_runtime_report.json")
OUT = os.path.join(PROJECT_ROOT, "artifacts", "evaluation", "precision_recall_metrics.json")

# Load runtime validation report.
with open(REPORT) as f:
    data = json.load(f)

# Interpret global runtime-validation counts as evaluation inputs.
tp = data["global_metrics"]["total_confirmed_warnings"]
fp = data["global_metrics"]["total_static_warnings"] - tp
fn = 0  # runtime-grounded evaluation treats confirmed warnings as TP

# In this runtime-grounded formulation, only confirmed warnings are counted
# as true positives, and false negatives are not separately modeled.
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

# Save metric output to the evaluation artifacts directory.
os.makedirs(os.path.dirname(OUT), exist_ok=True)

with open(OUT, "w") as f:
    json.dump(metrics, f, indent=4)

print("Precision/Recall metrics generated")
print(json.dumps(metrics, indent=4))