"""
QueryLens — Execution Plan Operator Inspector

Inspects a SQL Server execution plan file and prints the physical and logical
operators found in each RelOp node.

Purpose:
    - assist debugging of execution plan parsing
    - reveal the operator types present in a plan
    - help validate operator coverage used by runtime analysis
"""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def detect_namespace(root):
    """
    Detects the XML namespace used in the execution plan document
    and returns it in ElementTree lookup format.
    """
    if root.tag.startswith("{"):
        uri = root.tag.split("}")[0].strip("{")
        return {"sp": uri}
    return {"sp": ""}


def main(argv):
    """
    Loads a .sqlplan file, extracts all RelOp nodes, and prints
    their physical and logical operator types.
    """
    if len(argv) < 2:
        print("Usage: python inspect_plan_ops.py plans/<plan_file.sqlplan>")
        sys.exit(1)

    plan_path = Path(argv[1])

    if not plan_path.exists():
        print(f"File not found: {plan_path}")
        sys.exit(1)

    tree = ET.parse(plan_path)
    root = tree.getroot()
    ns = detect_namespace(root)

    # Collect all relational operator nodes from the plan.
    relops = root.findall(".//sp:RelOp", ns)

    print(f"Found {len(relops)} RelOp nodes in plan: {plan_path}")
    seen = set()

    for op in relops:
        physical_op = op.get("PhysicalOp")
        logical_op = op.get("LogicalOp")
        node_id = op.get("NodeId")
        seen.add(physical_op)
        print(f"[Node {node_id}] PhysicalOp={physical_op}, LogicalOp={logical_op}")

    # Print the distinct physical operators present in the plan.
    print("\nDistinct PhysicalOp values:")
    for op_name in sorted(seen):
        print(f"  {op_name}")


if __name__ == "__main__":
    main(sys.argv)
