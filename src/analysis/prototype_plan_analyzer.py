"""
Execution Plan Analyzer Responsibilities:

1. Parse SQL Server XML plan files (.sqlplan)
2. Extract:
    - physical operators
    - estimated rows
    - subtree cost
3. Convert operators → runtime issue signals

Used by:
    - correlation engine
    - runtime validation pipeline
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = PROJECT_ROOT / "artifacts"


def parse_plan(file_path):
    # Read raw bytes
    with open(file_path, "rb") as f:
        raw = f.read()

    # Decode safely
    try:
        xml_text = raw.decode("utf-16")
    except UnicodeError:
        xml_text = raw.decode("utf-8", errors="ignore")

    # Remove XML declaration if present
    if xml_text.startswith("<?xml"):
        xml_text = xml_text.split("?>", 1)[1]

    root = ET.fromstring(xml_text)

    ns = {"p": "http://schemas.microsoft.com/sqlserver/2004/07/showplan"}

    findings = []
    query_id = Path(file_path).stem

    for relop in root.findall(".//p:RelOp", ns):
        findings.append({
            "query_id": query_id,
            "operator": relop.get("PhysicalOp"),
            "logical_op": relop.get("LogicalOp"),  
            "estimated_rows": float(relop.get("EstimateRows") or 0),
            "subtree_cost": float(relop.get("EstimatedTotalSubtreeCost") or 0)
        })

    return findings

# -------------------------------------------------
# Week 10: Operator → runtime issue classification
# -------------------------------------------------
def classify_runtime_issues(plan_rows):
    """
    Converts raw operators into runtime performance evidence.
    Extended Week 16 to support EXISTS, WINDOW, HAVING, CROSS JOIN.
    """

    runtime_issues = []

    for row in plan_rows:
        op = (row.get("operator") or "").upper()

        # -------------------------
        # SCAN detection
        # -------------------------
        if "TABLE SCAN" in op or "INDEX SCAN" in op:
            runtime_issues.append({"issue_type": "FULL_SCAN"})

        # -------------------------
        # JOIN detection
        # -------------------------
        elif "HASH MATCH" in op:
            logical = (row.get("logical_op") or "").upper()

            if "JOIN" in logical:
                runtime_issues.append({"issue_type": "HASH_JOIN"})
            elif "AGGREGATE" in logical:
                runtime_issues.append({"issue_type": "HASH_AGGREGATE"})

        elif "MERGE JOIN" in op:
            runtime_issues.append({"issue_type": "MERGE_JOIN"})

        elif "NESTED LOOPS" in op:
            runtime_issues.append({"issue_type": "NESTED_LOOP"})

        # -------------------------
        # SORT detection
        # -------------------------
        elif "SORT" in op:
            runtime_issues.append({"issue_type": "SORT"})

        # -------------------------
        # WINDOW function detection (NEW)
        # -------------------------
        elif "SEGMENT" in op:
            runtime_issues.append({"issue_type": "WINDOW_FUNCTION"})

        elif "SEQUENCE PROJECT" in op:
            runtime_issues.append({"issue_type": "WINDOW_FUNCTION"})

        # -------------------------
        # Aggregation evidence (HAVING support)
        # -------------------------
        elif "STREAM AGGREGATE" in op:
            runtime_issues.append({"issue_type": "AGGREGATION"})

    return runtime_issues

def analyze_plan_file(plan_path):
    """
    Required by full_pipeline_evaluator.
    Returns runtime evidence in normalized format.
    """

    raw_rows = parse_plan(plan_path)
    return classify_runtime_issues(raw_rows)
    
def save_results(results):
    out_dir = ARTIFACTS / "analysis"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "plan_results.json"

    with open(out_path, "w") as f:
        json.dump(results, f, indent=4)

    print(f"Runtime plan results saved to {out_path}")
