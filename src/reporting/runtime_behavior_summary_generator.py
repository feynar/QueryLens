"""
QueryLens — Runtime Behavior Summary Generator

Produces a human-readable summary of execution plan behavior
across the expanded runtime validation workload.
"""

import json
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

DIST_FILE = os.path.join(PROJECT_ROOT, "artifacts", "eval", "runtime_operator_distribution.json")
OUT_FILE = os.path.join(PROJECT_ROOT, "artifacts", "eval", "runtime_behavior_summary.txt")

with open(DIST_FILE) as f:
    data = json.load(f)

total = sum(data.values())

lines = []
lines.append("QueryLens Runtime Behavior Summary")
lines.append("=================================\n")

for op, count in sorted(data.items(), key=lambda x: x[1], reverse=True):
    pct = round((count / total) * 100, 2)
    lines.append(f"{op}: {count} occurrences ({pct}%)")

lines.append("\nInterpretation:")
lines.append("Index Seek operators indicate efficient index usage.")
lines.append("Index Scan operators suggest potential non-sargable predicates or low selectivity filters.")
lines.append("Hash Match operators are typically produced by large join or aggregation operations.")
lines.append("Sort operators occur when ordering cannot be satisfied by an index.")

os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)

with open(OUT_FILE, "w") as f:
    f.write("\n".join(lines))

print("✔ Runtime behavior summary generated")