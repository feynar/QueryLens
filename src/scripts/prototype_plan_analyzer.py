"""
QueryLens Prototype — Execution Plan Analyzer (Week 5)

Parses SQL Server execution plan (.sqlplan XML) files and extracts
operators and estimated row counts for correlation.
"""

import json
import os
import sys
import xml.etree.ElementTree as ET


def parse_plan(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()

    ns = {"p": "http://schemas.microsoft.com/sqlserver/2004/07/showplan"}

    findings = []
    query_id = os.path.splitext(os.path.basename(file_path))[0]

    for relop in root.findall(".//p:RelOp", ns):
        physical_op = relop.get("PhysicalOp")
        est_rows = relop.get("EstimateRows")
        subtree_cost = relop.get("EstimatedTotalSubtreeCost")

        findings.append({
            "query_id": query_id,
            "operator": physical_op,
            "estimated_rows": float(est_rows) if est_rows else 0,
            "subtree_cost": float(subtree_cost) if subtree_cost else 0
        })

    return findings


def save_results(results):
    os.makedirs("artifacts", exist_ok=True)
    out_path = os.path.join("artifacts", "runtime_results.json")

    with open(out_path, "w") as f:
        json.dump(results, f, indent=4)

    print(f"Runtime results saved to {out_path}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python prototype_plan_analyzer.py <plan.sqlplan>")
        sys.exit(1)

    plan_file = sys.argv[1]
    results = parse_plan(plan_file)
    save_results(results)