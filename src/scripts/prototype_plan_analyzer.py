import sys
import os
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional


THRESHOLD_ROWS = 1000  # lower for demo; can be raised later


def _strip_ns(tag: str) -> str:
    """Remove XML namespace from tag."""
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _to_float(val: Optional[str]) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0


def extract_operators(plan_path: str) -> List[Dict[str, Optional[str]]]:
    """Extract RelOp operators from a SQL Server execution plan."""
    tree = ET.parse(plan_path)
    root = tree.getroot()

    operators = []

    for elem in root.iter():
        if _strip_ns(elem.tag) == "RelOp":
            operators.append(
                {
                    "node_id": elem.attrib.get("NodeId"),
                    "physical_op": elem.attrib.get("PhysicalOp"),
                    "logical_op": elem.attrib.get("LogicalOp"),
                    "estimated_rows": elem.attrib.get("EstimateRows"),
                    "estimated_cost": elem.attrib.get("EstimatedTotalSubtreeCost"),
                }
            )

    return operators


def flag_issues(operators: List[Dict[str, Optional[str]]]) -> List[Dict[str, Optional[str]]]:
    """Apply simple prototype performance rules."""
    issues = []

    for op in operators:
        phys = op["physical_op"]
        est_rows = _to_float(op["estimated_rows"])

        if phys == "Table Scan":
            issues.append(
                {
                    "node_id": op["node_id"],
                    "issue": "Table Scan detected",
                    "detail": "Full table scan may indicate a missing index or non-sargable predicate.",
                    "estimated_rows": op["estimated_rows"],
                    "estimated_cost": op["estimated_cost"],
                }
            )

        elif phys in ("Index Scan", "Clustered Index Scan") and est_rows > THRESHOLD_ROWS:
            issues.append(
                {
                    "node_id": op["node_id"],
                    "issue": f"{phys} with high estimated row count",
                    "detail": "Large row scan suggests inefficient filtering or index design.",
                    "estimated_rows": op["estimated_rows"],
                    "estimated_cost": op["estimated_cost"],
                }
            )

    return issues


def main():
    print("\n=== QueryLens Prototype: Execution Plan Analysis ===\n")

    if len(sys.argv) < 2:
        print("ERROR: No execution plan file provided.")
        print("Usage: python prototype_plan_analyzer.py <file.sqlplan>")
        sys.exit(1)

    plan_path = sys.argv[1]

    if not os.path.exists(plan_path):
        print("ERROR: File does not exist:", plan_path)
        sys.exit(1)

    print("Plan file:", plan_path)

    operators = extract_operators(plan_path)

    print("\nOperators found in plan:")
    for op in operators:
        print(
            f"  [Node {op['node_id']}] "
            f"{op['physical_op']} ({op['logical_op']}) "
            f"rows={op['estimated_rows']} "
            f"cost={op['estimated_cost']}"
        )

    issues = flag_issues(operators)

    print("\nDetected issues (prototype rules):")
    if not issues:
        print("  None detected.")
    else:
        for issue in issues:
            print(
                f"  [Node {issue['node_id']}] {issue['issue']}\n"
                f"    {issue['detail']}\n"
                f"    estimated rows={issue['estimated_rows']}, "
                f"cost={issue['estimated_cost']}\n"
            )

    print("Analysis complete.\n")


if __name__ == "__main__":
    main()
