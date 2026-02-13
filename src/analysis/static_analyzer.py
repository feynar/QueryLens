"""
QueryLens Static Analyzer — Hybrid Engine
Week 7: Regex + AST Integration
"""

import os

from src.analysis.legacy_regex_rules import analyze_sql_regex
from src.analysis.sql_parser import parse_sql_file
from src.analysis.ast_visitor import QueryLensASTVisitor


def analyze_sql(file_path):
    findings = []

    query_id = os.path.splitext(os.path.basename(file_path))[0]

    # 1️⃣ Legacy regex detection (unchanged behavior)
    findings.extend(analyze_sql_regex(file_path))

    # 2️⃣ AST-based detection (new capability)
    try:
        tree, parser = parse_sql_file(file_path)
        visitor = QueryLensASTVisitor(query_id)
        visitor.visit(tree)
        findings.extend(visitor.findings)
    except Exception:
        # Parser errors should NEVER break pipeline
        pass

    return findings
