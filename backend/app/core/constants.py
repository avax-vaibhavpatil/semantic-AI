"""
Business Constants

Constants that define business rules and limits.
These are domain-specific, not technical constants.
"""

# Query Limits
MAX_QUERY_ROWS = 10000
DEFAULT_MAX_ROWS = 500
MIN_QUERY_ROWS = 1

# Report Limits
MAX_REPORT_NAME_LENGTH = 255
MAX_REPORT_DESCRIPTION_LENGTH = 1000
MAX_TAGS_PER_REPORT = 10
MAX_TAG_LENGTH = 50

# SQL Limits
MAX_SQL_LENGTH = 50000  # Maximum SQL query length
MIN_SQL_LENGTH = 10     # Minimum SQL query length

# Execution Limits
MAX_EXECUTION_TIME_MS = 300000  # 5 minutes max execution time
DEFAULT_TIMEOUT_MS = 30000     # 30 seconds default timeout

# Report Status Values
REPORT_STATUS_ACTIVE = "active"
REPORT_STATUS_ARCHIVED = "archived"
REPORT_STATUS_DELETED = "deleted"

# Column Types
COLUMN_TYPE_DIMENSION = "dimension"
COLUMN_TYPE_MEASURE = "measure"
COLUMN_TYPE_DATE = "date"

# Semantic Layer
SEMANTIC_JSON_ENCODING = "utf-8"

