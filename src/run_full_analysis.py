"""
QueryLens — Full Batch Analysis Pipeline

Runs the complete end-to-end analysis workflow over all SQL queries
and execution plans in the plans/ directory.

Pipeline stages:
    1. Optional live execution-plan capture using pyodbc
    2. Static analysis
    3. Execution plan parsing
    4. Correlation
    5. Rewrite suggestion generation
    6. Metrics and report generation
    7. Proposal-supporting artifact generation
    
Inputs:
    plans/*.sql
    plans/*.sqlplan

Outputs:
    artifacts/analysis/static_results.json
    artifacts/analysis/plan_results.json
    artifacts/analysis/correlation_output.json
    artifacts/analysis/validated_results.json
    artifacts/analysis/static_only_results.json
    artifacts/evaluation/evaluation_metrics.json
    artifacts/evaluation/expanded_runtime_report.json
    artifacts/evaluation/rule_level_metrics.json
    artifacts/reports/runtime_validation_report.html
    artifacts/detection_results.json
    artifacts/static_test_log.txt
    artifacts/correlation_matrix.csv
    artifacts/validation_log.txt
    artifacts/comparison_summary.csv
    artifacts/combined_vs_baseline.png
    artifacts/performance_log.csv
"""

import csv
import json
import os
import time
from pathlib import Path

from src.analysis.static_analyzer import analyze_sql
from src.analysis.plan_analyzer import parse_plan
from src.analysis.rewrite_engine import suggest_rewrites
from src.analysis.rule_enricher import enrich_rules
from src.correlation.correlator import correlate
from src.parser.feature_extractor import FeatureExtractor
from src.parser.sql_parser import parse_sql
from src.reporting.generate_comparison_artifacts import main as generate_comparison_artifacts

from src.evaluation.runtime_validator_expanded import run_evaluation
from src.evaluation.generate_rule_level_metrics import generate_rule_level_metrics
from src.evaluation.evaluate_static_accuracy import run_static_accuracy_evaluation

from src.metrics.global_metrics import generate_global_metrics

from src.reporting.html_report_generator import generate_report
from src.reporting.generate_correlation_matrix import generate_matrix

from src.tools.generate_static_test_log import generate_static_test_log
from src.tools.false_positive_analyzer import run_analysis as run_false_positive_analysis

from src.db.live_plan_capture import capture_all_plans
from src.db.index_metadata_loader import load_index_metadata

PROJECT_ROOT = Path(__file__).resolve().parents[1] 

PLANS_FOLDER = PROJECT_ROOT / "plans"
LIVE_PLANS_FOLDER = PROJECT_ROOT / "plans_live"
ARTIFACTS = PROJECT_ROOT / "artifacts"

# Set to True to generate fresh actual execution plans using pyodbc.
# Set to False to use saved .sqlplan files from plans/.
USE_LIVE_CAPTURE = True

def save_json(data, path):
    """Writes JSON output to disk, creating parent directories if needed."""    
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

def measure_baseline_runtime(plans_folder):
    """
    Measures a lightweight baseline by only reading SQL files from disk.
    This provides a simple comparison point for the full QueryLens pipeline.
    """
    start = time.time()
    query_count = 0

    for file in os.listdir(plans_folder):
        if not file.endswith(".sql"):
            continue

        query_count += 1
        sql_file = plans_folder / file

        try:
            with open(sql_file, "r", encoding="utf-8") as f:
                _ = f.read()
        except UnicodeDecodeError:
            with open(sql_file, "r", encoding="cp1252") as f:
                _ = f.read()

    end = time.time()
    return query_count, (end - start)
    
