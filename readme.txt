# QueryLens Python Module Guide

This document describes the purpose of each Python module in the QueryLens repository.

QueryLens is a static SQL analysis system that detects query performance anti-patterns and
correlates them with SQL Server execution plan behavior. The repository is organized into
components for SQL parsing, static rule analysis, execution plan inspection, signal correlation,
and experimental evaluation.

---

# Reproducing the Experiment

To regenerate the analysis artifacts used in the evaluation:

python -m src.analysis.debug_rule_coverage
python -m src.analysis.runtime_validator_expanded
python -m src.analysis.generate_rule_level_metrics
python -m src.analysis.runtime_behavior_summary_generator

The debug_rule_coverage script can be used during development to verify that
static rules are triggering across the evaluation workload.

These commands will regenerate the primary evaluation artifacts located in:

artifacts/eval/

---

# Top-level package files

* `src/run_full_analysis.py` — main pipeline entrypoint that runs static analysis, runtime validation, and evaluation artifact generation.

---

# `src/analysis/` (analysis pipeline)

* `src/analysis/sql_parser.py` — helper functions to parse SQL text/files into a parse tree.
* `src/analysis/ast_visitor.py` — AST visitor class used to extract structural query features from SQL.
* `src/analysis/feature_extractor.py — extracts structural SQL features from the AST and query text, including SELECT *, predicate usage, joins, aggregation, subqueries, window functions, and Cartesian joins.
* `src/analysis/static_rules.py — rule engine that maps extracted query features to performance anti-pattern warnings (e.g., SELECT *, non-sargable predicates, complex joins, sorting operations, and Cartesian joins).
* `src/analysis/static_analyzer.py` — orchestrates parser + feature extraction + static rule evaluation.
* `src/analysis/ast_rules.py` — AST-specific rule checks and AST-based analysis entrypoints.

### Legacy / baseline components

* `src/analysis/legacy_regex_rules.py` — earlier regex-based static analyzer retained for baseline comparison.
* `src/analysis/compare_engines.py` — compares regex and AST analyzers on the same SQL inputs.
* `src/analysis/comparison_summary.py` — summarizes analyzer comparison output into report-friendly metrics.

### Execution plan analysis

* `src/analysis/prototype_plan_analyzer.py` — prototype SQL Server execution plan analyzer used to classify runtime behaviors.
* `src/analysis/runtime_validator.py` — validates static warnings against execution plan behavior for the baseline workload.
* `src/analysis/runtime_validator_expanded.py` — runtime validation implementation used for the expanded evaluation dataset.

### Runtime behavior characterization

* `src/analysis/runtime_behavior_summary.py` — library functions that aggregate execution plan operator behavior.
* `src/analysis/runtime_behavior_summary_generator.py` — script entrypoint that generates runtime behavior summary artifacts.
* `src/analysis/runtime_operator_distribution.py` — computes operator distribution statistics across execution plans.

### Evaluation and metrics generation

* `src/analysis/false_positive_analyzer.py` — analyzes potential false positives from static rule detection.
* `src/analysis/generate_evaluation_table.py` — builds tabular static-evaluation output.
* `src/analysis/evaluate_static_accuracy.py` — evaluates static analyzer results against ground truth.
* `src/analysis/generate_research_tables.py` — creates research summary tables from analysis artifacts.
* `src/analysis/generate_expanded_research_table.py` — generates expanded research table reports.
* `src/analysis/generate_correlation_matrix.py` — computes and exports rule/runtime correlation matrices.
* `src/analysis/generate_rule_level_metrics.py` — produces per-rule precision metrics from runtime validation results.
* `src/analysis/precision_recall_metrics.py` — computes precision/recall style performance metrics.
* `src/analysis/html_report_generator.py` — compiles analysis artifacts into an HTML report.

### Development utilities

* `src/analysis/inspect_plan_ops.py` — utility script for inspecting operator names and XML namespaces in execution plan files.
* `src/analysis/threshold_config.py` — central location for correlation and runtime confirmation thresholds.
* `src/analysis/debug_rule_coverage.py — developer utility that reports which static rules trigger for each query in the evaluation dataset.

---

# `src/correlation/` (cross-signal matching)

* `src/correlation/correlator.py` — normalizes static and runtime signals and performs cross-signal correlation.

---

# `src/metrics/` (metric generation)

* `src/metrics/evaluation_metrics.py` — generates consolidated evaluation metrics from analysis outputs.

---

# `parser/` (standalone parser package)

* `parser/sql_parser.py` — parser entrypoint for converting SQL text into parse trees.
* `parser/feature_extractor.py` — feature extraction class built on parser output.


---

## `parser/grammar/` (ANTLR-generated grammar files)

These files are automatically generated from the T-SQL grammar and should not be modified manually.

* `parser/grammar/TSqlLexer.py` — generated lexer for the T-SQL grammar.
* `parser/grammar/TSqlParser.py` — generated parser for the T-SQL grammar.
* `parser/grammar/TSqlParserListener.py` — generated listener base class for parse-tree walking.
* `parser/grammar/TSqlParserVisitor.py` — generated visitor base class for parse-tree traversal.

---

# `tests/` (test suite)

* `tests/test_parser.py` — unit tests for SQL parsing behavior.
* `tests/test_ast_rules.py` — tests for AST-based static rule detection.
* `tests/test_regex_rules.py` — tests for legacy regex static rule detection.
* `tests/test_correlation.py` — tests for static/runtime correlation behavior.
* `tests/test_pipeline_integration.py` — integration tests for the end-to-end analysis pipeline.
* `tests/test_feature_extraction_accuracy.py` — validates feature extraction accuracy against expected outputs.

---

# Generated Evaluation Artifacts

The analysis pipeline generates several artifacts used in the experimental evaluation:

* `artifacts/eval/expanded_runtime_report.json` — runtime validation results across the expanded query workload.
* `artifacts/eval/runtime_behavior_summary.json` — aggregated execution plan operator statistics.
* `artifacts/eval/rule_level_metrics.json` — per-rule detection precision metrics derived from runtime validation.

These artifacts are used to produce the tables and figures reported in the experimental results section.

## Repository Structure

The QueryLens repository is organized around the static analysis pipeline, runtime execution-plan inspection, and evaluation artifact generation.

```
QueryLens
│
├── src/
│   ├── analysis/        # static analysis, runtime validation, evaluation scripts
│   ├── correlation/     # static runtime signal correlation logic
│   ├── metrics/         # evaluation metric generation
│   └── run_full_analysis.py
│
├── parser/              # ANTLR-based SQL parser and feature extraction
│   └── grammar/         # generated T-SQL grammar files
│
├── plans_expanded/      # SQL Server execution plans used in evaluation
├── datasets/            # SQL workload queries
├── artifacts/
│   └── eval/            # generated evaluation outputs and metrics
│
└── tests/               # unit and integration test suite
```

The typical analysis workflow is:


SQL Queries
     ↓
SQL Parser (ANTLR)
     ↓
Feature Extraction
     ↓
Static Rule Engine
     ↓
Execution Plan Analysis
     ↓
Runtime Validation
     ↓
Evaluation Metrics + Research Artifacts