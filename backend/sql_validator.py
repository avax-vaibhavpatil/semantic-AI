# sql_validator.py
import re
from typing import List, Dict, Any, Tuple, Optional
from db_connector import get_engine
from sqlalchemy import text

# Basic forbidden patterns (case-insensitive)
FORBIDDEN_PATTERNS = [
    r"\binsert\b", r"\bupdate\b", r"\bdelete\b", r"\bdrop\b", r"\balter\b",
    r"\btruncate\b", r";", r"\bmerge\b", r"\bcall\b", r"\bexec\b", r"\bexecute\b"
]

SELECT_ONLY_RE = re.compile(r"^\s*select\b", re.IGNORECASE | re.DOTALL)

def basic_sql_safety(sql: str) -> bool:
    s = sql.strip().lower()
    if not SELECT_ONLY_RE.match(s):
        return False
    for patt in FORBIDDEN_PATTERNS:
        if re.search(patt, s, re.IGNORECASE):
            return False
    return True

def extract_identifiers(sql: str) -> List[str]:
    """
    Very simple heuristic to pull out table/column-like identifiers for whitelist checking.
    Not perfect; used for an extra safety layer.
    """
    # remove string literals
    sql_no_str = re.sub(r"'.*?'", "", sql)
    # Remove everything after AS keyword (aliases)
    sql_no_str = re.sub(r'\s+AS\s+\w+', '', sql_no_str, flags=re.IGNORECASE)
    # find word tokens
    tokens = re.findall(r"[a-zA-Z_][a-zA-Z0-9_\.]*", sql_no_str)
    return list(set(tokens))

def validate_against_semantic(sql: str, semantic: Dict[str, Any]) -> (bool, str):
    """
    Validate SQL uses only allowed tables/columns from semantic JSON.
    Returns (is_valid, message)
    """
    if not basic_sql_safety(sql):
        return False, "SQL failed basic safety checks (non-SELECT or forbidden keywords)."

    # Check for AI error messages in the generated SQL
    if "ERROR:" in sql.upper() or "NOT FOUND" in sql.upper():
        # AI is indicating it cannot fulfill the query
        return False, sql.strip()

    tokens = extract_identifiers(sql)
    allowed = set()
    allowed_tables = set()
    allowed_columns = set()
    
    for tname, tmeta in semantic.get("tables", {}).items():
        allowed.add(tname)
        allowed_tables.add(tname)
        for col in tmeta.get("columns", {}).keys():
            allowed.add(col)
            allowed_columns.add(col)
        for dm in tmeta.get("derived_measures", []) or []:
            if isinstance(dm, dict) and dm.get("name"):
                allowed.add(dm.get("name"))
                allowed_columns.add(dm.get("name"))
            elif isinstance(dm, str):
                allowed.add(dm)
                allowed_columns.add(dm)

    if not any(tok in allowed for tok in tokens):
        return False, "SQL appears to reference no allowed tables or columns."

    suspicious = [tok for tok in tokens if tok.lower() not in {a.lower() for a in allowed} and '.' not in tok]
    
    # Extended SQL keywords and functions
    sql_keywords = {
        'select','from','where','group','by','order','limit','having','as','on','and','or','join',
        'left','right','inner','outer','over','partition','distinct','all','union','intersect',
        'except','case','when','then','else','end','null','nulls','is','not','in','between','like',
        'exists','asc','desc','first','last','offset','fetch','with','recursive','using','natural',
        # SQL functions
        'sum','avg','count','min','max','stddev','variance','coalesce','nullif','cast','extract',
        'upper','lower','substring','trim','concat','length','round','floor','ceil','abs','power',
        'sqrt','exp','log','sin','cos','tan','date','time','timestamp','interval','year','month',
        'day','hour','minute','second','now','current_date','current_time','current_timestamp',
        'row_number','rank','dense_rank','ntile','lag','lead','first_value','last_value',
        # PostgreSQL specific common functions
        'string_agg','array_agg','json_agg','jsonb_agg','to_char','to_date','to_timestamp','age',
        'date_part','date_trunc','generate_series','unnest','array','json','jsonb','rollup','cube',
        'grouping','sets','percentile_cont','percentile_disc','median','mode','corr','regr_slope',
        'regr_intercept','bool_and','bool_or','every','bit_and','bit_or','xmlagg'
    }
    
    suspicious = [s for s in suspicious if s.lower() not in sql_keywords and not re.match(r'^\d+$', s)]
    if suspicious:
        # Create helpful error message with available columns
        available_cols_sample = sorted(list(allowed_columns))[:10]
        return False, (
            f"❌ VALIDATION ERROR: Column(s)/Table(s) '{', '.join(suspicious)}' not found in database schema.\n\n"
            f"📋 Available tables: {', '.join(sorted(allowed_tables))}\n"
            f"📋 Sample columns: {', '.join(available_cols_sample)}{'...' if len(allowed_columns) > 10 else ''}\n\n"
            f"💡 TIP: Check the semantic schema for exact column names. Query rejected to prevent errors."
        )
    return True, "OK"


