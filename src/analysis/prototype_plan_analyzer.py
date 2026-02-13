"""
QueryLens Prototype — Execution Plan Analyzer (Week 5)

Parses SQL Server execution plan (.sqlplan XML) files and extracts
operators and estimated row counts for correlation.
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = PROJECT_ROOT / "artifacts"


def parse_plan(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    ns = {"p": "http://schemas.microsoft.com/sqlserver/2004/07/showplan"}

    findings = []
    query_id = Path(file_path).stem

    for relop in root.findall(".//p:RelOp", ns):
        findings.append({
            "query_id": query_id,
            "operator": relop.get("PhysicalOp"),
            "estimated_rows": float(relop.get("EstimateRows") or 0),
            "subtree_cost": float(relop.get("EstimatedTotalSubtreeCost") or 0)
        })

    return findings


def save_results(results):
    out_dir = ARTIFACTS / "analyzer"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "plan_results.json"

    with open(out_path, "w") as f:
        json.dump(results, f, indent=4)

    print(f"Runtime plan results saved to {out_path}")
