"""
QueryLens — Execution Plan Analyzer

Responsibilities:
    1. Parse SQL Server XML plan files (.sqlplan)
    2. Extract key plan attributes such as:
        - physical operators
        - logical operators
        - estimated rows
        - actual rows
        - actual executions
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
        - actual rows
        - actual executions
        - estimated subtree cost
        - missing-index warning signal
    """
    
    # Read the raw plan bytes first so decoding can be handled safely.
    with open(file_path, "rb") as f:
        raw = f.read()

    # Live-captured plans are saved as UTF-8, while manually exported
    # SQL Server plans may be UTF-16. Try UTF-8 first to avoid decoding
    # UTF-8 live plans incorrectly as UTF-16.
    try:
        xml_text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            xml_text = raw.decode("utf-16")
        except UnicodeError:
            xml_text = raw.decode("utf-8", errors="ignore")

    xml_text = xml_text.strip()

    # Remove XML declaration if present before parsing.
    if xml_text.startswith("<?xml"):
        xml_text = xml_text.split("?>", 1)[1].strip()

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

        runtime_counters = relop.findall(
            ".//p:RunTimeInformation/p:RunTimeCountersPerThread",
            ns
        )

        actual_rows = 0.0
        actual_executions = 0.0

        for counter in runtime_counters:
            actual_rows += float(counter.get("ActualRows") or 0)
            actual_executions += float(counter.get("ActualExecutions") or 0)

        has_actual_runtime_stats = len(runtime_counters) > 0

        findings.append({
            "query_id": query_id,
            "operator": physical_op,
            "logical_op": logical_op,
            "estimated_rows": float(relop.get("EstimateRows") or 0),
            "subtree_cost": float(relop.get("EstimatedTotalSubtreeCost") or 0),

            "actual_rows": actual_rows,
            "actual_executions": actual_executions,
            "has_actual_runtime_stats": has_actual_runtime_stats
        })

    return findings

def classify_runtime_issues(plan_rows):
    """
    Converts raw plan operators into normalized runtime evidence categories.
    """

    runtime_issues = []

    for row in plan_rows:
        op = (row.get("operator") or "").upper()        
        logical = (row.get("logical_op") or "").upper()

        # -------------------------
        # SCAN detection
        # -------------------------
        if "TABLE SCAN" in op or "INDEX SCAN" in op:
            runtime_issues.append({"issue_type": "FULL_SCAN"})

        # -------------------------
        # JOIN and HASH AGGREGATE detection
        # -------------------------
        elif "HASH MATCH" in op:
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
        elif "SEGMENT" in op or "SEQUENCE PROJECT" in op:
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

        # -------------------------
        # MISSING INDEX detection
        # -------------------------
        if "MISSING INDEX" in op:
            runtime_issues.append({"issue_type": "MISSING_INDEX"})
            
    return runtime_issues

def analyze_plan_file(plan_path):
    """
    Parses a plan file and returns normalized runtime issue evidence.

    This is a convenience wrapper used by pipeline-level evaluation code.
    """

    raw_rows = parse_plan(plan_path)
    return classify_runtime_issues(raw_rows)
    
def save_plan_results(plan_files, output_path=None):
    """
    Parses multiple .sqlplan files and saves combined operator-level results.
    """

    all_results = []

    for plan_file in plan_files:
        all_results.extend(parse_plan(plan_file))

    if output_path is None:
        output_path = ARTIFACTS / "analysis" / "plan_results.json"

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=4)

    return all_results


if __name__ == "__main__":
    plans_dir = PROJECT_ROOT / "plans"
    plan_files = sorted(plans_dir.glob("*.sqlplan"))

    results = save_plan_results(plan_files)

    print(f"Parsed {len(plan_files)} plan files")
    print(f"Extracted {len(results)} runtime operators")