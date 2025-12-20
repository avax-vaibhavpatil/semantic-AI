#!/usr/bin/env python3
"""
inference_engine.py

Takes compact metadata (from manifest_reader output) and infers:
- dimensions
- measures
- time_columns
- derived_measures
- quality_rules

Outputs inferred JSON suitable for semantic_generator.py

Usage:
    python inference_engine.py --metadata backend/metadata/metadata.json --out backend/metadata/inferred.json

Optional:
    --sample-db : run quick sampling to get actual column types (requires DATABASE_URL env var)
"""

import json
import re
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
import os

logger = logging.getLogger("inference_engine")
logging.basicConfig(level=logging.INFO)

# Heuristics / hints (tune as needed)
NUMERIC_HINTS = ['amount', 'price', 'qty', 'quantity', 'count', 'total', 'revenue', 'tax', 'discount', 'balance', 'paid']
DATE_HINTS = ['date', 'day', 'month', 'year', 'created_at', 'updated_at', 'ts', 'timestamp']
DIMENSION_HINTS = ['name', 'category', 'type', 'status', 'region', 'branch', 'city', 'country', 'code', 'id', 'label']
ID_SUFFIXES = ['_id', 'id']  # careful: 'id' alone is generic

# Optional DB sampling
try:
    from sqlalchemy import create_engine, text
except Exception:
    create_engine = None  # optional


