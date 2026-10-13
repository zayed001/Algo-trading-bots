"""
Simple Moving Average (SMA) Crossover Trading Bot for MetaTrader 5 (MT5)

Strategy Logic:
- Calculates a Fast SMA and a Slow SMA on closed candles.
- Golden Cross (Fast crosses above Slow): Send BUY order.
- Death Cross (Fast crosses below Slow): Send SELL order.
- Manages single open position per symbol with configurable Stop-Loss and Take-Profit.
"""

import time
import logging
from typing import Optional, Dict, Any
import pandas as pd
import MetaTrader5 as mt5

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("SMABot")

# --- Bot Configuration Parameters ---
CONFIG = {
    "symbol": "EURUSD",
    "timeframe": mt5.TIMEFRAME_M15,     # 15-Minute candles
    "fast_period": 10,                 # Fast Moving Average period
    "slow_period": 30,                 # Slow Moving Average period
    "lot_size": 0.01,                  # Trade volume
    "stop_loss_pips": 25,              # SL in pips
    "take_profit_pips": 50,            # TP in pips
    "slippage": 10,                    # Max slippage in points
    "magic_number": 101001,            # Unique identifier for bot's trades
    "poll_interval_sec": 15,           # Check interval between loops
}


def initialize_mt5() -> bool:
    """Initialize connection to the MetaTrader 5 terminal."""
    if not mt5.initialize():
        logger.error("MetaTrader 5 initialization failed. Error code: %s", mt5.last_error())
        return False
    
    account_info = mt5.account_info()
    if account_info is None:
        logger.error("Failed to retrieve account info. Ensure MT5 is logged into an account.")
        return False

    logger.info("Connected to MT5 successfully!")
    logger.info(
        "Account: %d | Server: %s | Balance: %.2f %s | Leverage: 1:%d",
        account_info.login,
        account_info.server,
        account_info.balance,
        account_info.currency,
        account_info.leverage,
    )
    return True


def ensure_symbol_ready(symbol: str) -> Optional[Dict[str, Any]]:
    """Ensure the symbol is selected and available in Market Watch."""
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        logger.error("Symbol '%s' not found on broker.", symbol)
        return None

    if not symbol_info.visible:
        if not mt5.symbol_select(symbol, True):
            logger.error("Failed to select symbol '%s' into Market Watch.", symbol)
            return None
        symbol_info = mt5.symbol_info(symbol)

    return symbol_info._asdict()


def get_market_data(symbol: str, timeframe: int, count: int) -> Optional[pd.DataFrame]:
    """Fetch historical candle rates and compute Moving Averages."""
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    if rates is None or len(rates) == 0:
        logger.warning("No candle data returned for symbol: %s", symbol)
        return None

    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df.set_index("time", inplace=True)
    return df


def calculate_signals(df: pd.DataFrame, fast_period: int, slow_period: int) -> pd.DataFrame:
    """Calculate SMA indicators and identify crossover signals."""
    df["fast_sma"] = df["close"].rolling(window=fast_period).mean()
    df["slow_sma"] = df["close"].rolling(window=slow_period).mean()

    # Determine crossover condition on the last completed candle (index -2)
    # Candle -1 is the current forming candle; candle -2 is closed.
    prev_fast = df["fast_sma"].iloc[-3]
    prev_slow = df["slow_sma"].iloc[-3]
    curr_fast = df["fast_sma"].iloc[-2]
    curr_slow = df["slow_sma"].iloc[-2]

    signal = None
    if prev_fast <= prev_slow and curr_fast > curr_slow:
        signal = "BUY"
    elif prev_fast >= prev_slow and curr_fast < curr_slow:
        signal = "SELL"

    return signal, curr_fast, curr_slow


def get_open_positions(symbol: str, magic_number: int):
    """Retrieve existing open positions managed by this bot."""
    positions = mt5.positions_get(symbol=symbol)
    if positions is None:
        return []
    return [pos for pos in positions if pos.magic == magic_number]


