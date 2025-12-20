# db_connector.py
from sqlalchemy import create_engine, text
import os
from typing import List, Dict, Any

def get_engine():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise EnvironmentError("DATABASE_URL not set")
    return create_engine(db_url, pool_pre_ping=True)

def run_select(sql: str, max_rows: int = 1000) -> List[Dict[str, Any]]:
    eng = get_engine()
    safe_sql = sql.strip()
    if "limit" not in safe_sql.lower():
        safe_sql = safe_sql + f" LIMIT {max_rows}"
    with eng.connect() as conn:
        res = conn.execute(text(safe_sql))
        # SQLAlchemy 2.0 compatible way to convert rows to dictionaries
        rows = [dict(row._mapping) for row in res]
    return rows
