import pandas as pd

from alpha_scanner.tccm import TCCMConfig, compute_capacity_usage


def test_qa04_liquidity_shock():
    """
    QA-04: Liquidity Shock

    Simulate a scenario where trading volume drops sharply and ensure
    capacity usage increases (tighter capacity).
    """
    dates = pd.date_range("2020-01-01", periods=40, freq="B")

    rows = []
    for i, d in enumerate(dates):
        vol = 1_000_000 if i < 20 else 100_000  # 90% drop
        rows.append(
            {
                "date": d.date(),
                "ticker": "AAA",
                "close": 100.0,
                "volume": vol,
            }
        )

    df = pd.DataFrame(rows).set_index(["date", "ticker"])

    positions = pd.Series(1_000.0, index=df.index, name="position")

    cfg = TCCMConfig(adv_window=20)
    cap_usage = compute_capacity_usage(
        positions=positions,
        prices=df["close"],
        volume=df["volume"],
        config=cfg,
    ).unstack("ticker")["AAA"]

    before = cap_usage.iloc[25]
    after = cap_usage.iloc[-1]

    assert after > before


