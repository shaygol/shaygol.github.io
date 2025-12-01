"""
Data snapshot, checksum, and schema validation utilities.

Implements:
- Saving raw data snapshots to Parquet with timestamped filenames.
- Calculating file checksums.
- Simple schema/type validation and schema-diff detection.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict

import pandas as pd


@dataclass
class SchemaDefinition:
    """
    Expected schema definition for input data.

    `dtypes` maps column name -> pandas dtype string (e.g. 'float32').
    """

    dtypes: Dict[str, str]

    def to_json(self) -> str:
        return json.dumps(self.dtypes, sort_keys=True)

    @classmethod
    def from_json(cls, s: str) -> "SchemaDefinition":
        return cls(dtypes=json.loads(s))


def save_raw_snapshot(
    df: pd.DataFrame,
    output_dir: str | Path,
    label: str = "raw",
) -> Path:
    """
    Save a raw Parquet snapshot with a timestamped filename and return the path.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"{label}_snapshot_{ts}.parquet"
    path = output_dir / filename

    df.to_parquet(path)
    return path


def calculate_checksum(path: str | Path, algo: str = "sha256") -> str:
    """
    Calculate a checksum of a file using the selected algorithm.
    """
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_schema(
    df: pd.DataFrame,
    schema: SchemaDefinition,
) -> None:
    """
    Validate that the DataFrame conforms to the expected schema.

    Raises ValueError when a mismatch is detected.
    """
    missing_cols = set(schema.dtypes) - set(df.columns)
    extra_cols = set(df.columns) - set(schema.dtypes)
    if missing_cols:
        raise ValueError(f"Missing columns: {sorted(missing_cols)}")

    for col, expected_dtype in schema.dtypes.items():
        if col not in df.columns:
            continue
        actual = str(df[col].dtype)
        if actual != expected_dtype:
            raise ValueError(
                f"Column {col!r} has dtype {actual}, expected {expected_dtype}"
            )

    # extra_cols are allowed; the caller may treat this as schema diff
    _ = extra_cols


def detect_schema_diff(
    df: pd.DataFrame,
    reference_schema: SchemaDefinition,
) -> Dict[str, list]:
    """
    Compare DataFrame schema with a reference and return a diff structure.
    """
    missing_cols = sorted(set(reference_schema.dtypes) - set(df.columns))
    extra_cols = sorted(set(df.columns) - set(reference_schema.dtypes))

    mismatched_types = []
    for col, expected_dtype in reference_schema.dtypes.items():
        if col not in df.columns:
            continue
        actual = str(df[col].dtype)
        if actual != expected_dtype:
            mismatched_types.append(
                {"column": col, "expected": expected_dtype, "actual": actual}
            )

    return {
        "missing_columns": missing_cols,
        "extra_columns": extra_cols,
        "mismatched_types": mismatched_types,
    }