def load_json(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return json.loads(p.read_text(encoding="utf-8"))


def guess_type_from_name(col: str) -> str:
    n = col.lower()
    if any(h in n for h in NUMERIC_HINTS) or n.endswith('_amt') or n.endswith('_amount') or n.endswith('_price'):
        return 'numeric'
    if any(h in n for h in DATE_HINTS) or n.endswith('_date') or n.endswith('_at') or n.endswith('_ts'):
        return 'date'
    # id heuristics - prefer id be dimension (but also entity identifier)
    if any(n.endswith(s) for s in ID_SUFFIXES) or n.lower().endswith('_key'):
        return 'id'
    # strings fallback
    if any(h in n for h in DIMENSION_HINTS):
        return 'dimension'
    # default: unknown -> treat as dimension
    return 'dimension'


def sample_column_types_from_db(table_name: str, columns: List[str], sample_rows: int = 5) -> Dict[str, str]:
    """
    Optional: connect to DATABASE_URL and sample rows to infer types.
    Returns mapping col -> inferred_type ('numeric'|'date'|'dimension'|'unknown')
    """
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        raise EnvironmentError("DATABASE_URL not set for sampling")
    if create_engine is None:
        raise ImportError("sqlalchemy not installed; cannot sample DB")

    eng = create_engine(db_url)
    col_list = ", ".join(columns[:100])  # safe limit
    qry = f"SELECT {col_list} FROM {table_name} LIMIT {sample_rows}"
    types = {}
    with eng.connect() as conn:
        try:
            res = conn.execute(text(qry))
            rows = [dict(r) for r in res]
        except Exception as e:
            logger.warning(f"Sampling query failed: {e}")
            return {c: 'unknown' for c in columns}

    for c in columns:
        types[c] = 'unknown'
    for r in rows:
        for c, v in r.items():
            if v is None:
                continue
            t = type(v)
            if t in (int, float):
                types[c] = 'numeric'
            else:
                sval = str(v)
                if re.match(r'^\d{4}-\d{2}-\d{2}', sval):
                    types[c] = 'date'
                elif re.match(r'^\d{4}-\d{2}-\d{2}T', sval):
                    types[c] = 'date'
                else:
                    if types[c] != 'numeric':
                        types[c] = 'dimension'
    return types


def infer_for_model(model_meta: Dict[str, Any],
                    use_db_sampling: bool = False,
                    sample_rows: int = 5) -> Dict[str, Any]:
    table_key = model_meta.get('name') or model_meta.get('unique_id')
    cols = list(model_meta.get('columns', {}).keys())
    inferred = {
        'table_name': table_key,
        'description': model_meta.get('description', ''),
        'columns': [],
        'dimensions': [],
        'measures': [],
        'time_columns': [],
        'derived_measures': [],
        'quality_rules': [],
        'hints': {}
    }

    db_types = {}
    if use_db_sampling:
        try:
            db_types = sample_column_types_from_db(table_key, cols, sample_rows=sample_rows)
            logger.info(f"Sampled DB types for {table_key}: {db_types}")
        except Exception as e:
            logger.warning(f"DB sampling failed for {table_key}: {e}")
            db_types = {}

    for c in cols:
        guessed = db_types.get(c) or guess_type_from_name(c)
        col_obj = {'name': c, 'type_guess': guessed, 'description': model_meta.get('columns', {}).get(c, {}).get('description', '')}
        inferred['columns'].append(col_obj)
        if guessed == 'numeric':
            inferred['measures'].append(c)
        elif guessed == 'date':
            inferred['time_columns'].append(c)
        else:
            inferred['dimensions'].append(c)

    colset = set(cols)
    if 'invoice_amount' in colset and 'amount_paid' in colset:
        inferred['derived_measures'].append({
            'name': 'paid_ratio',
            'expression': 'SUM(amount_paid) / NULLIF(SUM(invoice_amount), 0)',
            'type': 'ratio',
            'description': 'Fraction of invoice amount paid'
        })
        inferred['quality_rules'].append({
            'name': 'underpaid_flag',
            'expression': 'CASE WHEN amount_paid < 0.5 * invoice_amount THEN 1 ELSE 0 END',
            'description': 'Invoice paid less than 50%'
        })
    if 'discount_amount' in colset and 'invoice_amount' in colset:
        inferred['derived_measures'].append({
            'name': 'discount_pct',
            'expression': 'SUM(discount_amount) / NULLIF(SUM(invoice_amount), 0)',
            'type': 'ratio',
            'description': 'Discount as % of invoice amount'
        })
        inferred['quality_rules'].append({
            'name': 'high_discount_flag',
            'expression': 'CASE WHEN discount_amount > 0.3 * invoice_amount THEN 1 ELSE 0 END',
            'description': 'Discount > 30% of invoice'
        })

    for m in list(inferred['measures']):
        inferred['derived_measures'].append({
            'name': f'sum__{m}',
            'expression': f'SUM({m})',
            'type': 'sum',
            'description': f'Sum of {m}'
        })
        inferred['derived_measures'].append({
            'name': f'avg__{m}',
            'expression': f'AVG({m})',
            'type': 'avg',
            'description': f'Average of {m}'
        })

    if 'invoice_amount' in colset:
        inferred['derived_measures'].append({
            'name': 'branch_sales_contribution',
            'expression': 'SUM(invoice_amount) / NULLIF(SUM(invoice_amount) OVER (), 0)',
            'type': 'percentage',
            'description': 'Branch share of total invoice amount (partitioning to be applied at query-time)'
        })

    if 'invoice_amount' in colset:
        inferred['quality_rules'].append({
            'name': 'invalid_invoice_amount_flag',
            'expression': 'CASE WHEN invoice_amount <= 0 THEN 1 ELSE 0 END',
            'description': 'Invoice amount <= 0'
        })

    inferred['hints'] = {
        'measures_count': len(inferred['measures']),
        'dimensions_count': len(inferred['dimensions']),
        'time_columns_count': len(inferred['time_columns'])
    }

    return inferred


def infer_all(metadata: Dict[str, Any], use_db_sampling: bool = False, sample_rows: int = 5) -> Dict[str, Any]:
    out = {}
    for model_key, model_meta in metadata.items():
        logger.info(f"Inferring for model: {model_meta.get('name') or model_key}")
        inf = infer_for_model(model_meta, use_db_sampling=use_db_sampling, sample_rows=sample_rows)
        out[model_meta.get('name') or model_key] = inf
    return out


def write_json(out_path: str, data: Dict[str, Any]) -> None:
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"Wrote inferred metadata to {out_path}")


def cli_main():
    parser = argparse.ArgumentParser(description="Inference Engine for semantic JSON")
    parser.add_argument('--metadata', required=True, help='Path to manifest-reader output JSON (metadata.json)')
    parser.add_argument('--out', default='backend/metadata/inferred.json', help='Path to write inferred JSON')
    parser.add_argument('--use-db-sampling', action='store_true', help='Try sampling DB to get real types (requires DATABASE_URL)')
    parser.add_argument('--sample-rows', type=int, default=5, help='Number of sample rows for DB sampling')
    args = parser.parse_args()

    metadata = load_json(args.metadata)
    inferred = infer_all(metadata, use_db_sampling=args.use_db_sampling, sample_rows=args.sample_rows)
    write_json(args.out, inferred)


if __name__ == '__main__':
    cli_main()
