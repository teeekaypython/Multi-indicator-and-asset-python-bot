import MetaTrader5 as mt5
import pandas as pd
import pytz
import talib
from datetime import datetime


# Initialize MT5
def initialize_mt5():
    if not mt5.initialize():
        print("Failed to initialize MetaTrader 5")
        return False
    return True


# Fetch data from MT5
def fetch_mt5_data(asset):
    timeframe = mt5.TIMEFRAME_M15
    utc_from = datetime(2025, 12, 4, tzinfo=pytz.utc)
    rates = mt5.copy_rates_from(asset, timeframe, utc_from, 10000)

    if rates is None or len(rates) == 0:
        print(f"Failed to retrieve data for {asset}")
        return None

    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df


# Calculate oscillators
def oscillators(data):
    close = data['close']
    high = data['high']
    low = data['low']

    def safe_last(series, default_value=None):
        if len(series) == 0 or pd.isna(series).all():
            return default_value
        return series.dropna().iloc[-1]

    indicators = {
        "Relative Strength Index (14)": safe_last(talib.RSI(close, timeperiod=14), default_value=float('nan')),
        "Stochastic %K (14, 3, 3)": safe_last(talib.STOCH(
            high, low, close,
            fastk_period=14,
            slowk_period=3,
            slowk_matype=0,
            slowd_period=3,
            slowd_matype=0)[0], default_value=float('nan')),
        "Commodity Channel Index (20)": safe_last(talib.CCI(high, low, close, timeperiod=20), default_value=float('nan')),
        "Average Directional Index (14)": safe_last(talib.ADX(high, low, close, timeperiod=14), default_value=float('nan')),
        "Awesome Oscillator": safe_last((high + low) / 2 - talib.MA((high + low) / 2, timeperiod=34), default_value=float('nan')),
        "Momentum (10)": safe_last(talib.MOM(close, timeperiod=10), default_value=float('nan')),
        "MACD Level (12, 26)": safe_last(talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)[0], default_value=float('nan')),
        "Stochastic RSI Fast (3, 3, 14, 14)": safe_last(talib.STOCHRSI(
            close, timeperiod=14,
            fastk_period=3,
            fastd_period=3,
            fastd_matype=0)[0], default_value=float('nan')),
        "Williams Percent Range (14)": safe_last(talib.WILLR(high, low, close, timeperiod=14), default_value=float('nan')),
        "Bull Bear Power": safe_last(close - talib.EMA(close, timeperiod=13), default_value=float('nan')),
        "Ultimate Oscillator (7, 14, 28)": safe_last(talib.ULTOSC(
            high, low, close,
            timeperiod1=7,
            timeperiod2=14,
            timeperiod3=28), default_value=float('nan'))
    }

    # Classification of oscillator signals (Overbought/Oversold)
    classification = {}
    for name, value in indicators.items():
        if pd.notna(value):
            if name in ["Relative Strength Index (14)", "Stochastic %K (14, 3, 3)", "Commodity Channel Index (20)"]:
                if value < 30:
                    classification[name] = "Buy (Oversold)"
                elif value > 70:
                    classification[name] = "Sell (Overbought)"
                else:
                    classification[name] = "Neutral"
            elif name in ["Awesome Oscillator", "Momentum (10)", "MACD Level (12, 26)"]:
                if value > 0:
                    classification[name] = "Buy"
                elif value < 0:
                    classification[name] = "Sell"
                else:
                    classification[name] = "Neutral"
            else:
                classification[name] = "Neutral"
        else:
            classification[name] = "Not enough data to calculate."

    return classification


