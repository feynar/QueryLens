"""
QueryLens — AST Static SQL Analyzer (Week 8)
Grammar-aware SQL detection using ANTLR parse tree.
Produces same output format as legacy regex analyzer.
"""

import os
from src.analysis.sql_parser import parse_sql_file, parse_sql_text
from src.analysis.feature_extractor import FeatureExtractor
from src.analysis.static_rules import detect_issues_from_features

def analyze_sql(file_path):

    # Parse AST
    tree, _ = parse_sql_file(file_path)

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

    return detect_issues_from_features(features, query_id)

# Helper used by unit tests
def analyze_with_ast_text(sql_text):

    tree, _ = parse_sql_text(sql_text)

    extractor = FeatureExtractor(sql_text)

    features = extractor.extract(tree)

    return detect_issues_from_features(features, "test_query")