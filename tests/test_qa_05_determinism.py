import pandas as pd

from alpha_scanner.calibrator import BacktestConfig, calibrate_phase1


def test_qa05_determinism():
    """
    QA-05: Determinism Test

    Running the Calibrator with the same data and candidate weights
    twice should produce identical outputs (no randomness).
    """
    dates = pd.date_range("2020-01-01", periods=50, freq="B")
    rows = []
    for t in ["AAA", "BBB"]:
        price = 100.0
        for d in dates:
            price *= 1.001
            rows.append(
                {
                    "date": d.date(),
                    "ticker": t,
                    "open": price,
                    "high": price * 1.01,
                    "low": price * 0.99,
                    "close": price,
                    "volume": 1_000_000,
                }
            )
    df = pd.DataFrame(rows)

    candidate_weights = [
        {
            "RS_score": 0.2,
            "Trend_score": 0.2,
            "Squeeze_score": 0.2,
            "Momentum_score": 0.2,
            "Volume_score": 0.2,
        }
    ]

    cfg = BacktestConfig()
    w1, s1 = calibrate_phase1(df, candidate_weights, cfg)
    w2, s2 = calibrate_phase1(df, candidate_weights, cfg)

    assert w1 == w2
    assert s1 == s2


