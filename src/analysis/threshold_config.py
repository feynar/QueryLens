# src/analysis/threshold_config.py

"""
Centralized correlation thresholds for runtime confirmation logic.
Week 12 introduces tunable parameters for experimental calibration.
"""

# Estimated rows above which scans are considered performance-impacting
HIGH_ROW_THRESHOLD = 10000

# Minimum number of scan operators required for confirmation
MIN_SCAN_COUNT = 2

# Allow confirmation if any hash join observed
ALLOW_HASH_JOIN_CONFIRMATION = False

# Allow confirmation if explicit sort observed
ALLOW_SORT_CONFIRMATION = False