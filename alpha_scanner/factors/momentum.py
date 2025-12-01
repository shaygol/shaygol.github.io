"""
Momentum factor implementation.

Aggregates:
- RSI (14).
- MACD (12, 26, 9).
- Short/medium-term Rate of Change.
- Stochastic oscillator (%K).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .utils import (
    ensure_multiindex,
    rate_of_change,
    rolling_apply_grouped,
    validate_required_columns,
)


@dataclass
class MomentumConfig:
    """
    Simplified momentum configuration.

    For the PoC we use only short and medium term ROC to avoid
    complexity around multi-index alignment while still capturing
    meaningful momentum information.
    """

    roc_short: int = 10
    roc_long: int = 20


def _ema(series: pd.Series, span: int) -> pd.Series:
    """
    Exponential moving average that works for both MultiIndex
    (date, ticker) and single-index Series.
    """
    if isinstance(series.index, pd.MultiIndex):
        return (
            series.groupby(level="ticker")
            .apply(
                lambda s: s.droplevel("ticker").ewm(span=span, adjust=False).mean()
            )
            .reset_index(level=0, drop=True)
        )
    # Fallback: treat as a single time series
    return series.ewm(span=span, adjust=False).mean()


def _rsi(close: pd.Series, period: int) -> pd.Series:
    diff = close.groupby(level="ticker").diff()
    up = diff.clip(lower=0.0)
    down = -diff.clip(upper=0.0)

    roll_up = rolling_apply_grouped(up, period, lambda x: x.mean())
    roll_down = rolling_apply_grouped(down, period, lambda x: x.mean())

    rs = roll_up / roll_down.replace(0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi


def _stochastic_k(df: pd.DataFrame, period: int) -> pd.Series:
    high = df["high"]
    low = df["low"]
    close = df["close"]

    rolling_high = rolling_apply_grouped(high, period, max)
    rolling_low = rolling_apply_grouped(low, period, min)

    return (close - rolling_low) / (rolling_high - rolling_low).replace(0, np.nan)


def compute_momentum_score(
    df: pd.DataFrame,
    config: MomentumConfig | None = None,
) -> pd.Series:
    """
    Compute Momentum raw factor per (date, ticker).

    PoC implementation: blend of short and medium-term ROC.
    """
    if config is None:
        config = MomentumConfig()

    validate_required_columns(df, ["date", "ticker", "close"])
    df = ensure_multiindex(df)

    close = df["close"]

    roc_short = rate_of_change(close, config.roc_short)
    roc_long = rate_of_change(close, config.roc_long)

    momentum_raw = 0.6 * roc_short.fillna(0.0) + 0.4 * roc_long.fillna(0.0)
    momentum_raw.name = "Momentum_raw"
    return momentum_raw


