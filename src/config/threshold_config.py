"""
QueryLens — Runtime Threshold Configuration

Defines configurable thresholds used by the correlation engine to
interpret execution plan behavior.

Purpose:
    - centralize all runtime tuning parameters
    - enable controlled experimentation without modifying core logic
    - ensure consistent scoring behavior across the system

Notes:
    - thresholds influence confidence scoring and rule confirmation
    - tuning these values will directly affect evaluation metrics
"""


# -------------------------------------------------
# Row volume thresholds
# -------------------------------------------------

# Estimated row count above which operations are considered high-impact
# Used to amplify confidence for scans, joins, and lookups
HIGH_ROW_THRESHOLD = 10000

# -------------------------------------------------
# Operator thresholds
# -------------------------------------------------

# Minimum number of scan operators required before treating scan behavior
# as strong evidence of inefficiency
MIN_SCAN_COUNT = 2

# -------------------------------------------------
# Optional correlation relaxations
# -------------------------------------------------

# If enabled, allows hash join presence to contribute to confirmation scoring
# Disabled by default to avoid over-attributing join complexity
ALLOW_HASH_JOIN_CONFIRMATION = False

# If enabled, allows sort operators to contribute to confirmation scoring
# Disabled by default to maintain stricter validation criteria
ALLOW_SORT_CONFIRMATION = False