def extract_date_from_sql(sql: str) -> Optional[str]:
    """
    Extract date value from SQL WHERE clause
    Returns date string if found, None otherwise
    """
    # Pattern to match date comparisons: WHERE date_col = 'YYYY-MM-DD'
    date_patterns = [
        r"=\s*['\"](\d{4}-\d{2}-\d{2})['\"]",
        r"BETWEEN\s*['\"](\d{4}-\d{2}-\d{2})['\"]",
        r">=\s*['\"](\d{4}-\d{2}-\d{2})['\"]",
        r"<=\s*['\"](\d{4}-\d{2}-\d{2})['\"]",
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, sql, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def check_available_dates(table_name: str, date_column: str, semantic: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    """
    Check available date range in database
    Returns (min_date, max_date) or (None, None) if error
    """
    try:
        engine = get_engine()
        # Find date column from semantic
        date_col = None
        for tname, tmeta in semantic.get("tables", {}).items():
            if table_name in tname or tname in table_name:
                time_cols = tmeta.get("time_columns", [])
                if date_column in time_cols:
                    date_col = date_column
                    break
                elif time_cols:
                    date_col = time_cols[0]  # Use first time column
        
        if not date_col:
            return None, None
        
        query = text(f"SELECT MIN({date_col}) as min_date, MAX({date_col}) as max_date FROM {table_name} WHERE {date_col} IS NOT NULL")
        with engine.connect() as conn:
            result = conn.execute(query)
            row = result.fetchone()
            if row and row[0]:
                return str(row[0]), str(row[1])
    except Exception:
        pass
    return None, None


def check_query_results(rows: List[Dict], query_desc: str = "", sql: str = "", semantic: Dict[str, Any] = None) -> Tuple[bool, str]:
    """
    Check if query results are meaningful (not all nulls, not empty when data expected)
    Also checks for date issues
    Returns (is_valid, message)
    """
    if not rows:
        # Check if it's a date issue
        date_issue_msg = ""
        if sql and semantic:
            extracted_date = extract_date_from_sql(sql)
            if extracted_date:
                # Check available dates
                min_date, max_date = check_available_dates("public.gwanalytics", "gws_date", semantic)
                if min_date and max_date:
                    if extracted_date < min_date or extracted_date > max_date:
                        date_issue_msg = (
                            f"\n\n📅 DATE ISSUE DETECTED: The query uses date '{extracted_date}' "
                            f"but your database only has data from '{min_date}' to '{max_date}'. "
                            f"Try using a date within this range (e.g., '{max_date}')."
                        )
        
        if date_issue_msg:
            return False, (
                f"❌ NO DATA FOUND: The query returned 0 rows.{date_issue_msg}"
            )
        else:
            return False, (
                "❌ NO DATA FOUND: The query returned 0 rows. "
                "Possible reasons: (1) Date doesn't exist in database, (2) Too many IS NOT NULL filters, "
                "(3) No matching records. Check your date filter or try removing restrictive WHERE conditions."
            )
    
    # Check if all values are null
    all_null = True
    for row in rows:
        if any(val is not None for val in row.values()):
            all_null = False
            break
    
    if all_null:
        return False, (
            f"⚠️ WARNING: Query returned {len(rows)} row(s) but all values are NULL. "
            "This might indicate: (1) Data doesn't exist, (2) Wrong column names, or (3) Need WHERE clause to filter NULLs."
        )
    
    return True, "OK"
