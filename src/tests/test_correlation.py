import json
import os
import sys

# Allow importing from src/scripts
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
from correlator import correlate

# Get project root (QueryLens/)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

static_path = os.path.join(BASE_DIR, "artifacts", "static_results.json")
runtime_path = os.path.join(BASE_DIR, "artifacts", "runtime_results.json")

with open(static_path) as f:
    static_data = json.load(f)

with open(runtime_path) as f:
    runtime_data = json.load(f)

results = correlate(static_data, runtime_data)

assert any(r["confirmed"] for r in results), "No correlations confirmed!"
print("Correlation test passed.")
