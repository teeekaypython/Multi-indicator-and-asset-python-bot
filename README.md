# Multi-indicator-and-asset-python-bot
This repository contains a fully functional MetaTrader 5 trading bot built with Python. The bot uses technical indicators from the TA-Lib library to scan multiple assets, evaluate trading signals, and place trades automatically based on signal strength.
✅ Connects to MT5 and fetches historical price data in real time.

📊 Technical Indicators:

Oscillators: RSI, Stochastic, MACD, CCI, ADX, Awesome Oscillator, Momentum, Williams %R, Ultimate Oscillator, etc.

Moving Averages: SMA, EMA, and Ichimoku base line.

🤖 Signal Classification:

Classifies signals as Buy, Sell, or Neutral.

Combines oscillator and moving average votes to determine trade direction.

📉 Trade Execution:

Calculates Stop Loss and Take Profit based on the ATR (Average True Range).

Avoids duplicate trades by checking for open positions.

⏱️ Runs in a continuous loop, analyzing and trading on every new candle (M15 timeframe).

📦 Built with MetaTrader5, pandas, pytz, and TA-Lib.