def write_performance_log(total_queries, baseline_seconds, querylens_seconds):
    """
    Writes a baseline-vs-QueryLens performance comparison log.

    The baseline is a lightweight file-read pass over the workload.
    QueryLens time is the full pipeline runtime.
    """
    output_path = ARTIFACTS / "performance_log.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    overhead_percent = (
        round(((querylens_seconds - baseline_seconds) / baseline_seconds) * 100, 3)
        if baseline_seconds > 0 else 0
    )

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "run_id",
            "queries_processed",
            "baseline_seconds",
            "querylens_seconds",
            "avg_baseline_seconds_per_query",
            "avg_querylens_seconds_per_query",
            "overhead_percent"
        ])
        writer.writerow([
            1,
            total_queries,
            round(baseline_seconds, 4),
            round(querylens_seconds, 4),
            round(baseline_seconds / total_queries, 4) if total_queries else 0,
            round(querylens_seconds / total_queries, 4) if total_queries else 0,
            overhead_percent
        ])

    print(f"Performance log generated → {output_path}")
    

def get_plan_file(base, plans_folder):
    """
    Returns the execution plan path for the current query.

    Live mode:
        plans_live/<query>.sqlplan

    Offline mode:
        plans/<query>.sqlplan
    """
    if USE_LIVE_CAPTURE:
        return LIVE_PLANS_FOLDER / f"{base}.sqlplan"

    return plans_folder / f"{base}.sqlplan"
    
