"""
Relative Strength (RS) factor.

Implements the RS factor as described in the plan:
- Performance vs SPY (or other benchmark) over multiple horizons.
- Fallback to pure momentum-style RS when no benchmark is supplied.

All sub-elements are aggregated into a single raw RS factor, which is
later rank-normalized by the factor engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd

from .utils import ensure_multiindex, rate_of_change, validate_required_columns


@dataclass
class RSConfig:
    """Configuration for RS factor horizons (in trading days)."""

    short_window: int = 21  # ~1M
    mid_window: int = 63  # ~3M
    long_window: int = 126  # ~6M
    very_long_window: int = 252  # ~12M


def _compute_rs_vs_benchmark(
    prices: pd.Series,
    benchmark: pd.Series,
    window: int,
) -> pd.Series:
    """
    Compute relative strength vs benchmark as excess ROC over `window`.
    """
    roc_asset = rate_of_change(prices, window=window)
    roc_bench = rate_of_change(benchmark, window=window)
    roc_bench_aligned = roc_bench.reindex(roc_asset.index, method="ffill")
    return roc_asset - roc_bench_aligned


def compute_rs_score(
    df: pd.DataFrame,
    benchmark_prices: Optional[pd.Series] = None,
    config: Optional[RSConfig] = None,
) -> pd.Series:
    """
    Compute RS raw factor per (date, ticker).

    Parameters
    ----------
    df:
        OHLCV data with at least ['date', 'ticker', 'close'].
    benchmark_prices:
        Optional Series of benchmark close prices indexed by date (e.g. SPY).
        If not provided, RS is computed purely from the asset's own momentum.
    config:
        RSConfig with horizon windows.
    """
    if config is None:
        config = RSConfig()

    validate_required_columns(df, ["date", "ticker", "close"])
    df = ensure_multiindex(df)

    close = df["close"]

    if benchmark_prices is None:
        rs_short = rate_of_change(close, config.short_window)
        rs_mid = rate_of_change(close, config.mid_window)
        rs_long = rate_of_change(close, config.long_window)
        rs_vlong = rate_of_change(close, config.very_long_window)
    else:
        bench_multi = benchmark_prices.reindex(
            close.index.get_level_values("date")
        )
        bench_multi.index = close.index

        rs_short = _compute_rs_vs_benchmark(close, bench_multi, config.short_window)
        rs_mid = _compute_rs_vs_benchmark(close, bench_multi, config.mid_window)
        rs_long = _compute_rs_vs_benchmark(close, bench_multi, config.long_window)
        rs_vlong = _compute_rs_vs_benchmark(
            close, bench_multi, config.very_long_window
        )

    rs_raw = (
        0.1 * rs_short
        + 0.3 * rs_mid
        + 0.3 * rs_long
        + 0.3 * rs_vlong
    )
    rs_raw.name = "RS_raw"
    return rs_raw


