"""
Reporter module for generating the final Excel deliverable.

Main entry point:
- `write_scanner_results_excel(...)` which produces
  `scanner_results_[DATE].xlsx` compatible with the plan's specification.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Optional

import pandas as pd


def write_scanner_results_excel(
    output_path: str | Path,
    candidates: pd.DataFrame,
    run_date: Optional[date] = None,
) -> Path:
    """
    Write the Top N candidates to an Excel workbook.

    Parameters
    ----------
    output_path:
        Directory or full path. If a directory is provided, a filename
        `scanner_results_[DATE].xlsx` will be created inside it.
    candidates:
        DataFrame with at least the following columns:
        - 'ticker'
        - 'composite_score'
        - 'vol_adj_shares'
        - 'est_entry_price'
        - 'est_slippage_cost'
        - 'capacity_usage'
        - 'significance'
    run_date:
        Optional date override; otherwise uses today's date.
    """
    output_path = Path(output_path)

    if output_path.is_dir():
        rd = run_date or date.today()
        filename = f"scanner_results_{rd.isoformat()}.xlsx"
        filepath = output_path / filename
    else:
        filepath = output_path

    required_cols = [
        "ticker",
        "composite_score",
        "vol_adj_shares",
        "est_entry_price",
        "est_slippage_cost",
        "capacity_usage",
        "significance",
    ]
    missing = [c for c in required_cols if c not in candidates.columns]
    if missing:
        raise ValueError(f"Missing required candidate columns: {missing}")

    df = candidates.copy()
    df["Rank"] = df["composite_score"].rank(
        method="first", ascending=False
    ).astype(int)
    df = df.sort_values("Rank")

    sheet = df[
        [
            "Rank",
            "ticker",
            "composite_score",
            "vol_adj_shares",
            "est_entry_price",
            "est_slippage_cost",
            "capacity_usage",
            "significance",
        ]
    ].rename(
        columns={
            "ticker": "Ticker",
            "composite_score": "Composite Score",
            "vol_adj_shares": "Vol_Adj_Shares",
            "est_entry_price": "Est_Entry_Price",
            "est_slippage_cost": "Est_Slippage_Cost",
            "capacity_usage": "Capacity_Usage",
            "significance": "Significance",
        }
    )

    with pd.ExcelWriter(filepath, engine="xlsxwriter") as writer:
        sheet.to_excel(writer, sheet_name="Top 20 Candidates", index=False)

    return filepath


