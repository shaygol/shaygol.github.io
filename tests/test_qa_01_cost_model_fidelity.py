import numpy as np
import pandas as pd

from alpha_scanner.calibrator import BacktestConfig, calibrate_phase1
from alpha_scanner.tccm import TCCMConfig


def test_qa01_cost_model_fidelity():
    """
    QA-01: Cost Model Fidelity

    Run a simulation with a relatively illiquid asset and punitive
    transaction costs and ensure that the resulting Sharpe is not
    unrealistically high.
    """
    dates = pd.date_range("2020-01-01", periods=200, freq="B")
    rows = []
    price = 100.0
    rng = np.random.default_rng(0)
    for d in dates:
        ret = 0.0005 + rng.normal(0, 0.01)
        price *= 1 + ret
        rows.append(
            {
                "date": d.date(),
                "ticker": "ILLQ",
                "open": price,
                "high": price * 1.01,
                "low": price * 0.99,
                "close": price,
                "volume": 50_000,
            }
        )
    df = pd.DataFrame(rows)

    tc_config = TCCMConfig(
        commission_per_share=0.01,
        calibration_constant=0.05,
        impact_alpha=0.9,
        adv_window=20,
    )
    bt_config = BacktestConfig(tc_config=tc_config)

    candidate_weights = [
        {
            "RS_score": 0.2,
            "Trend_score": 0.2,
            "Squeeze_score": 0.2,
            "Momentum_score": 0.2,
            "Volume_score": 0.2,
        }
    ]

    _w, sharpe = calibrate_phase1(df, candidate_weights, bt_config)

    # With very high costs and low liquidity, Sharpe should be modest
    assert sharpe < 1.0


