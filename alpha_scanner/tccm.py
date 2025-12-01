"""
Transaction Cost & Capacity Model (TCCM).

Implements:
- Commission + Market Impact Cost (MIC) slippage formula.
- Simple capacity metric based on OrderSize / ADV.

For PoC usage this module can be configured with very small or zero
commissions/impact and used primarily for diagnostics.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class TCCMConfig:
    commission_per_share: float = 0.0
    calibration_constant: float = 0.005  # 50 bps as decimal
    impact_alpha: float = 0.75
    adv_window: int = 20


def compute_adv(volume: pd.Series, window: int) -> pd.Series:
    """
    Compute Average Daily Volume (ADV) per (date, ticker).
    """
    return (
        volume.groupby(level="ticker")
        .rolling(window=window, min_periods=window)
        .mean()
        .reset_index(level=0, drop=True)
    )


def estimate_trade_costs(
    positions_prev: pd.Series,
    positions_next: pd.Series,
    prices: pd.Series,
    volume: pd.Series,
    volatility: pd.Series,
    config: TCCMConfig | None = None,
) -> pd.Series:
    """
    Estimate dollar trading costs for position changes.

    Parameters
    ----------
    positions_prev, positions_next:
        Position sizes in shares per (date, ticker).
    prices:
        Close prices per (date, ticker).
    volume:
        Traded volume per (date, ticker) (shares).
    volatility:
        Volatility proxy (e.g., ATR or stdev) per (date, ticker).
    """
    if config is None:
        config = TCCMConfig()

    delta_shares = (positions_next - positions_prev).abs()
    dollar_size = delta_shares * prices

    adv = compute_adv(volume, window=config.adv_window)

    commission = delta_shares * config.commission_per_share

    with np.errstate(divide="ignore", invalid="ignore"):
        size_over_adv = dollar_size / adv.replace(0, np.nan)
        mic = (
            config.calibration_constant
            * (size_over_adv ** config.impact_alpha)
            * volatility
        )

    cost = commission + mic.fillna(0.0)
    cost.name = "trade_cost"
    return cost


def compute_capacity_usage(
    positions: pd.Series,
    prices: pd.Series,
    volume: pd.Series,
    config: TCCMConfig | None = None,
) -> pd.Series:
    """
    Compute Capacity_Usage = OrderSize / ADV.
    """
    if config is None:
        config = TCCMConfig()

    dollar_size = positions.abs() * prices
    adv = compute_adv(volume, window=config.adv_window)
    capacity_usage = dollar_size / adv.replace(0, np.nan)
    capacity_usage.name = "capacity_usage"
    return capacity_usage


