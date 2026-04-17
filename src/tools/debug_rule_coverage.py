"""
QueryLens — Rule Coverage Debug Tool

Provides a simple diagnostic view of static rule detection across
the SQL workload.

Purpose:
    - verify that each query triggers expected rules
    - validate coverage of the test workload
    - assist debugging of feature extraction and rule evaluation

Output:
    - prints a table mapping each query file to detected rule names
    - displays "-" for queries with no detected rules
"""

import os

from src.analysis.static_analyzer import analyze_sql
from src.correlation.correlator import normalize_static


# -------------------------------------------------
# Path configuration
# -------------------------------------------------

# Resolve project root relative to this file
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Directory containing SQL workload files
QUERY_DIR = os.path.join(PROJECT_ROOT, "plans")

# -------------------------------------------------
# Main debug routine
# -------------------------------------------------

def run_debug():
    """
    Executes rule coverage analysis across all SQL files.

    For each query:
        - runs static analysis
        - normalizes detected rule names
        - prints a formatted summary row

    Intended for development and validation use only.
    """
    print("\nQUERY RULE COVERAGE\n")
    print(f"{'QUERY':40} RULES DETECTED")
    print("-" * 65)

    # Iterate through all SQL files in workload
    for file in sorted(os.listdir(QUERY_DIR)):

        # Skip non-SQL files
        if not file.endswith(".sql"):
            continue

        path = os.path.join(QUERY_DIR, file)

        # Run static analysis
        findings = analyze_sql(path)
        
        # Normalize rule names for consistency
        rules = [normalize_static(f) for f in findings]
        
        # Format output
        if rules:
            rule_string = ", ".join(rules)
        else:
            rule_string = "-"

        print(f"{file:40} {rule_string}")


if __name__ == "__main__":
    run_debug()