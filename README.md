# QueryLens Python Module Guide

QueryLens is a static SQL analysis system that detects query performance anti-patterns and correlates them with SQL Server execution plan behavior. The repository is organized into components for SQL parsing, static rule analysis, execution plan inspection, signal correlation, runtime validation, reporting, and experimental evaluation.

---

# Reproducing the Main Experiment

To regenerate the primary analysis and evaluation artifacts used in the project, run:

python -m src.run_full_analysis

This command runs the complete end-to-end pipeline, including:

static SQL analysis
SQL parsing and feature extraction
execution plan parsing
static/runtime correlation
rewrite suggestion generation
global evaluation metrics
expanded runtime validation report
rule-level metrics
HTML report generation

The main generated outputs are written to:

artifacts/analysis/
artifacts/evaluation/
artifacts/reports/

Optional Development / Debug Utilities

These scripts are useful during development and validation, but are not required for the main experiment.

Rule coverage check
python -m src.tools.debug_rule_coverage

Prints which static rules are detected for each SQL query in the workload.

Execution plan operator inspection
python -m src.tools.inspect_plan_ops plans/<plan_file.sqlplan>

Prints raw operator names from a SQL Server execution plan.

False-positive diagnostic report
python -m src.tools.false_positive_analyzer

Generates a diagnostic log for static warnings that were not confirmed by runtime evidence.

Top-level Files
src/run_full_analysis.py — main pipeline entrypoint that runs static analysis, runtime correlation, evaluation metric generation, and HTML report generation.
README.md — repository/module guide.

Repository Structure
QueryLens
│
├── src/
│   ├── analysis/        # core static analysis, plan parsing, rewrite logic
│   ├── config/          # runtime validation configuration and thresholds
│   ├── correlation/     # static/runtime signal correlation
│   ├── evaluation/      # runtime evaluation artifact generation
│   ├── metrics/         # global validation-aware metrics
│   ├── parser/          # ANTLR SQL parsing and feature extraction
│   ├── reporting/       # HTML and research-report artifact generation
│   ├── tools/           # development and debugging utilities
│   └── run_full_analysis.py
│
├── plans/               # SQL workload files and matching SQL Server plans
├── datasets/            # schema, seed data, and workload source SQL
├── artifacts/           # generated outputs
│   ├── analysis/
│   ├── evaluation/
│   └── reports/
│
├── docs/                # architecture and design documentation
├── logs/                # weekly development logs
└── tests/               # unit and integration tests
src/analysis/ — Core Analysis Pipeline

This package contains the main analysis logic for static detection, execution plan parsing, rule enrichment, and rewrite suggestion generation.

src/analysis/static_analyzer.py — orchestrates SQL parsing, feature extraction, static rule evaluation, and recommendation generation.
src/analysis/static_rules.py — maps extracted SQL features to static anti-pattern warnings.
src/analysis/plan_analyzer.py — parses SQL Server execution plans and extracts runtime operator evidence.
src/analysis/recommendation_engine.py — maps detected rules to human-readable issue/impact/recommendation metadata.
src/analysis/rewrite_engine.py — generates example SQL rewrite suggestions for selected anti-patterns.
src/analysis/rule_enricher.py — enriches detected rules with recommendation metadata.
Archived Analysis Components

These are older or legacy files retained for reference:

src/analysis/archive/ast_rules.py
src/analysis/archive/ast_visitor.py
src/analysis/archive/compare_engines.py
src/analysis/archive/comparison_summary.py
src/analysis/archive/legacy_regex_rules.py
src/analysis/archive/runtime_confidence.py
src/parser/ — SQL Parsing and Feature Extraction

This package handles SQL parsing through ANTLR and extracts structural query features used by the static rule engine.

src/parser/sql_parser.py — helper functions for parsing SQL text and files into ANTLR parse trees.
src/parser/feature_extractor.py — extracts structural SQL features from the parse tree and raw SQL text, including:
SELECT *
non-sargable predicates
joins
aggregation
EXISTS / NOT EXISTS
derived tables
HAVING clauses
window functions
correlated subqueries
src/parser/grammar/ — ANTLR Grammar Files

These files are generated from the T-SQL grammar and support parsing.

Generated grammar source files:

src/parser/grammar/TSqlLexer.py
src/parser/grammar/TSqlParser.py
src/parser/grammar/TSqlParserListener.py
src/parser/grammar/TSqlParserVisitor.py

Other supporting files:

src/parser/grammar/TSqlLexer.tokens
src/parser/grammar/TSqlParser.tokens
src/parser/grammar/TSqlLexer.interp
src/parser/grammar/TSqlParser.interp
src/correlation/ — Static/Runtime Correlation

