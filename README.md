# QueryLens — SQL Performance Analysis System

QueryLens is a Python-based SQL Server performance analysis tool that combines:

- Static SQL analysis (pattern detection)
- Execution plan analysis (runtime behavior)
- Correlation (validation-aware diagnostics)

The system identifies inefficient SQL patterns and confirms their real performance impact using execution plan evidence, producing actionable optimization recommendations.

---

# Reproducing the Main Experiment

To regenerate all evaluation artifacts used in this project:

```bash
python -m src.run_full_analysis
```

---

## What This Runs

The full end-to-end pipeline:

- Static SQL analysis (AST-based rule detection)
- SQL parsing and feature extraction (ANTLR)
- Execution plan parsing (XML operator extraction)
- Static/runtime correlation
- Rewrite suggestion generation
- Evaluation metric computation
- HTML report generation
- Proposal-supporting artifact generation

---

## Key Outputs

All outputs are written to `artifacts/`:

### Core Analysis
```
artifacts/analysis/
    static_results.json
    plan_results.json
    correlation_output.json
    validated_results.json
    static_only_results.json
```

### Evaluation Metrics
```
artifacts/evaluation/
    evaluation_metrics.json
    expanded_runtime_report.json
    rule_level_metrics.json
```

### Reports
```
artifacts/reports/
    runtime_validation_report.html
```

### Proposal / Evaluation Artifacts
```
artifacts/
    detection_results.json
    static_test_log.txt
    correlation_matrix.csv
    validation_log.txt
    performance_log.csv
    comparison_summary.csv
    combined_vs_baseline.png
```

---

## Experimental Results (Summary)

From the final run:

- Queries processed: **31**
- Static findings: **57**
- Validated findings: **37**
- Static-only findings: **20**
- Runtime agreement rate: **86.5%**
- Precision (combined analysis): **~65%**
- Pipeline runtime: **~11.5 seconds**

These results demonstrate that runtime validation significantly reduces false positives and improves recommendation quality compared to static-only analysis.

---

# Setup and Installation

## Requirements

- Python 3.10+
- Windows (tested) or compatible environment
- SQL Server execution plans (`.sqlplan` files)

## Install Dependencies

```bash
pip install matplotlib antlr4-python3-runtime
```

---

## Repository Structure

```
QueryLens/
│
├── src/
│   ├── analysis/
│   ├── parser/
│   ├── correlation/
│   ├── evaluation/
│   ├── reporting/
│   ├── metrics/
│   ├── tools/
│   └── run_full_analysis.py
│
├── plans/
├── datasets/
├── artifacts/
├── logs/
├── tests/
└── README.md
```

---

## Architecture Overview

```
SQL Query
   ↓
ANTLR Parser
   ↓
Feature Extraction
   ↓
Static Rule Detection
   ↓
Execution Plan Parsing
   ↓
Correlation Engine
   ↓
Validated Findings + Confidence
   ↓
Recommendations + Rewrites
   ↓
Metrics + Reports
```

---

## Key Components

### Static Analysis
Detects inefficiencies such as:
- SELECT *
- Non-sargable predicates
- Inefficient joins
- ORDER BY without index

### Runtime Analysis
Extracts execution plan operators:
- Scans vs seeks
- Join types (hash, merge, nested loop)
- Sort and aggregate operations
- Parallelism indicators

### Correlation Engine
- Links static findings to runtime evidence
- Assigns validation status, confidence, and suppression logic

### Reporting
- HTML diagnostic report
- CSV/JSON evaluation artifacts
- Comparison metrics

---

## Comparison Framework

QueryLens evaluates performance against a baseline (static-only analysis).

Artifacts:
```
artifacts/comparison_summary.csv
artifacts/combined_vs_baseline.png
```

These demonstrate:
- Reduction in false positives
- Improvement in precision
- Increased actionable recommendations

---

## Development Utilities

```bash
python -m src.tools.debug_rule_coverage
python -m src.tools.inspect_plan_ops plans/<file.sqlplan>
python -m src.tools.false_positive_analyzer
```

---

## Tests

```bash
pytest tests/
```

Includes:
- Parser validation
- Rule detection
- Correlation correctness
- Pipeline integration

---

## Notes

- Designed specifically for SQL Server
- Uses ANTLR T-SQL grammar
- Works with pre-generated execution plans
- No external services required

---

## Final Status

QueryLens fully implements:

- Static + runtime SQL analysis
- Validation-aware correlation
- Performance evaluation framework
- Reproducible experimental artifacts
