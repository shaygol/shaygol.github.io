
"""
Factor computation modules.

Each module exposes a `compute_<factor>_score` function that accepts a
DataFrame with OHLCV data for a universe of tickers and returns a
Series with a raw factor value per (date, ticker).

Raw factors are later rank-normalized by `factor_engine.compute_factor_matrix`.
"""

from .rs import compute_rs_score  # noqa: F401
from .trend import compute_trend_score  # noqa: F401
from .squeeze import compute_squeeze_score  # noqa: F401
from .momentum import compute_momentum_score  # noqa: F401
from .volume import compute_volume_score  # noqa: F401