def execute_order(symbol: str, order_type: str, lot: float, sl_pips: float, tp_pips: float, magic: int, slippage: int):
    """Send a trade request to MetaTrader 5."""
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        return False

    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        logger.error("Failed to get current tick for %s", symbol)
        return False

    point = symbol_info.point
    # Standard pip calculation (for 5-digit / 3-digit brokers, 1 pip = 10 points)
    pip_factor = 10 if symbol_info.digits in (3, 5) else 1
    pip_size = point * pip_factor

    if order_type == "BUY":
        action_type = mt5.ORDER_TYPE_BUY
        price = tick.ask
        sl = price - (sl_pips * pip_size) if sl_pips > 0 else 0.0
        tp = price + (tp_pips * pip_size) if tp_pips > 0 else 0.0
    elif order_type == "SELL":
        action_type = mt5.ORDER_TYPE_SELL
        price = tick.bid
        sl = price + (sl_pips * pip_size) if sl_pips > 0 else 0.0
        tp = price - (tp_pips * pip_size) if tp_pips > 0 else 0.0
    else:
        logger.error("Unknown order type: %s", order_type)
        return False

    # Choose valid filling mode supported by the symbol
    filling_mode = mt5.ORDER_FILLING_IOC
    if symbol_info.filling_mode & mt5.SYMBOL_FILLING_IOC:
        filling_mode = mt5.ORDER_FILLING_IOC
    elif symbol_info.filling_mode & mt5.SYMBOL_FILLING_FOK:
        filling_mode = mt5.ORDER_FILLING_FOK
    else:
        filling_mode = mt5.ORDER_FILLING_RETURN

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": float(lot),
        "type": action_type,
        "price": float(price),
        "sl": float(round(sl, symbol_info.digits)),
        "tp": float(round(tp, symbol_info.digits)),
        "deviation": int(slippage),
        "magic": int(magic),
        "comment": "SMA Crossover Bot",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": filling_mode,
    }

    logger.info("Sending %s order for %.2f lots of %s @ %.5f (SL: %.5f, TP: %.5f)", order_type, lot, symbol, price, sl, tp)
    result = mt5.order_send(request)

    if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
        retcode = result.retcode if result else "None"
        comment = result.comment if result else mt5.last_error()
        logger.error("Order failed! Retcode: %s, Message: %s", retcode, comment)
        return False

    logger.info("Order executed successfully! Deal ticket: %d", result.order)
    return True


def run_strategy():
    """Main strategy execution loop."""
    if not initialize_mt5():
        return

    symbol = CONFIG["symbol"]
    if not ensure_symbol_ready(symbol):
        mt5.shutdown()
        return

    logger.info(
        "Strategy started on %s | Fast SMA: %d | Slow SMA: %d | Polling every %ds",
        symbol,
        CONFIG["fast_period"],
        CONFIG["slow_period"],
        CONFIG["poll_interval_sec"],
    )

    history_needed = CONFIG["slow_period"] + 20

    try:
        while True:
            df = get_market_data(symbol, CONFIG["timeframe"], history_needed)
            if df is not None and len(df) >= CONFIG["slow_period"]:
                signal, fast_val, slow_val = calculate_signals(
                    df, CONFIG["fast_period"], CONFIG["slow_period"]
                )

                open_positions = get_open_positions(symbol, CONFIG["magic_number"])

                logger.info(
                    "Latest Closed Candle: Fast SMA=%.5f | Slow SMA=%.5f | Signal=%s | Open Positions=%d",
                    fast_val,
                    slow_val,
                    signal or "HOLD",
                    len(open_positions),
                )

                if signal and len(open_positions) == 0:
                    logger.info("Signal detected: %s. Executing trade...", signal)
                    execute_order(
                        symbol=symbol,
                        order_type=signal,
                        lot=CONFIG["lot_size"],
                        sl_pips=CONFIG["stop_loss_pips"],
                        tp_pips=CONFIG["take_profit_pips"],
                        magic=CONFIG["magic_number"],
                        slippage=CONFIG["slippage"],
                    )

            time.sleep(CONFIG["poll_interval_sec"])

    except KeyboardInterrupt:
        logger.info("Manual stop signal received. Shutting down bot...")
    finally:
        mt5.shutdown()
        logger.info("MT5 connection closed.")


if __name__ == "__main__":
    run_strategy()
