"""
Calibrator module.

Phase 1 (PoC):
- Evaluate a small, fixed set of candidate factor weight vectors.
- Backtest each candidate with optional TCCM costs.
- Select the best-performing weights by net Sharpe (and constraints).

Phase 2 (Production, to be extended):
- Upgrade to Dirichlet Sampling, walk-forward, Bootstrap, and stability
  checks as described in the plan.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Tuple

import numpy as np
import pandas as pd

from .factor_engine import compute_factor_matrix
from .tccm import TCCMConfig, estimate_trade_costs
from .factors.utils import ensure_multiindex


@dataclass
class BacktestConfig:
    """
    Simplified backtest configuration for Phase 1.
    """

    volatility_target: float = 0.10  # target annualized volatility (placeholder)
    tc_config: TCCMConfig | None = None


def _positions_from_scores(
    scores: pd.Series,
    volatility_target: float,
    prices: pd.Series,
) -> pd.Series:
    """
    Very simplified volatility targeting:
    - Normalize scores to sum of absolutes = 1 per date.
    - Scale to constant notional (1.0).
    """
    scores_wide = scores.unstack("ticker")
    norm = scores_wide.abs().sum(axis=1).replace(0, np.nan)
    weights = scores_wide.div(norm, axis=0).fillna(0.0)

    capital = 1.0
    dollar_positions = weights * capital

    prices_wide = prices.unstack("ticker")
    shares = dollar_positions / prices_wide.replace(0, np.nan)
    shares = shares.fillna(0.0)

    return shares.stack().rename("position")


def _compute_returns(prices: pd.Series) -> pd.Series:
    """
    Daily log returns per (date, ticker).
    """
    prices_wide = prices.unstack("ticker")
    rets = np.log(prices_wide / prices_wide.shift(1))
    return rets.stack().rename("ret")


def backtest_weights(
    df: pd.DataFrame,
    weights: Dict[str, float],
    bt_config: BacktestConfig,
) -> Tuple[float, pd.Series]:
    """
    Run a very simplified backtest for a given factor weight vector.

    Returns
    -------
    sharpe_net:
        Cost-adjusted Sharpe ratio (annualized).
    equity_curve:
        Series of cumulative returns.
    """
    df = ensure_multiindex(df)

    # Lazily create default TCCMConfig to avoid mutable dataclass defaults
    if bt_config.tc_config is None:
        bt_config.tc_config = TCCMConfig()

    factor_scores = compute_factor_matrix(df)

    composite = sum(
        w * factor_scores[col]
        for col, w in weights.items()
        if col in factor_scores.columns
    )
    composite.name = "composite_score"

    prices = df["close"]
    volume = df.get("volume", pd.Series(index=df.index, dtype=float))

    asset_returns = _compute_returns(prices)

    positions = _positions_from_scores(
        composite, bt_config.volatility_target, prices
    )
    positions_prev = positions.groupby(level="ticker").shift(1).fillna(0.0)

    vol_proxy = (
        asset_returns.groupby(level="ticker")
        .rolling(window=20, min_periods=20)
        .std()
        .reset_index(level=0, drop=True)
    )

    trade_costs = estimate_trade_costs(
        positions_prev=positions_prev,
        positions_next=positions,
        prices=prices,
        volume=volume,
        volatility=vol_proxy,
        config=bt_config.tc_config,
    )

    asset_returns_wide = asset_returns.unstack("ticker")
    positions_prev_wide = positions_prev.unstack("ticker")
    port_ret = (positions_prev_wide * asset_returns_wide).sum(axis=1)

    trade_costs_daily = (
        trade_costs.unstack("ticker").sum(axis=1).reindex(port_ret.index).fillna(0.0)
    )
    port_ret_net = port_ret - trade_costs_daily

    mu = port_ret_net.mean() * 252
    sigma = port_ret_net.std(ddof=0) * np.sqrt(252)
    sharpe = mu / sigma if sigma > 0 else 0.0

    equity_curve = (1.0 + port_ret_net).cumprod()

    return float(sharpe), equity_curve


def calibrate_phase1(
    df: pd.DataFrame,
    candidate_weights: Iterable[Dict[str, float]],
    bt_config: BacktestConfig | None = None,
) -> Tuple[Dict[str, float], float]:
    """
    Phase 1 Calibrator.

    Parameters
    ----------
    df:
        Historical OHLCV data.
    candidate_weights:
        Iterable of dictionaries mapping factor names (e.g. 'RS_score') to
        weights that sum (roughly) to 1.
    bt_config:
        BacktestConfig.

    Returns
    -------
    best_weights, best_sharpe
    """
    if bt_config is None:
        bt_config = BacktestConfig()

    best_sharpe = -np.inf
    best_weights: Dict[str, float] = {}

    for w in candidate_weights:
        sharpe, _eq = backtest_weights(df, w, bt_config)
        if sharpe > best_sharpe:
            best_sharpe = sharpe
            best_weights = dict(w)

    return best_weights, float(best_sharpe)


