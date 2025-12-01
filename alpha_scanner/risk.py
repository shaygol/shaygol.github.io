"""
Risk & regime utilities, including the Kill Switch logic.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class KillSwitchConfig:
    """
    Configuration for the market-regime Kill Switch.
    """

    atr_multiplier: float = 2.0
    hist_vol_multiplier: float = 1.5


def should_activate_kill_switch(
    sector_drop_1w: float,
    atr: float,
    hist_vol_std: float,
    config: KillSwitchConfig | None = None,
) -> bool:
    """
    Implements the rule:

    Kill Switch is active if:
        Sector_Drop(1W) > max(atr_multiplier * ATR,
                              hist_vol_multiplier * HistVolStd)
    """
    if config is None:
        config = KillSwitchConfig()

    threshold = max(
        config.atr_multiplier * atr,
        config.hist_vol_multiplier * hist_vol_std,
    )
    return sector_drop_1w > threshold


