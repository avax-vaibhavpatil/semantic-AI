#!/usr/bin/env python3
"""
manifest_reader.py

Reads dbt's target/manifest.json and extracts "wide" models (or those matching a tag/filter).
Produces a compact metadata JSON for downstream semantic generation.

Usage:
    python manifest_reader.py --manifest target/manifest.json --out metadata.json --filter-tag wide
    python manifest_reader.py --manifest target/manifest.json --out metadata.json --name-matches branch_sales_wide
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
import argparse
import re
import os
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("manifest_reader")


def load_json(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return json.loads(p.read_text(encoding="utf-8"))


def model_matches_filters(node: Dict[str, Any],
                          filter_tag: Optional[str] = None,
                          name_matches: Optional[str] = None,
                          include_all: bool = False) -> bool:
    """
    Decide whether to include a model node.
    - filter_tag: include models that have this tag OR model name contains this string
    - name_matches: include models whose name contains this string (case-insensitive)
    - include_all: include all models
    """

    if include_all:
        return True

    model_name = node.get("name", "") or node.get("unique_id", "")
    tags = node.get("config", {}).get("tags", []) or node.get("tags", [])

    if filter_tag:
        if filter_tag in tags:
            return True
        if filter_tag.lower() in model_name.lower():
            return True

    if name_matches:
        if name_matches.lower() in model_name.lower():
            return True

    # default: reject
    return False


def extract_columns_from_node(node: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Extract column metadata from a dbt manifest model node.
    manifest nodes contain `columns` mapping with description, tests, meta etc.
    """
    cols = {}
    raw_cols = node.get("columns", {}) or {}
    for col_name, col_meta in raw_cols.items():
        # col_meta structure in dbt manifest has keys: description, tests, meta, quotation
        if isinstance(col_meta, dict):
            cols[col_name] = {
                "description": col_meta.get("description", ""),
                "tags": col_meta.get("tags", []),
                "meta": col_meta.get("meta", {}),
            }
        else:
            cols[col_name] = {"description": "", "tags": [], "meta": {}}
    return cols


def read_manifest_models(manifest_path: str,
                         filter_tag: Optional[str] = None,
                         name_matches: Optional[str] = None,
                         include_all: bool = False) -> Dict[str, Dict[str, Any]]:
    """
    Read manifest.json and return compact models dict.

    Output schema:
    {
      <unique_id or name>: {
         name: <name>,
         unique_id: <unique_id>,
         resource_type: <model|seed|...>,
         path: <original_file_path>,
         description: <desc>,
         columns: { col_name: {description, tags, meta}, ... },
         tags: [...],
         materialized: "table/view",
      }
    }
    """
    manifest = load_json(manifest_path)
    nodes = manifest.get("nodes", {}) or {}
    models = {}

    for node_id, node in nodes.items():
        # node.resource_type == 'model' typically
        if node.get("resource_type") != "model":
            continue

        # filter
        if not model_matches_filters(node, filter_tag, name_matches, include_all):
            continue

        model_key = node.get("unique_id") or node.get("name")
        models[model_key] = {
            "name": node.get("name"),
            "unique_id": node.get("unique_id"),
            "resource_type": node.get("resource_type"),
            "original_file_path": node.get("original_file_path"),
            "package_name": node.get("package_name"),
            "description": node.get("description", ""),
            "columns": extract_columns_from_node(node),
            "tags": node.get("tags") or node.get("config", {}).get("tags", []),
            "meta": node.get("meta", {}),
            "config": node.get("config", {}),
            "materialized": (node.get("config") or {}).get("materialized"),
        }

    # also inspect "sources" if needed (optional)
    # sources = manifest.get("sources", {})

    return models


def save_metadata(out_path: str, data: Dict[str, Any]) -> None:
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def cli_main():
    parser = argparse.ArgumentParser(description="DBT Manifest Reader")
    parser.add_argument("--manifest", required=True, help="Path to target/manifest.json")
    parser.add_argument("--out", default="metadata.json", help="Path to output compact metadata JSON")
    parser.add_argument("--filter-tag", default=None, help="Only include models with this tag or name substring")
    parser.add_argument("--name-matches", default=None, help="Only include models where name contains this substring")
    parser.add_argument("--include-all", action="store_true", help="Include all models (no filtering)")
    args = parser.parse_args()

    try:
        models = read_manifest_models(args.manifest, args.filter_tag, args.name_matches, include_all=args.include_all)
        if not models:
            logger.warning("No models matched filters. Output will be empty JSON.")
        save_metadata(args.out, models)
        logger.info(f"Wrote metadata for {len(models)} models to {args.out}")
    except Exception as exc:
        logger.exception("Failed to read manifest")
        sys.exit(2)


# Small helper function to pretty-print for debugging / dev
def pretty_print_models(models: Dict[str, Any], limit: int = 20):
    for k, v in list(models.items())[:limit]:
        print(f"MODEL: {v.get('name')} (unique_id: {v.get('unique_id')})")
        print(f"  path: {v.get('original_file_path')}")
        desc = v.get('description') or ''
        print(f"  desc: {desc[:120]}")
        print(f"  cols: {len(v.get('columns', {}))}")
        print(f"  tags: {v.get('tags')}")
        print("")
