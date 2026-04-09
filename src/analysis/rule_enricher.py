from src.analysis.recommendation_engine import generate_recommendation


def enrich_rules(rule_list):

    enriched = []

    for r in rule_list:
        rec = generate_recommendation(r["rule"], r["confidence"])

        enriched.append({
            **r,
            "details": rec
        })

    return enriched