"""
QueryLens — Runtime Operator Distribution

Counts the frequency of execution plan operators across the expanded workload.

Purpose:
    - provide empirical insight into runtime behavior patterns
    - support analysis of operator prevalence (e.g., scans, seeks, joins)
    - feed downstream reporting modules (e.g., behavior summaries)

Output:
    - JSON file mapping operator names to occurrence counts
"""

import os
import json
from collections import Counter
from src.analysis.plan_analyzer import parse_plan

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PLAN_DIR = os.path.join(PROJECT_ROOT, "plans_expanded")
OUTPUT = os.path.join(PROJECT_ROOT, "artifacts", "eval", "runtime_operator_distribution.json")

# -------------------------------------------------
# Operator frequency aggregation
# -------------------------------------------------
counter = Counter()

# Iterate through all execution plan files in the expanded workload.
for file in os.listdir(PLAN_DIR):
    if file.endswith(".sqlplan"):
        rows = parse_plan(os.path.join(PLAN_DIR, file))
        for r in rows:
            counter[r["operator"]] += 1

# -------------------------------------------------
# Output
# -------------------------------------------------

# Ensure output directory exists.
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

# Write operator distribution to JSON file.
with open(OUTPUT, "w") as f:
    json.dump(counter, f, indent=4)

print("Runtime operator distribution generated")
print(json.dumps(counter, indent=4))