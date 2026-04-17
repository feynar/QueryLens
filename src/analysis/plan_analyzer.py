"""
QueryLens — Execution Plan Analyzer

Responsibilities:
    1. Parse SQL Server XML plan files (.sqlplan)
    2. Extract key plan attributes such as:
        - physical operators
        - logical operators
        - estimated rows
        - subtree cost
    3. Convert operators into normalized runtime issue signals

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
    """
    Parses a SQL Server .sqlplan XML file into a list of operator-level findings.

    Extracts:
        - physical operator
        - logical operator
        - estimated rows
        - estimated subtree cost
        - missing-index warning signal
    """
    # Read the raw plan bytes first so decoding can be handled safely.
    with open(file_path, "rb") as f:
        raw = f.read()

    # SQL Server plans are often UTF-16, but fall back to UTF-8 if needed.
    try:
        xml_text = raw.decode("utf-16")
    except UnicodeError:
        xml_text = raw.decode("utf-8", errors="ignore")
        
    # Remove the XML declaration if present before parsing.
    if xml_text.startswith("<?xml"):
        xml_text = xml_text.split("?>", 1)[1]

    root = ET.fromstring(xml_text)

    ns = {"p": "http://schemas.microsoft.com/sqlserver/2004/07/showplan"}

    findings = []
    query_id = Path(file_path).stem

    for relop in root.findall(".//p:RelOp", ns):

        physical_op = relop.get("PhysicalOp", "")
        logical_op = relop.get("LogicalOp", "")

        # Missing-index hints can appear as plan warnings inside a RelOp subtree.
        missing_index = relop.find(".//p:MissingIndex", ns)
        if missing_index is not None:
            physical_op += " | MISSING INDEX"

        findings.append({
            "query_id": query_id,
            "operator": physical_op,
            "logical_op": logical_op,
            "estimated_rows": float(relop.get("EstimateRows") or 0),
            "subtree_cost": float(relop.get("EstimatedTotalSubtreeCost") or 0)
        })

    return findings

def classify_runtime_issues(plan_rows):
    """
    Converts raw plan operators into normalized runtime evidence categories.

    These issue labels are used by downstream evaluation and reporting logic.
    Extended to support EXISTS / NOT EXISTS, window functions, HAVING,
    and CROSS JOIN-related signals.
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
        # JOIN and HASH AGGREGATE detection
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
        # WINDOW function detection
        # -------------------------
        elif "SEGMENT" in op:
            runtime_issues.append({"issue_type": "WINDOW_FUNCTION"})

        elif "SEQUENCE PROJECT" in op:
            runtime_issues.append({"issue_type": "WINDOW_FUNCTION"})

        # -------------------------
        # Aggregation evidence
        # -------------------------
        elif "STREAM AGGREGATE" in op:
            runtime_issues.append({"issue_type": "AGGREGATION"})


        # -------------------------
        # KEY LOOKUP detection
        # -------------------------
        elif "KEY LOOKUP" in op:
            runtime_issues.append({"issue_type": "KEY_LOOKUP"})

    return runtime_issues

def analyze_plan_file(plan_path):
    """
    Parses a plan file and returns normalized runtime issue evidence.

    This is a convenience wrapper used by pipeline-level evaluation code.
    """

    raw_rows = parse_plan(plan_path)
    return classify_runtime_issues(raw_rows)
    
def save_results(results):
    """Saves parsed runtime plan results to the analysis artifacts directory."""
    out_dir = ARTIFACTS / "analysis"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "plan_results.json"

    with open(out_path, "w") as f:
        json.dump(results, f, indent=4)

    print(f"Runtime plan results saved to {out_path}")
