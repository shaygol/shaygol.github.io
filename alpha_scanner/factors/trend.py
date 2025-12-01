"""
Trend factor implementation.

Aggregates several sub-elements into a single raw Trend factor:
- SMA 50 vs SMA 200 (Golden/Death Cross).
- Distance from SMA 200.
- Slope of SMA 50 and SMA 200.
- Price vs short-term SMA (20).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .utils import (
    ensure_multiindex,
    simple_moving_average,
    validate_required_columns,
)


@dataclass
class TrendConfig:
    sma_short: int = 20
    sma_med: int = 50
    sma_long: int = 200
    slope_window: int = 20


def compute_trend_score(
    df: pd.DataFrame,
    config: TrendConfig | None = None,
) -> pd.Series:
    """
    Compute Trend raw factor per (date, ticker).

    Parameters
    ----------
    df:
        OHLCV data with at least ['date', 'ticker', 'close'].
    """
    if config is None:
        config = TrendConfig()

    validate_required_columns(df, ["date", "ticker", "close"])
    df = ensure_multiindex(df)

    close = df["close"]

    sma_short = simple_moving_average(close, config.sma_short)
    sma_med = simple_moving_average(close, config.sma_med)
    sma_long = simple_moving_average(close, config.sma_long)

    # Golden / Death cross state encoded as {-1, 0, +1}
    cross_state = np.sign(sma_med - sma_long)

    # Distance from long-term trend
    dist_long = (close - sma_long) / sma_long.replace(0, np.nan)

    # Slopes (difference over window)
    sma_med_shifted = sma_med.groupby(level="ticker").shift(config.slope_window)
    slope_med = (sma_med - sma_med_shifted) / max(config.slope_window, 1)

    sma_long_shifted = sma_long.groupby(level="ticker").shift(config.slope_window)
    slope_long = (sma_long - sma_long_shifted) / max(config.slope_window, 1)

    # Price position vs short SMA (captures short-term trend alignment)
    pos_short = (close - sma_short) / sma_short.replace(0, np.nan)

    trend_raw = (
        0.35 * cross_state.fillna(0.0)
        + 0.25 * dist_long.fillna(0.0)
        + 0.2 * slope_med.fillna(0.0)
        + 0.1 * slope_long.fillna(0.0)
        + 0.1 * pos_short.fillna(0.0)
    )
    trend_raw.name = "Trend_raw"
    return trend_raw


