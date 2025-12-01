import datetime as dt

import pandas as pd
import pytest
import yfinance as yf

from alpha_scanner.factor_engine import compute_factor_matrix


@pytest.mark.integration
def test_yfinance_connectivity_and_basic_schema():
    """
    Integration: verify that yfinance can download data and returns
    a non-empty DataFrame with expected OHLCV columns.
    """
    end = dt.date.today()
    start = end - dt.timedelta(days=10)

    df = yf.download("SPY", start=start, end=end, interval="1d", auto_adjust=False)

    # Basic connectivity / non-empty. In restricted/SSL-intercepted
    # environments yfinance may return an empty frame; in that case
    # treat this test as skipped rather than hard-failing.
    assert isinstance(df, pd.DataFrame)
    if df.empty:
        pytest.skip("yfinance returned empty DataFrame (likely SSL or network issue)")

    # Expected columns (case-sensitive as in yfinance)
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        assert col in df.columns


@pytest.mark.integration
def test_factor_engine_with_yfinance_data():
    """
    Integration: pull real data via yfinance, transform it into the
    internal OHLCV format, and ensure the factor engine returns a
    reasonable factor matrix for multiple tickers.
    """
    tickers = ["AAPL", "MSFT"]
    end = dt.date.today()
    start = end - dt.timedelta(days=60)

    data = yf.download(tickers, start=start, end=end, interval="1d", auto_adjust=False)

    # If data is empty (e.g. due to network issues), mark as skip.
    if data.empty:
        pytest.skip("yfinance returned empty data (possible network or API issue)")

    # yfinance multi-ticker format: columns are a MultiIndex (field, ticker)
    rows = []
    for date, row in data.iterrows():
        for t in tickers:
            try:
                open_ = row[("Open", t)]
                high = row[("High", t)]
                low = row[("Low", t)]
                close = row[("Close", t)]
                volume = row[("Volume", t)]
            except KeyError:
                continue

            if pd.isna(close) or pd.isna(volume):
                continue

            rows.append(
                {
                    "date": date.date(),
                    "ticker": t,
                    "open": float(open_),
                    "high": float(high),
                    "low": float(low),
                    "close": float(close),
                    "volume": float(volume),
                }
            )

    if not rows:
        pytest.skip("No valid OHLCV rows constructed from yfinance data.")

    df_ohlcv = pd.DataFrame(rows)

    factors = compute_factor_matrix(df_ohlcv)

    # Sanity checks on factor matrix
    assert not factors.empty
    idx_tickers = set(factors.index.get_level_values("ticker"))
    for t in tickers:
        assert t in idx_tickers