def main_batch(plans_folder):
    """
    Executes the full QueryLens batch pipeline over every SQL file in the plans folder.

    For each query:
        - runs static analysis
        - extracts SQL features
        - enriches rules with recommendations
        - parses the matching execution plan, if present
        - correlates static findings with runtime evidence
        - generates rewrite suggestions

    After processing all queries, writes analysis artifacts and produces
    evaluation metrics plus the final HTML report.
    """    
    print("\n=== Running QueryLens Batch Analysis ===")
    
    if USE_LIVE_CAPTURE:
        print("\n=== Live capture enabled ===")
        print("Generating fresh actual execution plans using pyodbc...")
        capture_all_plans()
        print("Live execution-plan capture complete\n")
    else:
        print("\n=== Offline mode enabled ===")
        print("Using saved .sqlplan files from plans/\n")

    print("\n=== Loading SQL Server index metadata ===")
    
    try:
        index_metadata = load_index_metadata(save_to_file=True)
        print("Index metadata loaded")
    except Exception as ex:
        index_metadata = {}
        print(f"Index metadata unavailable; continuing without index metadata: {ex}")
        
    baseline_query_count, baseline_seconds = measure_baseline_runtime(plans_folder)
    pipeline_start = time.time()
    
    all_static = []
    all_runtime = []
    all_correlated = []
    query_count = 0

    for file in os.listdir(plans_folder):
        if file.endswith(".sql"):
            query_count += 1
            base = file.replace(".sql", "")
            sql_file = plans_folder / f"{base}.sql"
            plan_file = get_plan_file(base, plans_folder)

            print(f"→ Processing: {base}")

            # -------------------------
            # 1. STATIC ANALYSIS
            # -------------------------
            static_results = analyze_sql(str(sql_file), index_metadata=index_metadata)

            # Read SQL text directly so feature extraction and rewrite generation
            # operate on the original query text.
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
            # Attach human-readable recommendation details to each static finding.            
            enriched_rules = enrich_rules(static_results)

            # -------------------------
            # 4. RUNTIME ANALYSIS
            # -------------------------
            # Parse the matching execution plan when available; otherwise treat
            # runtime evidence as absent for this query.            
            if plan_file.exists():
                runtime_results = parse_plan(str(plan_file))
            else:
                runtime_results = []
                print(f"No plan file for {base}")

            # -------------------------
            # 5. CORRELATION
            # -------------------------
            # Link static findings to runtime plan evidence and compute
            # confirmation / confidence scores.            
            correlation_results = correlate(enriched_rules, runtime_results)

            # -------------------------
            # 6. REWRITE SUGGESTIONS
            # -------------------------
            rewrites = suggest_rewrites(
                sql_text,
                correlation_results,
                features
            )

            # Attach rewrite suggestions to each correlated finding so downstream
            # reporting can display them without re-running rewrite generation.
            for r in correlation_results:
                r["rewrites"] = rewrites

            # -------------------------
            # COLLECT RESULTS
            # -------------------------
            all_static.extend(enriched_rules)
            all_runtime.extend(runtime_results)
            all_correlated.extend(correlation_results)
                
    # Split correlation output into runtime-validatable findings and static-only findings.
    validated_results = [r for r in all_correlated if r["validated"]]
    non_validated_results = [r for r in all_correlated if not r["validated"]]

    # Persist core analysis artifacts.    
    save_json(all_correlated, ARTIFACTS / "analysis/correlation_output.json")
    save_json(validated_results, ARTIFACTS / "analysis/validated_results.json")
    save_json(non_validated_results, ARTIFACTS / "analysis/static_only_results.json")
    save_json(all_runtime, ARTIFACTS / "analysis/plan_results.json")
    save_json(all_static, ARTIFACTS / "analysis/static_results.json")

    validated_total = len(validated_results)

    # Compute lightweight summary statistics for console reporting
    confirmed_count = sum(
        1 for r in validated_results if r.get("confirmed")
    )

    suppressed_count = sum(
        1 for r in validated_results if r.get("suppressed")
    )

    high_confidence_count = sum(
        1 for r in validated_results if r.get("confidence") == "high"
    )

    confirmation_rate = round(confirmed_count / validated_total, 3) if validated_total else 0
    suppression_rate = round(suppressed_count / validated_total, 3) if validated_total else 0
    
    # Generate evaluation artifacts and the final HTML report from the saved outputs.    
    generate_global_metrics(
        ARTIFACTS / "analysis/correlation_output.json",
        ARTIFACTS / "evaluation/evaluation_metrics.json"
    )
    
    run_evaluation(index_metadata=index_metadata)
    generate_rule_level_metrics()
    generate_report()

    # -------------------------
    # PROPOSAL-SUPPORTING ARTIFACTS
    # -------------------------
    generate_static_test_log()
    generate_matrix(index_metadata=index_metadata)
    run_false_positive_analysis(index_metadata=index_metadata)
    
    # Static accuracy evaluation requires datasets/ground_truth_static.json.
    # Leave enabled only if that file has been restored.
    try:
        run_static_accuracy_evaluation()
    except FileNotFoundError:
        print("Static accuracy evaluation skipped: ground_truth_static.json not found")

    generate_comparison_artifacts()
    
    pipeline_end = time.time()
    elapsed_seconds = pipeline_end - pipeline_start
    
    write_performance_log(query_count, baseline_seconds, elapsed_seconds)
    
    print("Batch analysis complete")
    print("Global evaluation metrics generated")
    print("Expanded runtime evaluation generated")
    print("Rule-level metrics generated")
    print("HTML report generated")
    print("Static test log generated")
    print("Correlation matrix generated")
    print("False positive validation log generated")
    print("Baseline vs combined comparison artifacts generated")
    
    print("\n Summary:")
    print(f"Total queries processed: {query_count}")
    print(f"Total static findings: {len(all_static)}")
    print(f"Total runtime operators: {len(all_runtime)}")
    print(f"Total correlated findings: {len(all_correlated)}")
    print(f"Validated findings: {len(validated_results)}")
    print(f"Static-only findings: {len(non_validated_results)}")
    print(f"Runtime-supported findings: {confirmed_count}")
    print(f"Runtime agreement rate: {confirmation_rate}")
    print(f"Suppressed findings: {suppressed_count}")
    print(f"Suppression rate: {suppression_rate}")
    print(f"High-confidence confirmations: {high_confidence_count}")
    print(f"Total pipeline runtime (seconds): {round(elapsed_seconds, 4)}")    

if __name__ == "__main__":
    main_batch(PLANS_FOLDER)