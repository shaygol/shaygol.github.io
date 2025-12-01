import pandas as pd

from alpha_scanner.factor_engine import compute_factor_matrix


def test_qa03_survivorship_injection():
    """
    QA-03: Survivorship Injection

    Inject tickers that mimic delisted names and ensure the factor
    engine preserves them in the factor matrix (no positive bias from
    silently dropping them).
    """
    dates = pd.date_range("2020-01-01", periods=10, freq="B")
    rows = []
    for t in ["ALIVE", "DEL_1", "DEL_2"]:
        for d in dates:
            rows.append(
                {
                    "date": d.date(),
                    "ticker": t,
                    "open": 100.0,
                    "high": 101.0,
                    "low": 99.0,
                    "close": 100.0,
                    "volume": 1_000_000,
                }
            )
    df = pd.DataFrame(rows)

    factors = compute_factor_matrix(df)

    assert set(factors.index.get_level_values("ticker")) == {"ALIVE", "DEL_1", "DEL_2"}


