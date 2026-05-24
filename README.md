QueryLens — SQL Performance Analysis and Runtime Validation System

QueryLens is a Python-based SQL Server query performance analysis system that combines:

Static SQL analysis
Execution plan runtime validation
Static/runtime correlation
Validation-aware confidence scoring
Automated reporting and evaluation artifacts

The system identifies inefficient SQL patterns and validates their real runtime impact using SQL Server execution plans and actual execution statistics.

Unlike traditional static-only SQL analysis tools, QueryLens reduces unsupported recommendations by correlating static findings against runtime execution-plan evidence.

Project Objectives

QueryLens was designed to address several common SQL performance analysis problems:

Excessive false positives from static-only SQL analysis
Lack of runtime validation in lightweight optimization tools
Difficulty interpreting SQL Server execution plans
Limited accessibility of performance tuning tools for non-DBA developers
Lack of reproducible evaluation frameworks for SQL performance diagnostics

The system combines grammar-aware SQL parsing with runtime execution-plan analysis to produce more reliable and actionable recommendations.

Core Features
Static SQL Analysis

QueryLens detects inefficient SQL patterns including:

SELECT *
Non-sargable predicates
Function-based filters
Inefficient joins
ORDER BY without supporting indexes
Correlated subqueries
Window functions
Missing-index candidates
Cartesian joins
Aggregation inefficiencies

Static analysis is performed using an AST-based rule engine built on ANTLR-generated T-SQL grammar parsing.

Runtime Execution Plan Analysis

QueryLens parses SQL Server .sqlplan files and extracts:

Physical operators
Logical operators
Estimated row counts
Actual row counts
Actual execution counts
Missing index recommendations
Join operators
Scan vs seek behavior
Sort operations
Window operators
Key lookups

Runtime analysis supports both:

Offline mode (pre-generated plans)
Live mode using pyodbc and SET STATISTICS XML ON
Validation-Aware Correlation Engine

The correlation engine links static findings to runtime execution evidence.

Examples:

Static Warning	Runtime Evidence
SELECT *	Scan operators
Non-sargable predicate	Table/Index Scan
ORDER BY without index	Sort operator
Correlated subquery	Nested Loops
Missing index candidate	Missing-index recommendation

The system computes:

confirmation status
confidence score
suppression logic
runtime evidence summaries

This validation-aware architecture reduces unsupported recommendations and improves diagnostic precision.

Runtime Validation Features

QueryLens now supports:

Actual runtime row counts
Actual execution counts
Runtime operator summaries
Live SQL Server index metadata integration
Validation-aware suppression logic
Rule-level confirmation metrics

The system validates findings using real SQL Server runtime behavior rather than estimated analysis alone.

Experimental Results

Final experimental workload results:

Metric	Result
Queries Processed	31
Static Findings	57
Runtime-Verifiable Findings	37
Runtime-Confirmed Findings	32
Runtime Agreement Rate	~86.5%
Combined Precision	~65%
False Positive Reduction	Significant improvement over static-only analysis
Pipeline Runtime	~11.5 seconds

These results demonstrate that runtime validation substantially improves recommendation quality compared to static-only SQL analysis.

System Architecture
High-Level Pipeline
SQL Query
   ↓
ANTLR Parser
   ↓
AST Feature Extraction
   ↓
Static Rule Detection
   ↓
Execution Plan Parsing
   ↓
Runtime Feature Extraction
   ↓
Correlation Engine
   ↓
Confidence + Validation
   ↓
Recommendations + Rewrites
   ↓
Reports + Evaluation Artifacts

Repository Structure
QueryLens/
│
├── artifacts/
│   ├── analysis/
│   ├── evaluation/
│   └── reports/
│
├── datasets/
├── docs/
├── logs/
├── plans/
├── plans_live/
├── src/
│   ├── analysis/
│   ├── config/
│   ├── correlation/
│   ├── db/
│   ├── evaluation/
│   ├── metrics/
│   ├── parser/
│   ├── reporting/
│   ├── tools/
│   └── run_full_analysis.py
│
├── tests/
└── README.md

Installation
Requirements
Software
Python 3.11.9 https://www.python.org/downloads/windows/
SQL Server 2019 Developer Edition
ODBC Driver 17 for SQL Server
Windows 10/11 (tested environment)
Python Dependencies

Install dependencies:

pip install -r requirements.txt

Recommended packages:

antlr4-python3-runtime
matplotlib
pyodbc
pytest

SQL Server Setup
Create Database

