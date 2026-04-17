"""
QueryLens — Rule Enricher

Enhances detected rule findings with human-readable recommendations.

This module acts as a lightweight enrichment layer that:
    - takes raw rule detections from the static analyzer
    - attaches descriptive metadata (issue, impact, recommendation)
    - produces a unified structure for downstream reporting

Used by:
    - reporting pipeline
    - UI / visualization layers
"""

from src.analysis.recommendation_engine import generate_recommendation

def enrich_rules(rule_list):
    """
    Enriches each rule instance with recommendation details.

    For every detected rule:
        - retrieves a recommendation from the recommendation engine
        - merges it into the rule object under the "details" field

    Parameters:
        rule_list (list): List of rule dictionaries produced by the analyzer

    Returns:
        list: Enriched rule dictionaries with attached recommendation details
    """
    
    enriched = []

    for r in rule_list:
        rec = generate_recommendation(r["rule"], r["confidence"])

        enriched.append({
            **r,
            "details": rec
        })

    return enriched