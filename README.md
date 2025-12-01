# The Alpha Scanner

An institutional-grade, autonomous trading system designed to generate statistically proven "alpha" (trading edge) that survives market friction.

## Overview

The Alpha Scanner analyzes S&P 500 and Nasdaq-100 stocks using multiple technical indicators, rigorous statistical validation, and real-world cost modeling to identify top trading candidates.

**Core Principles:**
- Statistical Significance: Bootstrap testing (P-value < 0.05)
- Real Cost Measurement: Transaction Cost & Capacity Model (TCCM)
- Risk Management: Volatility targeting and kill-switch mechanisms
- Data Integrity: Schema validation, checksums, survivorship bias handling

## Features

### Technical Indicators (Alpha Factors)
- **RS (Relative Strength)**: Multi-period performance vs SPY and sector
- **Trend**: SMA 50/200 Golden/Death Cross, slopes, price positioning
- **Squeeze**: Bollinger/Keltner compression, volatility ratios, ADX
- **Momentum**: Rate of Change across multiple timeframes
- **Volume**: Volume momentum, divergence detection

### System Components
- **Factor Engine**: Rank normalization and factor aggregation
- **Phase 1 Calibrator**: Rapid weight optimization for PoC (2-10 min)
- **Phase 2 Calibrator**: Full Dirichlet sampling + Bootstrap validation (1-4 hrs)
- **TCCM**: Market impact cost and capacity modeling
- **Risk Management**: Dynamic kill-switch for regime detection
- **LLM Module**: Extensible interface for fundamentals and sentiment (future)

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# or: source .venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
```

## Usage

### Run Tests
```bash
# Unit tests only (no network required)
pytest

# Include integration tests (requires working yfinance/network)
pytest -m integration
```

### Example PoC Run
```bash
python -m alpha_scanner.example_poc_runner
```

## Project Structure

```
alpha_scanner/
├── factors/          # Individual alpha factor modules
│   ├── rs.py
│   ├── trend.py
│   ├── squeeze.py
│   ├── momentum.py
│   └── volume.py
├── factor_engine.py  # Factor aggregation and normalization
├── calibrator.py     # Weight optimization (Phase 1 & 2)
├── tccm.py          # Transaction cost and capacity model
├── risk.py          # Kill-switch and risk management
├── data_snapshot.py # Data governance and schema validation
├── reporter.py      # Excel output generation
└── llm_module.py    # LLM interface (stub)

tests/
├── test_qa_01_cost_model_fidelity.py
├── test_qa_02_kill_switch.py
├── test_qa_03_survivorship_bias.py
├── test_qa_04_liquidity_shock.py
├── test_qa_05_determinism.py
├── test_qa_06_schema_change.py
└── test_integration_yfinance.py
```

## Documentation

- [English Plan](The_Stocker_Plan_EN.md): Full technical specification
- [Hebrew Plan](The_Stocker_Plan_Heb.md): תכנון מלא בעברית

## Current Status

✅ **Implemented & Tested:**
- All 5 alpha factors with sub-components
- Factor engine with rank normalization
- Phase 1 Calibrator (PoC)
- TCCM (cost and capacity model)
- Risk management / kill-switch
- Data snapshot and schema validation
- QA test suite (6/6 passing)
- Excel reporter

⏳ **Pending:**
- Network/SSL configuration for yfinance data download
- Phase 2 Calibrator (Dirichlet + Bootstrap)
- LLM integration for fundamentals/sentiment
- Universe loader from config

## License

[Specify your license here]
