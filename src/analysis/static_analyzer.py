"""
QueryLens — AST Static SQL Analyzer

Performs grammar-aware static SQL analysis using the ANTLR-generated
T-SQL parse tree.

Responsibilities:
    - parse SQL into an AST
    - extract structural features from the parse tree
    - evaluate static anti-pattern rules
    - attach recommendation metadata to each detected rule

Produces the same output format as the earlier regex-based analyzer.
"""

import os
from src.parser.sql_parser import parse_sql_file, parse_sql
from src.parser.feature_extractor import FeatureExtractor
from src.analysis.static_rules import evaluate_rules
from src.analysis.recommendation_engine import generate_recommendation

def analyze_sql(file_path):
    """
    Runs static analysis on a SQL file and returns structured rule findings.

    Each result includes:
        - query_id
        - rule
        - confidence
        - runtime_verifiable flag
        - recommendation metadata
    """
    
    # Parse the SQL file into an AST.
    tree, parser = parse_sql_file(file_path)

    # Read the raw SQL text directly so feature extraction has access to
    # the original query text in addition to the parse tree.
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            sql_text = f.read()
    except UnicodeDecodeError:
        with open(file_path, "r", encoding="cp1252") as f:
            sql_text = f.read()

    # Extract structural SQL features from the parse tree.
    extractor = FeatureExtractor(sql_text)
    features = extractor.extract(tree)

    query_id = os.path.splitext(os.path.basename(file_path))[0]
    

    # Evaluate static rule detections from the extracted features.    
    rules = evaluate_rules(features)

    results = []
    for r in rules:
        results.append({
            "query_id": query_id,
            "rule": r["rule"],  
            "confidence": r["confidence"],
            "runtime_verifiable": r["runtime_verifiable"],
            "recommendation": generate_recommendation(
                r["rule"],
                r["confidence"]
            )
        })

    return results

def analyze_with_ast_text(sql_text):
    """
    Helper used by tests to run static analysis directly on a SQL string
    instead of a file.
    """    

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