Run:

datasets/1_schema.sql
datasets/2_seed_data.sql
datasets/3_schema_expanded.sql
datasets/4_seed_data_expanded.sql

This creates:

QueryLensDB
test tables
indexes
workload data

Configure Database Connection

Edit:

src/config/db_config.py

Example:

SERVER = "localhost"
DATABASE = "QueryLensDB"
DRIVER = "ODBC Driver 17 for SQL Server"
TRUSTED_CONNECTION = "yes"

Running QueryLens
Full Pipeline

Run the full experimental workflow:

python -m src.run_full_analysis

This executes:

Live plan capture (optional)
Static SQL analysis
Runtime execution-plan parsing
Static/runtime correlation
Rewrite generation
Evaluation metric generation
HTML report generation
Proposal-supporting artifact generation

Enable live capture in src/config/dbconfig.py:

ENABLE_LIVE_CAPTURE = True

Offline Mode

Offline mode uses existing .sqlplan files stored in:

plans/

inside:

src/run_full_analysis.py

Live mode uses:

pyodbc
SQL Server
SET STATISTICS XML ON

to generate fresh execution plans with:

actual row counts
actual executions
runtime operator metrics


Generated plans are written to:

plans_live/

Main Outputs
Analysis Artifacts
artifacts/analysis/

Contains:

static_results.json
plan_results.json
correlation_output.json
validated_results.json
static_only_results.json
Evaluation Artifacts
artifacts/evaluation/

Contains:

evaluation_metrics.json
expanded_runtime_report.json
rule_level_metrics.json

Reports
artifacts/reports/

Contains:

runtime_validation_report.html
Experimental Comparison Artifacts
artifacts/

Contains:

comparison_summary.csv
combined_vs_baseline.png
correlation_matrix.csv
performance_log.csv
validation_log.txt
static_test_log.txt
Runtime Operator Summaries

QueryLens generates operator summaries including:

Scan count
Seek count
Sort count
Hash joins
Nested loops
Key lookups

These summaries improve runtime visibility and help explain performance behavior during analysis and demonstrations.

Evaluation Framework

The system includes:

Rule-level validation metrics
False-positive analysis
Static-vs-runtime comparison
Precision improvement analysis
Runtime confirmation scoring
Experimental artifact generation

This allows QueryLens to function as both:

a diagnostic tool
an experimental SQL performance analysis framework
HTML Reporting

The HTML reporting system provides:

Global evaluation metrics
Per-query summaries
Expandable detailed findings
Runtime evidence blocks
Operator summaries
Recommendations
Rewrite suggestions
Confidence visualization

Generated report:

artifacts/reports/runtime_validation_report.html
Development Utilities
Rule Coverage Debugging
python -m src.tools.debug_rule_coverage
Execution Plan Operator Inspection
python -m src.tools.inspect_plan_ops plans/<plan_file.sqlplan>
False Positive Analysis
python -m src.tools.false_positive_analyzer
Database Connectivity Test
python -m src.db.db_connection
Index Metadata Loader
python -m src.db.index_metadata_loader
Testing

Run unit and integration tests:

pytest tests/

Tests include:

Parser validation
Rule detection validation
Correlation testing
Pipeline integration testing
Runtime validation checks

Technologies Used
Python 3.11.9
ANTLR 4
SQL Server
pyodbc
XML execution-plan parsing
matplotlib
pytest
Key Innovations

QueryLens introduces several validation-aware features:

Hybrid static/runtime SQL analysis
Runtime-confirmed recommendations
Confidence-based correlation scoring
Suppression of unsupported findings
Runtime-aware missing-index heuristics
Actual execution statistics integration
Operator-level runtime diagnostics

The system demonstrates that correlating static analysis against runtime evidence significantly improves diagnostic reliability.

Academic and Professional Contribution

QueryLens demonstrates a practical approach to reducing false positives in SQL performance analysis systems through runtime validation.

The project combines:

compiler/parser concepts,
database systems,
runtime analysis,
software engineering,
experimental evaluation,

into a reproducible validation-aware performance analysis framework.

The architecture can be extended to support:

additional DBMS platforms,
automated tuning recommendations,
real-time monitoring,
workload-level analysis,
machine-learning-assisted optimization.
Final Status

QueryLens fully implements:

Static SQL analysis
Runtime execution-plan analysis
Live SQL Server integration
Validation-aware correlation
Confidence scoring
Runtime suppression logic
Experimental evaluation framework
HTML reporting
Reproducible research artifacts
