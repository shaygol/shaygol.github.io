from alpha_scanner.risk import KillSwitchConfig, should_activate_kill_switch


def test_qa02_synthetic_regime_flip():
    """
    QA-02: Synthetic Regime Flip

    Simulate a scenario where the sector index drops sharply and ensure
    the Kill Switch activates.
    """
    cfg = KillSwitchConfig()

    sector_drop = 0.05  # 5% drop
    atr = 0.01
    hist_vol = 0.015

    assert should_activate_kill_switch(sector_drop, atr, hist_vol, cfg)


