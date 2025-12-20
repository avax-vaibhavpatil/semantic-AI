
#!/usr/bin/env python3
"""
semantic_generator.py

Takes inferred.json (output of inference_engine.py) and produces
a clean semantic.json formatted consistently for the SQL Agent.

Usage:
    python semantic_generator.py --inferred backend/metadata/inferred.json --out backend/metadata/semantic.json
"""

import json
import argparse
from pathlib import Path
from typing import Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("semantic_generator")


def load_json(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return json.loads(p.read_text(encoding="utf-8"))


def build_table_block(inferred_table: Dict[str, Any]) -> Dict[str, Any]:
    table_name = inferred_table["table_name"]
    description = inferred_table.get("description", "")

    columns = {}
    for c in inferred_table["columns"]:
        col_name = c["name"]
        col_type = c.get("type_guess", "dimension")
        columns[col_name] = {"type": col_type}

    return {
        "description": description,
        "columns": columns,
        "dimensions": inferred_table.get("dimensions", []),
        "measures": inferred_table.get("measures", []),
        "derived_measures": inferred_table.get("derived_measures", []),
        "quality_rules": inferred_table.get("quality_rules", []),
        "time_columns": inferred_table.get("time_columns", []),
    }


def build_semantic_json(inferred: Dict[str, Any]) -> Dict[str, Any]:
    semantic = {"tables": {}}

    for table_name, inferred_table in inferred.items():
        logger.info(f"Building semantic layer for: {table_name}")
        semantic["tables"][table_name] = build_table_block(inferred_table)

    return semantic


def write_json(path: str, data: Dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"Semantic JSON written to {path}")


def cli_main():
    parser = argparse.ArgumentParser(description="Generate semantic.json from inferred.json")
    parser.add_argument("--inferred", required=True, help="Path to inferred.json")
    parser.add_argument("--out", default="backend/metadata/semantic.json", help="Path to write semantic.json")
    args = parser.parse_args()

    inferred = load_json(args.inferred)
    semantic = build_semantic_json(inferred)
    write_json(args.out, semantic)


if __name__ == "__main__":
    cli_main()
