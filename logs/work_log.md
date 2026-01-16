Week 1 — Development Environment Setup

Hours Logged: 6

Activities:
Installed Microsoft SQL Server 2019 Developer Edition and SQL Server Management Studio (SSMS) to provide a local database environment for generating execution plans. Installed Python 3.11 (64-bit), pip, and Git to establish the development toolchain. Configured required Python libraries including pyodbc, antlr4-python3-runtime, and lxml. Initialized the QueryLens Git repository with structured directories for source code, datasets, plans, logs, and artifacts. Verified successful imports of all required dependencies and confirmed SQL Server connectivity readiness.

Outcome:
Fully operational development environment and initialized repository.
Evidence: Initial Git commit – “Week 1: Initialize QueryLens repository structure”.

Week 2 — Execution Plan Analysis Prototype

Hours Logged: 15

Activities:
Developed an initial Python prototype to parse SQL Server execution plan (.sqlplan) XML files. Implemented logic to extract RelOp nodes, physical and logical operators, estimated row counts, and subtree cost values. Created rule-based detection for identifying high-row-count Index Scan and Clustered Index Scan operators as potential performance risks. Generated sample execution plans from SQL Server using sargable and non-sargable query variants and validated prototype output against expected execution plan operator behavior.

Outcome:
Working runtime execution plan analyzer capable of reading .sqlplan files and flagging scan-based inefficiencies.

Evidence:
src/scripts/prototype_plan_analyzer.py
plans/query1_good.sqlplan
plans/query2_nonsargable.sqlplan
Git commit – “Week 2: Add execution plan analyzer prototype and sample sqlplan files”.

Week 3 — Plan Operator Inspection and Dataset Preparation

Hours Logged: 14

Activities:
Implemented a supporting inspection script to enumerate all RelOp operators in execution plans for exploratory analysis of SQL Server plan structures. Used this script to confirm operator variety across single-table and join queries. Prepared initial test query set including baseline sargable filter, non-sargable filter, and join query examples. Verified correct detection of Index Seek, Index Scan, Hash Match, Merge Join, Sort, and Compute Scalar operators in sample plans. Updated repository structure to store prototype scripts and plan samples in version control.

Outcome:
Supporting operator inspection tooling completed and baseline test queries established for later static and correlation testing.
Evidence:

src/scripts/inspect_plan_ops.py

Updated /plans/ directory

Git commit – “Week 3: Add plan operator inspection helper script for operator exploration”.