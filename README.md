# Algo-Trading-Bots: SMA Crossover Bot

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-MetaTrader%205-0078D7.svg)](https://www.metatrader5.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An automated algorithmic trading bot designed for Forex markets using **Python** and the **MetaTrader 5 (MT5)** terminal API. It implements a quantitative **Simple Moving Average (SMA) Crossover** strategy with integrated risk management and position control.

---

## 📈 Strategy Overview

The Simple Moving Average (SMA) crossover is a classic trend-following strategy:

* **Golden Cross (Bullish Signal):**
  When the **Fast SMA** crosses **above** the **Slow SMA** on the latest closed candle, the bot triggers a **BUY** order.
* **Death Cross (Bearish Signal):**
  When the **Fast SMA** crosses **below** the **Slow SMA** on the latest closed candle, the bot triggers a **SELL** order.
* **Closed-Candle Execution:**
  Calculations evaluate closed candles (Index `-2` and `-3`) rather than the active forming candle to avoid false whipsaws or repainting.
* **Position Protection:**
  Ensures that only **one active position per symbol** is managed at a time under the configured `magic_number`. Every trade is guarded with predefined **Stop-Loss (SL)** and **Take-Profit (TP)** in pips.

---

## ⚙️ Configuration Parameters

All key parameters are easily configurable at the top of [`sma_crossover_bot.py`](sma_crossover_bot.py):

| Parameter | Default | Description |
| :--- | :--- | :--- |
| `symbol` | `"EURUSD"` | Target currency pair or trading asset |
| `timeframe` | `TIMEFRAME_M15` | Bar timeframe (`M1`, `M5`, `M15`, `H1`, etc.) |
| `fast_period` | `10` | Period for the fast moving average |
| `slow_period` | `30` | Period for the slow moving average |
| `lot_size` | `0.01` | Fixed order volume (micro lot) |
| `stop_loss_pips` | `25` | Distance from entry to Stop-Loss in pips |
| `take_profit_pips` | `50` | Distance from entry to Take-Profit in pips |
| `slippage` | `10` | Maximum acceptable slippage in points |
| `magic_number` | `101001` | Unique trade identifier for MT5 position tracking |
| `poll_interval_sec` | `15` | Loop pause between market checks |

---

## 🚀 Getting Started

### Prerequisites

1. **MetaTrader 5 Desktop Terminal:**
   - Install and log into your broker demo or live account.
   - In MT5, enable automated trading:
     `Tools` → `Options` → `Expert Advisors` → Check **"Allow Algo Trading"**.
2. **Python 3.10+** (or Conda environment).

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/zayed001/Algo-trading-bots.git
   cd Algo-trading-bots
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the bot:**
   ```bash
   python sma_crossover_bot.py
   ```

---

## 🛡️ Risk Management & Disclaimer

> [!WARNING]
> **Trading Foreign Exchange (Forex) and CFDs on margin carries a high level of risk and may not be suitable for all investors.**
> This repository is provided for educational, research, and testing purposes only. Always test thoroughly on a **Demo Account** before considering live market deployment. Past performance of any algorithm does not guarantee future results.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