# Moving averages
def moving_averages(data):
    close = data['close']
    close = data['close']
    high = data['high']
    low = data['low']
    if len(close) < 200:
        print("Not enough data points to calculate all moving averages.")
        return {}
    ichimoku_base_line = (high.rolling(window=9).max() + low.rolling(window=9).min()) / 2

    indicators = {
            "Exponential Moving Average (10)": talib.EMA(close, timeperiod=10).iloc[-1],
            "Simple Moving Average (10)": talib.SMA(close, timeperiod=10).iloc[-1],
            "Exponential Moving Average (20)": talib.EMA(close, timeperiod=20).iloc[-1],
            "Simple Moving Average (20)": talib.SMA(close, timeperiod=20).iloc[-1],
            "Exponential Moving Average (30)": talib.EMA(close, timeperiod=30).iloc[-1],
            "Simple Moving Average (30)": talib.SMA(close, timeperiod=30).iloc[-1],
            "Exponential Moving Average (50)": talib.EMA(close, timeperiod=50).iloc[-1],
            "Simple Moving Average (50)": talib.SMA(close, timeperiod=50).iloc[-1],
            "Exponential Moving Average (100)": talib.EMA(close, timeperiod=100).iloc[-1],
            "Simple Moving Average (100)": talib.SMA(close, timeperiod=100).iloc[-1],
            "Exponential Moving Average (200)": talib.EMA(close, timeperiod=200).iloc[-1],
            "Simple Moving Average (200)": talib.SMA(close, timeperiod=200).iloc[-1],
            "Ichimoku Base Line (9, 26, 52, 26)": ichimoku_base_line.iloc[-1]
        }

    # Check if the indicators contain valid values
    indicators = {k: v for k, v in indicators.items() if v is not None}
    if not indicators:
        print(f"No valid moving averages calculated.")
        return None

    # Classification of price in relation to moving averages
    price = close.iloc[-1]
    ma_classification = {}
    for name, value in indicators.items():
        if price > value:
            ma_classification[name] = "Buy"
        elif price < value:
            ma_classification[name] = "Sell"
        else:
            ma_classification[name] = "Neutral"

    return ma_classification

# Combine indicators
def logic(data):
    ma_classification = moving_averages(data)
    oscillator_classification = oscillators(data)

    classification_counts = {"Buy": 0, "Sell": 0, "Neutral": 0}
    for signal in ma_classification.values():
        classification_counts[signal.split()[0]] += 1
    for signal in oscillator_classification.values():
        classification_counts[signal.split()[0]] += 1

    return classification_counts


# Place a trade
# Place a trade
def place_trade(asset, classification_counts, data):
    # Check if there's already an open position for the asset
    positions = mt5.positions_get(symbol=asset)
    if positions is not None and len(positions) > 0:
        print(f"An open trade already exists for {asset}. Skipping trade placement.")
        return  # Skip opening a new trade if there's already an open position

    # Proceed with trade logic if no open position exists
    atr = talib.ATR(data['high'], data['low'], data['close'], timeperiod=14).iloc[-1]

    if atr is None or pd.isna(atr):
        print("ATR value could not be calculated.")
        return

    price = mt5.symbol_info_tick(asset).ask
    deviation = 10  # Maximum deviation in points

    sl = atr
    tp = 2 * atr

    if classification_counts["Buy"] > (classification_counts["Sell"] + classification_counts["Neutral"]):
        trade_type = mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(asset).ask
        sl_price = price - sl
        tp_price = price + tp
    elif classification_counts["Sell"] > (classification_counts["Buy"] + classification_counts["Neutral"]):
        trade_type = mt5.ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(asset).bid
        sl_price = price + sl
        tp_price = price - tp
    else:
        print("No clear trade signal.")
        return

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": asset,
        "volume": 0.1,
        "type": trade_type,
        "price": price,
        "sl": sl_price,
        "tp": tp_price,
        "deviation": deviation,
        "magic": 123456,
        "comment": "Trade based on logic",
    }

    result = mt5.order_send(request)
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        print(f"Trade successful: {result}")
    else:
        print(f"Trade failed: {result}")


# Main script
import time  # Add this import for the time module

def main():
    assets = ["Volatility 100 Index", "GBPUSD", "USDJPY", "XAUUSD"]  # Add the symbols you want to trade
    if not initialize_mt5():
        return

    while True:  # This will run the code in an infinite loop
        for asset in assets:
            print(f"Processing {asset}...")
            data = fetch_mt5_data(asset)
            if data is None:
                print(f"Skipping {asset} due to data issues.")
                continue

            classification_counts = logic(data)
            print(f"{asset} Classification counts:", classification_counts)

            place_trade(asset, classification_counts, data)

        print("Waiting for the next minute...")
        time.sleep(60)  # Wait for 1 minute before running the loop again

    mt5.shutdown()



if __name__ == "__main__":
    main()