This package links static warnings to runtime execution plan evidence.

src/correlation/correlator.py — normalizes static and runtime findings, extracts runtime plan signals, and computes confirmation/confidence results.
src/config/ — Configuration

This package contains configuration shared across runtime validation logic.

src/config/runtime_rules.py — defines which static rules are eligible for runtime validation.
src/config/threshold_config.py — centralizes thresholds used by the correlation engine.
src/evaluation/ — Evaluation Pipeline

This package contains scripts that generate evaluation outputs from the runtime validation workflow.

src/evaluation/runtime_validator_expanded.py — builds the expanded runtime validation report over the current 30-query workload.
src/evaluation/generate_rule_level_metrics.py — produces rule-level metrics from the expanded runtime validation report.
Archived Evaluation Components

These are older or non-primary evaluation scripts retained for reference:

src/evaluation/archive/evaluate_static_accuracy.py
src/evaluation/archive/precision_recall_metrics.py
src/evaluation/archive/runtime_validator.py
src/metrics/ — Global Metrics

This package contains summary metric generation logic.

src/metrics/global_metrics.py — computes validation-aware global metrics from correlation output.

These metrics describe agreement between static analysis and runtime evidence. They do not claim true ground-truth correctness.

src/reporting/ — Reports and Research Outputs

This package generates HTML and text-based outputs used in reporting and evaluation summaries.

src/reporting/html_report_generator.py — generates the final HTML runtime validation report.
src/reporting/generate_correlation_matrix.py — exports a rule-level correlation matrix.
src/reporting/generate_expanded_research_table.py — writes a concise expanded runtime evaluation summary.
src/reporting/generate_research_tables.py — writes combined research summary outputs.
src/reporting/runtime_behavior_summary.py — computes runtime operator behavior summaries across the workload.
Archived Reporting Components
src/reporting/archive/runtime_behavior_summary_generator.py
src/reporting/archive/runtime_operator_distribution.py
src/tools/ — Development Utilities

These scripts are intended for debugging and validation rather than the main experiment.

src/tools/debug_rule_coverage.py — prints which static rules are detected for each query.
src/tools/inspect_plan_ops.py — inspects raw execution plan XML and prints operator names.
src/tools/false_positive_analyzer.py — produces a report for static warnings not confirmed by runtime evidence.
tests/ — Test Suite

This directory contains the project’s unit and integration tests.

tests/test_parser.py — tests SQL parsing behavior.
tests/test_ast_rules.py — tests AST-based static rule detection.
tests/test_regex_rules.py — tests legacy regex-based detection.
tests/test_correlation.py — tests static/runtime correlation behavior.
tests/test_pipeline_integration.py — integration tests for the end-to-end pipeline.
tests/test_feature_extraction_accuracy.py — validates feature extraction behavior.
Workload and Data Files
datasets/

Contains schema/setup SQL and workload source files:

datasets/1_schema.sql
datasets/2_seed_data.sql
datasets/3_schema_expanded.sql
datasets/4_seed_data_expanded.sql
datasets/workload_30_queries.sql

Archived older dataset files are stored under:

datasets/Archive/
plans/

Contains the 30-query expanded workload as individual SQL files and matching SQL Server execution plans:

plans/Q01_SelectStar_Customers_FullScan.sql
plans/Q01_SelectStar_Customers_FullScan.sqlplan
...
plans/Q30_Correlated_Subquery.sql
plans/Q30_Correlated_Subquery.sqlplan

Archived older workload plans are stored under:

plans/archive/
Generated Artifacts
artifacts/analysis/

Core pipeline outputs:

static_results.json — static rule detections
plan_results.json — parsed execution plan output
correlation_output.json — static/runtime correlation results
validated_results.json — runtime-verifiable findings only
static_only_results.json — static-only findings
artifacts/evaluation/

Evaluation outputs:

evaluation_metrics.json — global validation-aware metrics
expanded_runtime_report.json — expanded runtime validation report
rule_level_metrics.json — per-rule metrics
artifacts/reports/

Presentation-ready report outputs:

runtime_validation_report.html — main HTML runtime validation report
Other artifact files

You may also see older or auxiliary files at the top level of artifacts/, such as:

correlation_matrix.csv
correlation_test_output.txt
validation_log.txt

These are supplementary outputs from debugging or earlier evaluation utilities.

Typical Analysis Workflow
SQL Queries
     ↓
ANTLR SQL Parser
     ↓
Feature Extraction
     ↓
Static Rule Engine
     ↓
Execution Plan Analysis
     ↓
Static/Runtime Correlation
     ↓
Rewrite Suggestions + Recommendations
     ↓
Evaluation Metrics + HTML Report