"""
Shared technical-analysis utilities used across factor modules.
"""

from __future__ import annotations

from typing import Iterable, Callable

import numpy as np
import pandas as pd


def ensure_multiindex(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure the DataFrame is indexed by ['date', 'ticker'] in that order.

    Expected columns: at least ['date', 'ticker'].
    """
    if isinstance(df.index, pd.MultiIndex):
        # If index already includes date/ticker, just ensure order
        names = list(df.index.names)
        if "date" in names and "ticker" in names:
            # Reorder if necessary
            if names != ["date", "ticker"]:
                df = df.reorder_levels(["date", "ticker"]).sort_index()
            else:
                df = df.sort_index()
            return df

    if {"date", "ticker"}.issubset(df.columns):
        return df.set_index(["date", "ticker"]).sort_index()

    raise ValueError(
        "DataFrame must have a MultiIndex (date, ticker) or columns ['date', 'ticker']"
    )


def validate_required_columns(df: pd.DataFrame, cols: Iterable[str]) -> None:
    """Raise if required label columns/index levels are missing."""
    present = set(df.columns) | set(df.index.names or [])
    missing = set(cols) - present
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")


def simple_moving_average(series: pd.Series, window: int) -> pd.Series:
    """Simple moving average along the time axis within each ticker."""
    return (
        series.groupby(level="ticker")
        .rolling(window=window, min_periods=window)
        .mean()
        .reset_index(level=0, drop=True)
    )


def rate_of_change(series: pd.Series, window: int) -> pd.Series:
    """Percentage rate of change over `window` days within each ticker."""
    prev = series.groupby(level="ticker").shift(window)
    return (series / prev - 1.0) * 100.0


def atr(df: pd.DataFrame, window: int = 14) -> pd.Series:
    """
    Average True Range (ATR) per (date, ticker).

    Expects columns: 'high', 'low', 'close'.
    """
    df = ensure_multiindex(df.copy())

    high = df["high"]
    low = df["low"]
    close = df["close"]

    prev_close = close.groupby(level="ticker").shift(1)

    tr = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    atr_series = (
        tr.groupby(level="ticker")
        .rolling(window=window, min_periods=window)
        .mean()
        .reset_index(level=0, drop=True)
    )
    atr_series.name = "atr"
    return atr_series


def rank_normalize(
    series: pd.Series,
    lower: float = -1.0,
    upper: float = 1.0,
) -> pd.Series:
    """
    Cross-sectionally rank-normalize a Series per date to [lower, upper].

    Expects a MultiIndex (date, ticker).
    """
    if not isinstance(series.index, pd.MultiIndex):
        raise ValueError("Series must use a MultiIndex (date, ticker)")

    def _rank(group: pd.Series) -> pd.Series:
        n = len(group)
        if n <= 1:
            return pd.Series(0.0, index=group.index)
        ranks = group.rank(method="average")
        scaled = lower + (ranks - 1.0) * (upper - lower) / (n - 1.0)
        return scaled

    return series.groupby(level="date").transform(_rank)


def zscore_cross_sectional(series: pd.Series) -> pd.Series:
    """
    Cross-sectional z-score per date.
    """

    def _z(group: pd.Series) -> pd.Series:
        mu = group.mean()
        sigma = group.std(ddof=0)
        if sigma == 0 or np.isnan(sigma):
            return pd.Series(0.0, index=group.index)
        return (group - mu) / sigma

    return series.groupby(level="date").transform(_z)


def rolling_apply_grouped(
    series: pd.Series,
    window: int,
    func: Callable[[pd.Series], float],
) -> pd.Series:
    """
    Helper to apply a rolling function within each ticker group.
    """
    return (
        series.groupby(level="ticker")
        .rolling(window=window, min_periods=window)
        .apply(func, raw=False)
        .reset_index(level=0, drop=True)
    )


