"""
QueryLens — Full Batch Analysis Pipeline

Pipeline stages:
1. Static analysis (AST-based rule detection)
2. Execution plan parsing (runtime evidence extraction)
3. Correlation (link static warnings → runtime operators)
4. Metrics generation (confirmation rate)

Input:
    plans/*.sql + plans/*.sqlplan

Outputs:
    artifacts/analysis/static_results.json
    artifacts/analysis/plan_results.json
    artifacts/analysis/correlation_output.json
    artifacts/evaluation/evaluation_metrics.json
"""

import json
import os
import sys
from pathlib import Path

from src.analysis.static_analyzer import analyze_sql
from src.analysis.prototype_plan_analyzer import parse_plan
from src.analysis.rewrite_engine import suggest_rewrites
from src.analysis.rule_enricher import enrich_rules
from src.correlation.correlator import correlate
from src.metrics.global_metrics import generate_metrics
from src.parser.feature_extractor import FeatureExtractor
from src.parser.sql_parser import parse_sql

PROJECT_ROOT = Path(__file__).resolve().parents[1]  # from src/scripts → project root
DATASET_FOLDER = PROJECT_ROOT / "datasets"
PLANS_FOLDER = PROJECT_ROOT / "plans"
ARTIFACTS = PROJECT_ROOT / "artifacts"

def save_json(data, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

def main_batch(plans_folder):
    print("\n=== Running QueryLens Batch Analysis ===")

    all_static = []
    all_runtime = []
    all_correlated = []
    query_count = 0

    for file in os.listdir(plans_folder):
        if file.endswith(".sql"):
            query_count += 1
            base = file.replace(".sql", "")
            sql_file = plans_folder / f"{base}.sql"
            plan_file = plans_folder / f"{base}.sqlplan"

            print(f"→ Processing: {base}")

            # -------------------------
            # 1. STATIC ANALYSIS
            # -------------------------
            static_results = analyze_sql(str(sql_file))

            # Read SQL text for rewrite engine
            try:
                with open(sql_file, "r", encoding="utf-8") as f:
                    sql_text = f.read()
            except UnicodeDecodeError:
                with open(sql_file, "r", encoding="cp1252") as f:
                    sql_text = f.read()

            # -------------------------
            # 2. FEATURE EXTRACTION
            # -------------------------
            tree, _ = parse_sql(sql_text)
            extractor = FeatureExtractor(sql_text)
            features = extractor.extract(tree)
            
            # -------------------------
            # 3. ENRICH RULES
            # -------------------------
            enriched_rules = enrich_rules(static_results)

            # -------------------------
            # 4. RUNTIME ANALYSIS
            # -------------------------
            if plan_file.exists():
                runtime_results = parse_plan(str(plan_file))
            else:
                runtime_results = []
                print(f"No plan file for {base}")

            # -------------------------
            # 5. CORRELATION
            # -------------------------
            correlation_results = correlate(enriched_rules, runtime_results)

            # -------------------------
            # 6. REWRITE SUGGESTIONS
            # -------------------------
            rewrites = suggest_rewrites(
                sql_text,
                correlation_results,
                features
            )

            # Attach rewrites to correlation output
            for r in correlation_results:
                r["rewrites"] = rewrites

            # -------------------------
            # COLLECT RESULTS
            # -------------------------
            all_static.extend(enriched_rules)
            all_runtime.extend(runtime_results)
            all_correlated.extend(correlation_results)

    save_json(all_correlated, ARTIFACTS / "analysis/correlation_output.json")
    save_json(all_runtime, ARTIFACTS / "analysis/plan_results.json")
    save_json(all_static, ARTIFACTS / "analysis/static_results.json")

    generate_metrics(
        ARTIFACTS / "analysis/correlation_output.json",
        ARTIFACTS / "evaluation/evaluation_metrics.json"
    )

    print("✔ Batch analysis complete")
    print("✔ Evaluation metrics generated")
    print("\n📊 Summary:")
    print(f"Total queries processed: {query_count}")
    print(f"Total static findings: {len(all_static)}")
    print(f"Total runtime operators: {len(all_runtime)}")
    print(f"Total correlated findings: {len(all_correlated)}")

if __name__ == "__main__":
    main_batch(PLANS_FOLDER)