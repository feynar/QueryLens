"""
QueryLens — AST Static SQL Analyzer (Week 8)
Grammar-aware SQL detection using ANTLR parse tree.
Produces same output format as legacy regex analyzer.
"""

import os
from src.parser.sql_parser import parse_sql_file, parse_sql
from src.parser.feature_extractor import FeatureExtractor
from src.analysis.static_rules import evaluate_rules
from src.analysis.recommendation_engine import generate_recommendation

def analyze_sql(file_path):

    # Parse AST
    tree, parser = parse_sql_file(file_path)

    # Read SQL text directly
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            sql_text = f.read()
    except UnicodeDecodeError:
        with open(file_path, "r", encoding="cp1252") as f:
            sql_text = f.read()

    # Extract features
    extractor = FeatureExtractor(sql_text)
    features = extractor.extract(tree)

    query_id = os.path.splitext(os.path.basename(file_path))[0]
    
    rules = evaluate_rules(features)

    results = []
    for r in rules:
        results.append({
            "query_id": query_id,
            "rule": r["rule"],  # ✅ standardized
            "confidence": r["confidence"],
            "runtime_verifiable": r["runtime_verifiable"],
            "recommendation": generate_recommendation(
                r["rule"],
                r["confidence"]
            )
        })

    return results

# Helper used by unit tests
def analyze_with_ast_text(sql_text):

    tree, parser = parse_sql(sql_text)

    extractor = FeatureExtractor(sql_text)
    features = extractor.extract(tree)

    rules = evaluate_rules(features)

    results = []
    for r in rules:
        results.append({
            "query_id": "test_query",
            "rule": r["rule"],
            "confidence": r["confidence"],
            "runtime_verifiable": r["runtime_verifiable"],
            "recommendation": generate_recommendation(
                r["rule"],
                r["confidence"]
            )
        })

    return results