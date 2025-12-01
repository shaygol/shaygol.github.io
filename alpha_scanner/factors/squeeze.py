"""
Squeeze factor implementation.

Captures volatility contraction/expansion patterns via:
- Bollinger Bands vs Keltner Channels compression.
- ATR-based volatility ratio (short vs long term).
- Simple range/ATR proxy for trend strength.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .utils import (
    atr,
    ensure_multiindex,
    simple_moving_average,
    validate_required_columns,
)


@dataclass
class SqueezeConfig:
    bb_window: int = 20
    bb_std: float = 2.0
    kc_window: int = 20
    kc_mult: float = 1.5
    atr_short: int = 20
    atr_long: int = 252


def compute_squeeze_score(
    df: pd.DataFrame,
    config: SqueezeConfig | None = None,
) -> pd.Series:
    """
    Compute Squeeze raw factor per (date, ticker).
    """
    if config is None:
        config = SqueezeConfig()

    validate_required_columns(df, ["date", "ticker", "high", "low", "close"])
    df = ensure_multiindex(df)

    close = df["close"]
    high = df["high"]
    low = df["low"]

    # Bollinger Bands
    mid_bb = simple_moving_average(close, config.bb_window)
    rolling_std = (
        close.groupby(level="ticker")
        .rolling(window=config.bb_window, min_periods=config.bb_window)
        .std()
        .reset_index(level=0, drop=True)
    )
    upper_bb = mid_bb + config.bb_std * rolling_std
    lower_bb = mid_bb - config.bb_std * rolling_std
    bb_width = (upper_bb - lower_bb) / mid_bb.replace(0, np.nan)

    # Keltner Channels (using ATR)
    mid_kc = simple_moving_average(close, config.kc_window)
    atr_series = atr(df, window=config.kc_window)
    upper_kc = mid_kc + config.kc_mult * atr_series
    lower_kc = mid_kc - config.kc_mult * atr_series
    kc_width = (upper_kc - lower_kc) / mid_kc.replace(0, np.nan)

    squeeze_flag = (bb_width < kc_width).astype(float)

    # Volatility ratio (short vs long)
    atr_short = atr(df, window=config.atr_short)
    atr_long = atr(df, window=config.atr_long)
    vol_ratio = atr_short / atr_long.replace(0, np.nan)

    # Range/ATR proxy
    range_bar = (high - low)
    range_over_atr = range_bar / atr_short.replace(0, np.nan)

    squeeze_raw = (
        0.4 * squeeze_flag.fillna(0.0)
        + 0.3 * (-vol_ratio.fillna(0.0))  # prefer compressed vol
        + 0.3 * range_over_atr.fillna(0.0)
    )
    squeeze_raw.name = "Squeeze_raw"
    return squeeze_raw


