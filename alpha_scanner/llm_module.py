"""
LLM-based Fundamentals & Sentiment Module (interface only).

This module defines the interface expected by the rest of the system.
The actual connection to a specific LLM provider and data sources is
left to the integrator.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Dict, Iterable

import pandas as pd


@dataclass
class LLMModuleConfig:
    """
    Configuration placeholder for the LLM module.

    In a real deployment this would include:
    - API keys / endpoints.
    - Model names.
    - Prompt templates.
    - Cache locations.
    """

    enabled: bool = False


class LLMAlphaModule:
    """
    Thin interface around an external LLM used to derive
    fundamentals and sentiment scores.
    """

    def __init__(self, config: LLMModuleConfig | None = None) -> None:
        self.config = config or LLMModuleConfig()

    def get_fundamental_scores(
        self,
        ticker: str,
        as_of_date: date,
    ) -> Dict[str, float]:
        """
        Return fundamental overlay scores for a single ticker.

        This is a stub implementation that returns neutral scores.
        """
        return {
            "fund_quality_score": 0.0,
            "fund_valuation_score": 0.0,
            "fund_risk_score": 0.0,
        }

    def get_sentiment_scores(
        self,
        ticker: str,
        as_of_date: date,
    ) -> Dict[str, float]:
        """
        Return sentiment/news scores for a single ticker.

        This is a stub implementation that returns neutral scores.
        """
        return {
            "news_sentiment_short_term": 0.0,
            "news_sentiment_medium_term": 0.0,
            "controversy_score": 0.0,
        }

    def get_fundamental_scores_batch(
        self,
        tickers: Iterable[str],
        as_of_date: date,
    ) -> pd.DataFrame:
        """
        Batch version returning a DataFrame indexed by ticker.
        """
        rows = []
        for t in tickers:
            row = self.get_fundamental_scores(t, as_of_date)
            row["ticker"] = t
            rows.append(row)
        if not rows:
            return pd.DataFrame(
                columns=[
                    "ticker",
                    "fund_quality_score",
                    "fund_valuation_score",
                    "fund_risk_score",
                ]
            ).set_index("ticker")
        df = pd.DataFrame(rows).set_index("ticker")
        return df

    def get_sentiment_scores_batch(
        self,
        tickers: Iterable[str],
        as_of_date: date,
    ) -> pd.DataFrame:
        """
        Batch version returning a DataFrame indexed by ticker.
        """
        rows = []
        for t in tickers:
            row = self.get_sentiment_scores(t, as_of_date)
            row["ticker"] = t
            rows.append(row)
        if not rows:
            return pd.DataFrame(
                columns=[
                    "ticker",
                    "news_sentiment_short_term",
                    "news_sentiment_medium_term",
                    "controversy_score",
                ]
            ).set_index("ticker")
        df = pd.DataFrame(rows).set_index("ticker")
        return df


