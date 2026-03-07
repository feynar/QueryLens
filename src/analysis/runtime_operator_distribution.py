"""
QueryLens — Runtime Operator Distribution (Week 16)

Counts operator frequency across execution plans.
Output used for thesis runtime behavior analysis.
"""

import os
import json
from collections import Counter
from src.analysis.prototype_plan_analyzer import parse_plan

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PLAN_DIR = os.path.join(PROJECT_ROOT, "plans_expanded")
OUTPUT = os.path.join(PROJECT_ROOT, "artifacts", "eval", "runtime_operator_distribution.json")

counter = Counter()

for file in os.listdir(PLAN_DIR):
    if file.endswith(".sqlplan"):
        rows = parse_plan(os.path.join(PLAN_DIR, file))
        for r in rows:
            counter[r["operator"]] += 1

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
with open(OUTPUT, "w") as f:
    json.dump(counter, f, indent=4)

print("✔ Runtime operator distribution generated")
print(json.dumps(counter, indent=4))