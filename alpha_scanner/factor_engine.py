"""
Factor aggregation engine.

Responsible for:
- Calling each factor module to compute raw factor values.
- Rank-normalizing factors cross-sectionally per date.
- Returning a unified factor matrix for use by the Calibrator or
  downstream scanners.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd

from . import factors
from .factors.utils import ensure_multiindex, rank_normalize


@dataclass
class FactorEngineConfig:
    """Configuration flags for which factors to compute."""

    use_rs: bool = True
    use_trend: bool = True
    use_squeeze: bool = True
    use_momentum: bool = True
    use_volume: bool = True


def compute_factor_matrix(
    df: pd.DataFrame,
    benchmark_prices: Optional[pd.Series] = None,
    config: Optional[FactorEngineConfig] = None,
) -> pd.DataFrame:
    """
    Compute rank-normalized factor scores for all enabled factors.

    Parameters
    ----------
    df:
        OHLCV data with at least
        ['date', 'ticker', 'open', 'high', 'low', 'close', 'volume'].
    benchmark_prices:
        Optional benchmark close series (e.g. SPY) for RS.
    config:
        FactorEngineConfig.
    """
    if config is None:
        config = FactorEngineConfig()

    df = ensure_multiindex(df)

    raw_factors = {}

    if config.use_rs:
        rs_raw = factors.compute_rs_score(df, benchmark_prices=benchmark_prices)
        raw_factors["RS_raw"] = rs_raw

    if config.use_trend:
        trend_raw = factors.compute_trend_score(df)
        raw_factors["Trend_raw"] = trend_raw

    if config.use_squeeze:
        squeeze_raw = factors.compute_squeeze_score(df)
        raw_factors["Squeeze_raw"] = squeeze_raw

    if config.use_momentum:
        momentum_raw = factors.compute_momentum_score(df)
        raw_factors["Momentum_raw"] = momentum_raw

    if config.use_volume:
        volume_raw = factors.compute_volume_score(df)
        raw_factors["Volume_raw"] = volume_raw

    raw_df = pd.DataFrame(raw_factors)
    raw_df.index = df.index

    scores = {}
    for col in raw_df.columns:
        scores[col.replace("_raw", "_score")] = rank_normalize(raw_df[col])

    scores_df = pd.DataFrame(scores)
    scores_df.index = raw_df.index
    return scores_df


