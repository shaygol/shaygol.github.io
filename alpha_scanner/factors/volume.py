"""
Volume factor implementation.

Aggregates:
- Volume momentum / acceleration.
- Volume vs moving-average ratios.
- Simple price-volume divergence proxy.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .utils import (
    ensure_multiindex,
    rate_of_change,
    simple_moving_average,
    validate_required_columns,
)


@dataclass
class VolumeConfig:
    vol_ma_short: int = 20
    vol_ma_long: int = 50
    roc_window: int = 20


def compute_volume_score(
    df: pd.DataFrame,
    config: VolumeConfig | None = None,
) -> pd.Series:
    """
    Compute Volume raw factor per (date, ticker).
    """
    if config is None:
        config = VolumeConfig()

    validate_required_columns(df, ["date", "ticker", "close", "volume"])
    df = ensure_multiindex(df)

    close = df["close"]
    volume = df["volume"]

    vol_ma_short = simple_moving_average(volume, config.vol_ma_short)
    vol_ma_long = simple_moving_average(volume, config.vol_ma_long)

    vol_ratio_short = volume / vol_ma_short.replace(0, np.nan)
    vol_ratio_long = volume / vol_ma_long.replace(0, np.nan)

    vol_roc = rate_of_change(volume, config.roc_window)
    price_roc = rate_of_change(close, config.roc_window)
    divergence = price_roc - vol_roc

    volume_raw = (
        0.35 * vol_ratio_short.fillna(0.0)
        + 0.25 * vol_ratio_long.fillna(0.0)
        + 0.25 * vol_roc.fillna(0.0)
        + 0.15 * (-divergence.fillna(0.0))
    )
    volume_raw.name = "Volume_raw"
    return volume_raw


