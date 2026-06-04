import os
import sys
import time
import sqlite3
from datetime import datetime, timedelta, time as dt_time
from zoneinfo import ZoneInfo

import pandas as pd
import requests
import yfinance as yf
from dotenv import load_dotenv


START_BALANCE=50000.0
MAX_OPEN_POSITIONS=10
POSITION_CASH=15000.0
SMALL_POSITION_CASH=8000.0
MEDIUM_POSITION_CASH=12000.0
TRUSTED_POSITION_CASH=15000.0
PROBATION_POSITION_CASH=4000.0
RECOVERY_TEST_POSITION_CASH=4000.0
LEARNING_SCOUT_POSITION_CASH=2500.0
BRAIN_EXPLORATION_POSITION_CASH=2500.0
OPPORTUNITY_RESCUE_POSITION_CASH=5000.0
ACTIVE_LEARNING_POSITION_CASH=3000.0
EUROPE_STOCK_POSITION_CASH=1500.0
EUROPE_STOCK_MIN_OPPORTUNITY=42
EUROPE_STOCK_MIN_RSI=48
EUROPE_STOCK_MAX_RSI=62
ASIA_STOCK_POSITION_CASH=1500.0
ASIA_STOCK_MIN_OPPORTUNITY=38
ASIA_STOCK_MIN_RSI=45
ASIA_STOCK_MAX_RSI=66
CRYPTO_EMA8_PULLBACK_SESSION_LOSS_LIMIT=2
DIRECT_ORDER_RISK_DOLLARS=100.0
DIRECT_ORDER_MIN_TRADE_MINUTES=10
STRONG_LIVE_MIN_SCORE=20
STRONG_LIVE_MIN_PROOF_COUNT=5
STRONG_LIVE_MAX_RISK_COUNT=4
STRONG_LIVE_MIN_OPPORTUNITY=30
OPPORTUNITY_RESCUE_MIN_SCORE=34
OPPORTUNITY_NORMAL_MIN_SCORE=38
ACTIVE_LEARNING_MIN_OPPORTUNITY=32
OPPORTUNITY_TOP_SCAN_LIMIT=40
LEARNING_SCOUT_AFTER_IDLE_MINUTES=3
LEARNING_SCOUT_COOLDOWN_MINUTES=3
ALTERNATE_SETUP_SCOUT_AFTER_IDLE_MINUTES=30
ALTERNATE_SETUP_SCOUT_COOLDOWN_MINUTES=35
ALTERNATE_SETUP_SCOUT_MIN_OPPORTUNITY=20
ALTERNATE_SETUP_SCOUT_MIN_RAW_SCORE=16
ALTERNATE_SETUP_SCOUT_MIN_ADJUSTED_SCORE=6
ALTERNATE_SETUP_SCOUT_POSITION_CASH=1500.0
MAX_MIXED_MARKET_SCOUT_POSITIONS=1
MIN_MIXED_MARKET_SCOUT_SCORE=24
MIN_KNOWLEDGE_A_SCORE=24
MIN_KNOWLEDGE_B_SCORE=16
MIN_SCORE_TO_TRADE=6
MIN_LONG_ADJUSTED_SCORE=6
MIN_SHORT_ADJUSTED_SCORE=10
FRESH_SETUP_SCORE_BOOST=2
BRAIN_TRAINING_HOURS=8
BRAIN_TRAINING_PERIOD="5d"
BRAIN_TRAINING_INTERVAL="1m"
BRAIN_MIN_PATTERN_TRADES=12
BRAIN_GOOD_WIN_RATE=55
BRAIN_BAD_WIN_RATE=42
BRAIN_HARD_WAIT_WIN_RATE=35
BRAIN_OVERRIDE_SCORE=28
BRAIN_HUNT_SCORE_BOOST=6
EMA8_PULLBACK_LONG_BOOST=3
WEAK_SHORT_EXTRA_MIN_SCORE=6
SESSION_SHORT_FAILURE_HARD_LIMIT=2
SESSION_BRAIN_DEFENSE_LOSS=-25.0
SESSION_BRAIN_HARD_STOP_LOSS=-75.0
SESSION_BRAIN_TICKER_DIRECTION_LOSS_LIMIT=2
SESSION_BRAIN_SETUP_DIRECTION_LOSS_LIMIT=3
SESSION_BRAIN_DEFENSE_MAX_CASH=1500.0
SESSION_BRAIN_DEFENSE_EXTRA_SCORE=5
SESSION_BRAIN_REPEAT_LOSS_EXTRA_SCORE=8
US_STOCK_LOSS_DEFENSE_CASH=1500.0
US_STOCK_MARKET_CONFIRM_CACHE_SECONDS=60
BRAIN_SYMBOL_LIMIT=28
MIN_PROBATION_LONG_SCORE=18
MIN_PROBATION_SHORT_SCORE=22
MIN_RECOVERY_RAW_LONG_SCORE=22
MIN_RECOVERY_RAW_SHORT_SCORE=24
MIN_TRUSTED_TICKER_RECOVERY_RAW_LONG_SCORE=18
MIN_TRUSTED_TICKER_RECOVERY_RAW_SHORT_SCORE=20
MAX_HOLD_MINUTES=20
STALE_POSITION_MINUTES=20
REFRESH_SECONDS=20
POSITION_CHECK_SECONDS=5
NEW_TRADE_SCAN_SECONDS=5
PENDING_CONFIRM_SECONDS=10
PENDING_MAX_AGE_SECONDS=90
TAKE_PROFIT_PCT=0.003
STOP_LOSS_PCT=0.0025
DIRECT_ORDER_POSITION_CASH=min(START_BALANCE*0.85,DIRECT_ORDER_RISK_DOLLARS/STOP_LOSS_PCT)
DAILY_LOSS_LIMIT=750.0
MIN_ENTRY_RSI=25
MAX_ENTRY_RSI=88
PROFIT_EXIT_MINUTES=5
PROFIT_EXIT_MIN_PCT=0.0015
PROFIT_LOCK_MINUTES=10
PROFIT_LOCK_MIN_PCT=0.0003
FLAT_EXIT_MINUTES=15
FLAT_EXIT_MAX_ABS_PCT=0.0005
FORCE_EXIT_MINUTES=20
EARLY_FAILURE_MINUTES=3
EARLY_FAILURE_MAX_LOSS_PCT=-0.0005
COOLDOWN_AFTER_LOSS_MINUTES=3
SAME_TRADE_COOLDOWN_MINUTES=4
PROBATION_COOLDOWN_MINUTES=10
TICKER_EARLY_FAILURE_COOLDOWN_MINUTES=10
SESSION_TICKER_EARLY_FAILURE_LIMIT=2
SESSION_EARLY_FAILURE_PAUSE_MINUTES=10
SESSION_EARLY_FAILURE_PAUSE_COUNT=3
SESSION_EARLY_FAILURE_LOOKBACK_MINUTES=30
SETUP_DIRECTION_EARLY_FAILURE_LIMIT=3
MAX_TRIGGER_AGE_SECONDS=90
SLIPPAGE_PCT=0.0004
BROKER_FEE_PCT=0.0002
BAD_SETUP_MIN_TRADES=6
BAD_SETUP_MAX_WIN_RATE=15
BAD_SETUP_MAX_AVG_PROFIT=-20.0
BAD_TICKER_MIN_TRADES=5
BAD_TICKER_MAX_WIN_RATE=35
BAD_TICKER_MAX_AVG_PROFIT=-8.0
BAD_TICKER_MAX_TOTAL_PROFIT=-50.0
BAD_COMBO_MIN_TRADES=3
BAD_COMBO_MAX_WIN_RATE=34
BAD_COMBO_MAX_AVG_PROFIT=-8.0
MAX_CRYPTO_POSITIONS=4
MAX_NEW_TRADES_PER_SCAN=4
CRYPTO_MARKET_WEAK_PENALTY=2
US_STOCK_MARKET_CONFIRM_CACHE={
    "time":None,
    "value":None
}

WATCHLISTS={
    "Stocks":[
        "AAPL","MSFT","NVDA","AMZN","META","TSLA","AMD",
        "GOOGL","NFLX","COIN","MSTR","PLTR","SMCI","AVGO",
        "QQQ","SPY","IWM"
    ],
    "Europe Stocks":[
        "ASML.AS","SAP.DE","SIE.DE","VOW3.DE","AIR.PA","MC.PA",
        "TTE.PA","OR.PA","AZN.L","SHEL.L","HSBA.L","BP.L",
        "NESN.SW","NOVN.SW"
    ],
    "Asia Stocks":[
        "7203.T","6758.T","9984.T","9983.T","8306.T","6861.T",
        "005930.KS","000660.KS","0700.HK","9988.HK","1211.HK",
        "1299.HK","2330.TW","2317.TW"
    ],
    "Crypto":[
        "BTC-USD","ETH-USD","SOL-USD","BNB-USD","XRP-USD","ADA-USD",
        "DOGE-USD","LINK-USD","AVAX-USD","LTC-USD","BCH-USD","DOT-USD",
        "UNI-USD","AAVE-USD","SUI-USD","NEAR-USD","ARB-USD","OP-USD",
        "INJ-USD","RENDER-USD","FET-USD"
    ],
    "Futures":["ES=F","NQ=F","GC=F"]
}

BRAIN_TRAINING_SYMBOLS=(
    WATCHLISTS["Crypto"][:18]+
    WATCHLISTS["Stocks"][:8]+
    WATCHLISTS["Futures"][:2]
)

USD_FACTOR_BY_SUFFIX={
    ".AS":1.09,
    ".DE":1.09,
    ".PA":1.09,
    ".SW":1.10,
    ".L":0.0127,
    ".T":0.0067,
    ".KS":0.00073,
    ".HK":0.128,
    ".TW":0.031,
}

load_dotenv()

TWELVE_DATA_API_KEY=os.getenv("TWELVE_DATA_API_KEY")


def connect_db():

    conn=sqlite3.connect(
        "users.db",
        timeout=60,
        check_same_thread=False
    )

    cursor=conn.cursor()
    cursor.execute("PRAGMA busy_timeout=60000")

    try:
        cursor.execute("PRAGMA journal_mode=WAL")
    except sqlite3.OperationalError:
        pass

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bot_state(
        email TEXT PRIMARY KEY,
        running INTEGER DEFAULT 0,
        pid INTEGER,
        status TEXT DEFAULT 'AI is stopped.',
        last_heartbeat TEXT,
        best_ticker TEXT,
        best_score REAL,
        open_positions_count INTEGER DEFAULT 0,
        today_profit REAL DEFAULT 0,
        searching_enabled INTEGER DEFAULT 1,
        session_start_time TEXT
    )
    """)

    cursor.execute("PRAGMA table_info(bot_state)")
    bot_state_cols=[c[1] for c in cursor.fetchall()]

    for col,col_type in [
        ("best_ticker","TEXT"),
        ("best_score","REAL"),
        ("open_positions_count","INTEGER DEFAULT 0"),
        ("today_profit","REAL DEFAULT 0"),
        ("searching_enabled","INTEGER DEFAULT 1"),
        ("session_start_time","TEXT")
    ]:

        if col not in bot_state_cols:
            cursor.execute(f"ALTER TABLE bot_state ADD COLUMN {col} {col_type}")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trades(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        time TEXT,
        ticker TEXT,
        entry REAL,
        exit REAL,
        profit REAL,
        entry_time TEXT,
        exit_time TEXT,
        reason TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS open_positions_v2(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        ticker TEXT,
        entry REAL,
        tp REAL,
        sl REAL,
        qty REAL,
        entry_time TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trade_decisions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        time TEXT,
        ticker TEXT,
        market TEXT,
        price REAL,
        score REAL,
        rsi REAL,
        adjusted_score REAL,
        decision TEXT,
        reason TEXT,
        memory_note TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS setup_memory(
        email TEXT,
        setup_type TEXT,
        trades INTEGER DEFAULT 0,
        wins INTEGER DEFAULT 0,
        total_profit REAL DEFAULT 0,
        avg_profit REAL DEFAULT 0,
        last_review TEXT,
        updated_at TEXT,
        PRIMARY KEY(email,setup_type)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ai_sessions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        start_time TEXT,
        end_time TEXT,
        profit REAL DEFAULT 0,
        trades INTEGER DEFAULT 0,
        status TEXT DEFAULT 'running'
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ai_lessons(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        created_at TEXT,
        source TEXT,
        lesson TEXT,
        active INTEGER DEFAULT 1
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pattern_brain(
        email TEXT,
        pattern_key TEXT,
        market TEXT,
        direction TEXT,
        setup_type TEXT,
        trades INTEGER DEFAULT 0,
        wins INTEGER DEFAULT 0,
        total_profit REAL DEFAULT 0,
        avg_profit REAL DEFAULT 0,
        win_rate REAL DEFAULT 0,
        last_trained TEXT,
        PRIMARY KEY(email,pattern_key)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS brain_training_runs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        started_at TEXT,
        finished_at TEXT,
        symbols INTEGER DEFAULT 0,
        samples INTEGER DEFAULT 0,
        status TEXT,
        note TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pending_setups(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        ticker TEXT,
        market TEXT,
        direction TEXT,
        setup_type TEXT,
        price REAL,
        score REAL,
        rsi REAL,
        reason TEXT,
        memory_note TEXT,
        trigger_time TEXT,
        trigger_high REAL,
        trigger_close REAL,
        created_at TEXT,
        UNIQUE(email,ticker,direction)
    )
    """)

    cursor.execute("PRAGMA table_info(trade_decisions)")
    decision_cols=[c[1] for c in cursor.fetchall()]

    for col,col_type in [
        ("adjusted_score","REAL"),
        ("memory_note","TEXT"),
        ("direction","TEXT DEFAULT 'LONG'"),
        ("trigger_time","TEXT"),
        ("trigger_high","REAL"),
        ("trigger_close","REAL"),
        ("setup_type","TEXT"),
        ("review_label","TEXT"),
        ("review_notes","TEXT"),
        ("hold_minutes","REAL"),
        ("move_pct","REAL")
    ]:

        if col not in decision_cols:
            cursor.execute(f"ALTER TABLE trade_decisions ADD COLUMN {col} {col_type}")

    cursor.execute("PRAGMA table_info(trades)")
    trade_cols=[c[1] for c in cursor.fetchall()]

    for col,col_type in [
        ("market","TEXT"),
        ("score","REAL"),
        ("rsi","REAL"),
        ("direction","TEXT DEFAULT 'LONG'"),
        ("entry_reason","TEXT"),
        ("trigger_time","TEXT"),
        ("trigger_high","REAL"),
        ("trigger_close","REAL"),
        ("setup_type","TEXT"),
        ("review_label","TEXT"),
        ("review_notes","TEXT"),
        ("hold_minutes","REAL"),
        ("move_pct","REAL")
    ]:

        if col not in trade_cols:
            cursor.execute(f"ALTER TABLE trades ADD COLUMN {col} {col_type}")

    cursor.execute("PRAGMA table_info(open_positions_v2)")
    position_cols=[c[1] for c in cursor.fetchall()]

    for col,col_type in [
        ("market","TEXT"),
        ("score","REAL"),
        ("rsi","REAL"),
        ("direction","TEXT DEFAULT 'LONG'"),
        ("entry_reason","TEXT"),
        ("trigger_time","TEXT"),
        ("trigger_high","REAL"),
        ("trigger_close","REAL")
    ]:

        if col not in position_cols:
            cursor.execute(f"ALTER TABLE open_positions_v2 ADD COLUMN {col} {col_type}")

    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_open_position_once
        ON open_positions_v2(email,ticker,direction)
    """)

    conn.commit()

    return conn,cursor


def clean_data(data):

    if isinstance(data.columns,pd.MultiIndex):
        data.columns=data.columns.get_level_values(0)

    return data


def calculate_rsi(close,period=14):

    delta=close.diff()
    gain=delta.where(delta>0,0).rolling(period).mean()
    loss=(-delta.where(delta<0,0)).rolling(period).mean()
    rs=gain/loss

    return 100-(100/(1+rs))


def chart_time_to_local_naive(value):

    if value is None:
        return None

    stamp=pd.Timestamp(value)

    if stamp.tzinfo is not None:
        stamp=stamp.tz_convert(ZoneInfo("Asia/Jerusalem")).tz_localize(None)

    return stamp.to_pydatetime()


def format_chart_time(value):

    local_time=chart_time_to_local_naive(value)

    if local_time is None:
        return None

    return local_time.strftime("%Y-%m-%d %H:%M:%S")


def twelvedata_latest_price(ticker):

    if not TWELVE_DATA_API_KEY:
        return None

    try:

        url=f"https://api.twelvedata.com/price?symbol={ticker}&apikey={TWELVE_DATA_API_KEY}"
        response=requests.get(url,timeout=10)
        data=response.json()

        if "price" in data:
            return round_market_price(float(data["price"]))

        return None

    except Exception:

        return None


def yfinance_latest_price(ticker):

    try:

        data=yf.download(
            ticker,
            period="1d",
            interval="1m",
            progress=False,
            auto_adjust=True
        )

        if data.empty:
            data=yf.download(
                ticker,
                period="5d",
                interval="1d",
                progress=False,
                auto_adjust=True
            )

        if data.empty:
            return None

        data=clean_data(data)

        return round_market_price(float(data["Close"].dropna().iloc[-1]))

    except Exception:

        return None


def latest_price(ticker):

    price=twelvedata_latest_price(ticker)

    if price:
        return price

    return yfinance_latest_price(ticker)


def price_decimals(price):

    price=abs(float(price))

    if price>=100:
        return 2
    if price>=1:
        return 4
    if price>=0.01:
        return 6

    return 8


def round_market_price(price):

    return round(
        float(price),
        price_decimals(price)
    )


def simulated_buy_fill(price):

    return round_market_price(
        price*(1+SLIPPAGE_PCT)
    )


def simulated_sell_fill(price):

    return round_market_price(
        price*(1-SLIPPAGE_PCT)
    )


def exit_fill_for_direction(direction,current):

    if direction=="SHORT":
        return simulated_buy_fill(current)

    return simulated_sell_fill(current)


def profit_for_direction(direction,entry,exit_price,qty,ticker=None):

    usd_factor=currency_to_usd_factor(
        ticker
    )

    if direction=="SHORT":
        gross=(entry-exit_price)*qty*usd_factor
    else:
        gross=(exit_price-entry)*qty*usd_factor

    return round(
        gross-estimated_fees(entry,exit_price,qty,ticker),
        2
    )


def ticker_suffix(ticker):

    ticker=ticker or ""

    for suffix in USD_FACTOR_BY_SUFFIX:
        if ticker.endswith(suffix):
            return suffix

    return ""


def currency_to_usd_factor(ticker):

    return USD_FACTOR_BY_SUFFIX.get(
        ticker_suffix(ticker),
        1.0
    )


def estimated_fees(entry,exit_price,qty,ticker=None):

    traded_value=((entry*qty)+(exit_price*qty))*currency_to_usd_factor(
        ticker
    )

    return traded_value*BROKER_FEE_PCT


def scan(symbols):

    results=[]

    for symbol in symbols:

        try:

            data=yf.download(
                symbol,
                period="1d",
                interval="1m",
                progress=False,
                auto_adjust=True
            )

            if data.empty:
                continue

            data=clean_data(data)

            close=data["Close"].squeeze()
            open_price=data["Open"].squeeze()
            high=data["High"].squeeze()
            low=data["Low"].squeeze()
            volume=data["Volume"].squeeze() if "Volume" in data.columns else None

            if len(close)<35:
                continue

            price=float(close.iloc[-1])
            ema3=close.rolling(3).mean()
            ema8=close.rolling(8).mean()
            ema21=close.rolling(21).mean()
            rsi=calculate_rsi(close).iloc[-1]

            score=0
            reasons=[]

            if price>float(ema3.iloc[-1]):
                score+=1
                reasons.append("above 1m EMA3")

            if price>float(ema8.iloc[-1]):
                score+=2
                reasons.append("above 1m EMA8")

            if price>float(ema21.iloc[-1]):
                score+=2
                reasons.append("above 1m EMA21")

            if float(ema3.iloc[-1])>float(ema8.iloc[-1])>float(ema21.iloc[-1]):
                score+=2
                reasons.append("1m EMA stack bullish")

            one_min_change=(close.iloc[-1]-close.iloc[-2])/close.iloc[-2]
            three_min_change=(close.iloc[-1]-close.iloc[-4])/close.iloc[-4]
            ten_min_change=(close.iloc[-1]-close.iloc[-11])/close.iloc[-11]
            signal_open=float(open_price.iloc[-2])
            signal_close=float(close.iloc[-2])
            signal_high=float(high.iloc[-2])
            previous_high=float(high.iloc[-3])
            signal_low=float(low.iloc[-2])
            signal_time=data.index[-2]
            signal_local_time=chart_time_to_local_naive(signal_time)
            trigger_age_seconds=(
                (datetime.now()-signal_local_time).total_seconds()
                if signal_local_time is not None
                else None
            )
            signal_range=max(signal_high-signal_low,price*0.0001)
            avg_range=(high-low).tail(20).mean()
            signal_close_position=(signal_close-signal_low)/signal_range
            trend_strength=(float(ema3.iloc[-1])-float(ema21.iloc[-1]))/price
            current_holds_trigger=price>=signal_close
            pullback_to_ema8=(
                float(low.tail(5).min())<=float(ema8.iloc[-1]) and
                price>float(ema3.iloc[-1])
            )
            above_vwap=True
            below_vwap=True

            if volume is not None:
                early_recent_volume_sum=volume.tail(60).sum()

                if early_recent_volume_sum>0:
                    early_typical_price=(high+low+close)/3
                    early_vwap=float(
                        (early_typical_price.tail(60)*volume.tail(60)).sum()/early_recent_volume_sum
                    )
                    above_vwap=price>early_vwap
                    below_vwap=price<early_vwap

            trigger_confirmed=(
                signal_close>signal_open and
                signal_close>previous_high and
                signal_range<=float(avg_range)*2.5
            )
            follow_through_confirmed=(
                price>signal_close and
                float(close.iloc[-1])>float(open_price.iloc[-1]) and
                one_min_change>0 and
                price>float(ema3.iloc[-1])
            )
            continuation_confirmed=(
                current_holds_trigger and
                price>float(ema3.iloc[-1])>float(ema8.iloc[-1]) and
                three_min_change>0 and
                follow_through_confirmed and
                above_vwap and
                ten_min_change<0.006 and
                signal_range<=float(avg_range)*2.5
            )

            if one_min_change>0:
                score+=1
                reasons.append("green 1m candle")

            if trigger_confirmed:
                score+=3
                reasons.append("1m bullish trigger candle")
            elif signal_range>float(avg_range)*2.5:
                score-=2
                reasons.append("trigger candle too large")

            if continuation_confirmed:
                score+=2
                reasons.append("strong 1m continuation")

            if signal_close_position>=0.65:
                score+=2
                reasons.append("trigger closed near high")

            if current_holds_trigger:
                score+=1
                reasons.append("price holding above trigger")

            if pullback_to_ema8:
                score+=2
                reasons.append("1m EMA8 pullback held")

            if trend_strength>0.0008:
                score+=1
                reasons.append("clean 1m trend strength")

            if three_min_change>0.001:
                score+=2
                reasons.append("3m momentum")

            if 0<ten_min_change<0.008:
                score+=1
                reasons.append("controlled 10m move")
            elif ten_min_change>=0.012:
                score-=2
                reasons.append("avoiding 1m spike chase")

            if 45<=rsi<=68:
                score+=2
                reasons.append("healthy 1m RSI")
            elif 68<rsi<=72:
                score+=1
                reasons.append("strong 1m RSI")

            recent_support=float(low.rolling(20).min().iloc[-2])
            recent_resistance=float(high.rolling(20).max().iloc[-2])
            support_distance=(price-recent_support)/price
            resistance_distance=(recent_resistance-price)/price

            if 0.0005<=support_distance<=0.006:
                score+=2
                reasons.append("near 1m support")

            if resistance_distance>0.001:
                score+=1
                reasons.append("room to 1m resistance")

            if volume is not None:
                avg_volume=volume.rolling(20).mean().iloc[-1]
                trigger_avg_volume=volume.rolling(20).mean().iloc[-2]
                recent_volume_sum=volume.tail(60).sum()

                if recent_volume_sum>0:

                    typical_price=(high+low+close)/3
                    vwap=float(
                        (typical_price.tail(60)*volume.tail(60)).sum()/recent_volume_sum
                    )

                    if price>vwap:
                        score+=2
                        reasons.append("above 1m VWAP")

                if avg_volume>0 and volume.iloc[-1]>avg_volume:
                    score+=1
                    reasons.append("1m volume above average")

                if trigger_avg_volume>0 and volume.iloc[-2]>trigger_avg_volume*1.3:
                    score+=2
                    reasons.append("trigger volume surge")

            recent_range=float(high.tail(10).max())-float(low.tail(10).min())
            volatility=max(recent_range,price*0.0015)

            results.append({
                "Ticker":symbol,
                "Price":round(price,2),
                "Score":score,
                "RSI":round(float(rsi),2),
                "Volatility":round(volatility,2),
                "Reason":", ".join(reasons) or "no 1m setup",
                "Direction":"LONG",
                "Trigger Confirmed":trigger_confirmed,
                "Continuation Confirmed":continuation_confirmed,
                "Follow Through Confirmed":follow_through_confirmed,
                "Trigger Time":format_chart_time(signal_time),
                "Trigger High":round(signal_high,2),
                "Trigger Close":round(signal_close,2),
                "Trigger Age Seconds":round(trigger_age_seconds,2) if trigger_age_seconds is not None else None
            })

            previous_low=float(low.iloc[-3])
            short_score=0
            short_reasons=[]

            if price<float(ema3.iloc[-1]):
                short_score+=1
                short_reasons.append("below 1m EMA3")

            if price<float(ema8.iloc[-1]):
                short_score+=2
                short_reasons.append("below 1m EMA8")

            if price<float(ema21.iloc[-1]):
                short_score+=2
                short_reasons.append("below 1m EMA21")

            if float(ema3.iloc[-1])<float(ema8.iloc[-1])<float(ema21.iloc[-1]):
                short_score+=2
                short_reasons.append("1m EMA stack bearish")

            short_current_holds_trigger=price<=signal_close
            short_trigger_confirmed=(
                signal_close<signal_open and
                signal_close<previous_low and
                signal_range<=float(avg_range)*2.5
            )
            short_follow_through_confirmed=(
                price<signal_close and
                float(close.iloc[-1])<float(open_price.iloc[-1]) and
                one_min_change<0 and
                price<float(ema3.iloc[-1])
            )
            short_continuation_confirmed=(
                short_current_holds_trigger and
                price<float(ema3.iloc[-1])<float(ema8.iloc[-1]) and
                three_min_change<0 and
                short_follow_through_confirmed and
                below_vwap and
                ten_min_change>-0.006 and
                signal_range<=float(avg_range)*2.5
            )
            short_close_position=(signal_high-signal_close)/signal_range
            pullback_to_ema8_short=(
                float(high.tail(5).max())>=float(ema8.iloc[-1]) and
                price<float(ema3.iloc[-1])
            )

            if one_min_change<0:
                short_score+=1
                short_reasons.append("red 1m candle")

            if short_trigger_confirmed:
                short_score+=3
                short_reasons.append("1m bearish trigger candle")
            elif signal_range>float(avg_range)*2.5:
                short_score-=2
                short_reasons.append("trigger candle too large")

            if short_continuation_confirmed:
                short_score+=2
                short_reasons.append("strong 1m bearish continuation")

            if short_close_position>=0.65:
                short_score+=2
                short_reasons.append("trigger closed near low")

            if short_current_holds_trigger:
                short_score+=1
                short_reasons.append("price holding below trigger")

            if pullback_to_ema8_short:
                short_score+=2
                short_reasons.append("1m EMA8 pullback rejected")

            if trend_strength<-0.0008:
                short_score+=1
                short_reasons.append("clean 1m downtrend strength")

            if three_min_change<-0.001:
                short_score+=2
                short_reasons.append("3m downside momentum")

            if -0.008<ten_min_change<0:
                short_score+=1
                short_reasons.append("controlled 10m drop")
            elif ten_min_change<=-0.012:
                short_score-=2
                short_reasons.append("avoiding 1m downside spike chase")

            if 32<=rsi<=55:
                short_score+=2
                short_reasons.append("healthy 1m short RSI")
            elif 28<=rsi<32:
                short_score+=1
                short_reasons.append("strong downside RSI")

            if 0.0005<=resistance_distance<=0.006:
                short_score+=2
                short_reasons.append("near 1m resistance")

            if support_distance>0.001:
                short_score+=1
                short_reasons.append("room to 1m support")

            if volume is not None:

                if recent_volume_sum>0 and price<vwap:
                    short_score+=2
                    short_reasons.append("below 1m VWAP")

                if avg_volume>0 and volume.iloc[-1]>avg_volume:
                    short_score+=1
                    short_reasons.append("1m volume above average")

                if trigger_avg_volume>0 and volume.iloc[-2]>trigger_avg_volume*1.3:
                    short_score+=2
                    short_reasons.append("trigger volume surge")

            results.append({
                "Ticker":symbol,
                "Price":round(price,2),
                "Score":short_score,
                "RSI":round(float(rsi),2),
                "Volatility":round(volatility,2),
                "Reason":", ".join(short_reasons) or "no 1m short setup",
                "Direction":"SHORT",
                "Trigger Confirmed":short_trigger_confirmed,
                "Continuation Confirmed":short_continuation_confirmed,
                "Follow Through Confirmed":short_follow_through_confirmed,
                "Trigger Time":format_chart_time(signal_time),
                "Trigger High":round(signal_high,2),
                "Trigger Close":round(signal_close,2),
                "Trigger Age Seconds":round(trigger_age_seconds,2) if trigger_age_seconds is not None else None
            })

        except Exception:

            pass

    return sorted(
        results,
        key=lambda x:x["Score"],
        reverse=True
    )


def rsi_bucket(rsi):

    if rsi is None:
        return "rsi_unknown"

    rsi=float(rsi)

    if rsi<30:
        return "rsi_under_30"
    if rsi<40:
        return "rsi_30_40"
    if rsi<55:
        return "rsi_40_55"
    if rsi<68:
        return "rsi_55_68"
    if rsi<75:
        return "rsi_68_75"

    return "rsi_over_75"


def brain_pattern_key_for_setup(candidate,setup_type):

    reason=(candidate.get("Reason") or "").lower()
    direction=candidate.get("Direction","LONG")

    vwap="vwap_yes" if (
        ("above 1m vwap" in reason and direction=="LONG") or
        ("below 1m vwap" in reason and direction=="SHORT")
    ) else "vwap_no"

    fresh="fresh" if is_fresh_intraday_setup(candidate) else "late_or_unclear"
    volume="volume_yes" if "trigger volume surge" in reason else "volume_no"

    return "|".join([
        candidate.get("Market","Unknown"),
        direction,
        setup_type,
        rsi_bucket(candidate.get("RSI")),
        fresh,
        vwap,
        volume
    ])


def brain_pattern_key(candidate):

    setup_type=candidate.get("Setup Type") or detect_setup_type(
        candidate.get("Reason")
    )

    return brain_pattern_key_for_setup(
        candidate,
        setup_type
    )


def historical_candidate_from_data(symbol,market,data,i,direction):

    close=data["Close"].squeeze()
    open_price=data["Open"].squeeze()
    high=data["High"].squeeze()
    low=data["Low"].squeeze()
    volume=data["Volume"].squeeze() if "Volume" in data.columns else None

    if i<60 or i>=len(close)-25:
        return None

    price=float(close.iloc[i])
    ema3=close.ewm(span=3,adjust=False).mean()
    ema8=close.ewm(span=8,adjust=False).mean()
    ema21=close.ewm(span=21,adjust=False).mean()
    rsi=float(calculate_rsi(close).iloc[i])

    if pd.isna(rsi):
        return None

    one_min_change=(close.iloc[i]-close.iloc[i-1])/close.iloc[i-1]
    three_min_change=(close.iloc[i]-close.iloc[i-3])/close.iloc[i-3]
    ten_min_change=(close.iloc[i]-close.iloc[i-10])/close.iloc[i-10]
    signal_open=float(open_price.iloc[i-1])
    signal_close=float(close.iloc[i-1])
    signal_high=float(high.iloc[i-1])
    signal_low=float(low.iloc[i-1])
    previous_high=float(high.iloc[i-2])
    previous_low=float(low.iloc[i-2])
    signal_range=max(signal_high-signal_low,price*0.0001)
    avg_range=float((high-low).iloc[:i+1].tail(20).mean())
    signal_close_position=(signal_close-signal_low)/signal_range
    short_close_position=(signal_high-signal_close)/signal_range
    trend_strength=(float(ema3.iloc[i])-float(ema21.iloc[i]))/price
    recent_support=float(low.iloc[:i+1].rolling(20).min().iloc[-2])
    recent_resistance=float(high.iloc[:i+1].rolling(20).max().iloc[-2])
    support_distance=(price-recent_support)/price
    resistance_distance=(recent_resistance-price)/price
    above_vwap=True
    below_vwap=True
    avg_volume=None
    trigger_avg_volume=None

    if volume is not None:
        recent_volume=volume.iloc[:i+1].tail(60)
        recent_volume_sum=recent_volume.sum()

        if recent_volume_sum>0:
            typical_price=(high+low+close)/3
            vwap=float((typical_price.iloc[:i+1].tail(60)*recent_volume).sum()/recent_volume_sum)
            above_vwap=price>vwap
            below_vwap=price<vwap

        avg_volume=volume.iloc[:i+1].rolling(20).mean().iloc[-1]
        trigger_avg_volume=volume.iloc[:i+1].rolling(20).mean().iloc[-2]

    score=0
    reasons=[]

    if direction=="LONG":
        trigger_confirmed=(
            signal_close>signal_open and
            signal_close>previous_high and
            signal_range<=avg_range*2.5
        )
        follow_through=(
            price>signal_close and
            float(close.iloc[i])>float(open_price.iloc[i]) and
            one_min_change>0 and
            price>float(ema3.iloc[i])
        )
        continuation=(
            price>=signal_close and
            price>float(ema3.iloc[i])>float(ema8.iloc[i]) and
            three_min_change>0 and
            follow_through and
            above_vwap and
            ten_min_change<0.006 and
            signal_range<=avg_range*2.5
        )

        checks=[
            (price>float(ema3.iloc[i]),1,"above 1m EMA3"),
            (price>float(ema8.iloc[i]),2,"above 1m EMA8"),
            (price>float(ema21.iloc[i]),2,"above 1m EMA21"),
            (float(ema3.iloc[i])>float(ema8.iloc[i])>float(ema21.iloc[i]),2,"1m EMA stack bullish"),
            (one_min_change>0,1,"green 1m candle"),
            (trigger_confirmed,3,"1m bullish trigger candle"),
            (continuation,2,"strong 1m continuation"),
            (signal_close_position>=0.65,2,"trigger closed near high"),
            (price>=signal_close,1,"price holding above trigger"),
            (trend_strength>0.0008,1,"clean 1m trend strength"),
            (three_min_change>0.001,2,"3m momentum"),
            (0<ten_min_change<0.008,1,"controlled 10m move"),
            (45<=rsi<=68,2,"healthy 1m RSI"),
            (68<rsi<=72,1,"strong 1m RSI"),
            (0.0005<=support_distance<=0.006,2,"near 1m support"),
            (resistance_distance>0.001,1,"room to 1m resistance"),
            (above_vwap,2,"above 1m VWAP")
        ]
    else:
        trigger_confirmed=(
            signal_close<signal_open and
            signal_close<previous_low and
            signal_range<=avg_range*2.5
        )
        follow_through=(
            price<signal_close and
            float(close.iloc[i])<float(open_price.iloc[i]) and
            one_min_change<0 and
            price<float(ema3.iloc[i])
        )
        continuation=(
            price<=signal_close and
            price<float(ema3.iloc[i])<float(ema8.iloc[i]) and
            three_min_change<0 and
            follow_through and
            below_vwap and
            ten_min_change>-0.006 and
            signal_range<=avg_range*2.5
        )

        checks=[
            (price<float(ema3.iloc[i]),1,"below 1m EMA3"),
            (price<float(ema8.iloc[i]),2,"below 1m EMA8"),
            (price<float(ema21.iloc[i]),2,"below 1m EMA21"),
            (float(ema3.iloc[i])<float(ema8.iloc[i])<float(ema21.iloc[i]),2,"1m EMA stack bearish"),
            (one_min_change<0,1,"red 1m candle"),
            (trigger_confirmed,3,"1m bearish trigger candle"),
            (continuation,2,"strong 1m bearish continuation"),
            (short_close_position>=0.65,2,"trigger closed near low"),
            (price<=signal_close,1,"price holding below trigger"),
            (trend_strength<-0.0008,1,"clean 1m downtrend strength"),
            (three_min_change<-0.001,2,"3m downside momentum"),
            (-0.008<ten_min_change<0,1,"controlled 10m drop"),
            (32<=rsi<=55,2,"healthy 1m short RSI"),
            (28<=rsi<32,1,"strong downside RSI"),
            (0.0005<=resistance_distance<=0.006,2,"near 1m resistance"),
            (support_distance>0.001,1,"room to 1m support"),
            (below_vwap,2,"below 1m VWAP")
        ]

    for passed,points,text in checks:
        if passed:
            score+=points
            reasons.append(text)

    if volume is not None:
        if avg_volume is not None and avg_volume>0 and volume.iloc[i]>avg_volume:
            score+=1
            reasons.append("1m volume above average")

        if trigger_avg_volume is not None and trigger_avg_volume>0 and volume.iloc[i-1]>trigger_avg_volume*1.3:
            score+=2
            reasons.append("trigger volume surge")

    if score<MIN_SCORE_TO_TRADE:
        return None

    return {
        "Ticker":symbol,
        "Market":market,
        "Price":price,
        "Score":score,
        "Adjusted Score":score,
        "RSI":round(rsi,2),
        "Reason":", ".join(reasons) or "historical setup",
        "Direction":direction,
        "Trigger Confirmed":trigger_confirmed,
        "Continuation Confirmed":continuation,
        "Follow Through Confirmed":follow_through,
        "Trigger Age Seconds":60
    }


def simulate_historical_trade(candidate,data,i):

    close=data["Close"].squeeze()
    high=data["High"].squeeze()
    low=data["Low"].squeeze()
    direction=candidate.get("Direction","LONG")
    entry=float(close.iloc[i])
    tp=entry*(1+TAKE_PROFIT_PCT) if direction=="LONG" else entry*(1-TAKE_PROFIT_PCT)
    sl=entry*(1-STOP_LOSS_PCT) if direction=="LONG" else entry*(1+STOP_LOSS_PCT)
    exit_price=float(close.iloc[min(i+MAX_HOLD_MINUTES,len(close)-1)])

    for offset in range(1,MAX_HOLD_MINUTES+1):
        idx=i+offset

        if idx>=len(close):
            break

        hi=float(high.iloc[idx])
        lo=float(low.iloc[idx])
        current=float(close.iloc[idx])
        move_pct=((current-entry)/entry) if direction=="LONG" else ((entry-current)/entry)

        if direction=="LONG":
            if lo<=sl:
                exit_price=sl
                break
            if hi>=tp:
                exit_price=tp
                break
        else:
            if hi>=sl:
                exit_price=sl
                break
            if lo<=tp:
                exit_price=tp
                break

        if offset>=EARLY_FAILURE_MINUTES and move_pct<=EARLY_FAILURE_MAX_LOSS_PCT:
            exit_price=current
            break

    qty=LEARNING_SCOUT_POSITION_CASH/(entry*currency_to_usd_factor(candidate["Ticker"]))
    return profit_for_direction(
        direction,
        simulated_buy_fill(entry) if direction=="LONG" else simulated_sell_fill(entry),
        exit_fill_for_direction(direction,exit_price),
        qty,
        candidate["Ticker"]
    )


def upsert_brain_sample(cursor,email,candidate,profit,trained_at):

    key=brain_pattern_key(candidate)
    win=1 if profit>0 else 0

    cursor.execute("""
        INSERT INTO pattern_brain(
            email,pattern_key,market,direction,setup_type,trades,wins,total_profit,
            avg_profit,win_rate,last_trained
        )
        VALUES(?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(email,pattern_key) DO UPDATE SET
            trades=pattern_brain.trades+1,
            wins=pattern_brain.wins+excluded.wins,
            total_profit=pattern_brain.total_profit+excluded.total_profit,
            avg_profit=(pattern_brain.total_profit+excluded.total_profit)/(pattern_brain.trades+1),
            win_rate=((pattern_brain.wins+excluded.wins)*100.0)/(pattern_brain.trades+1),
            last_trained=excluded.last_trained
    """,(
        email,
        key,
        candidate.get("Market"),
        candidate.get("Direction"),
        candidate.get("Setup Type") or detect_setup_type(candidate.get("Reason")),
        1,
        win,
        profit,
        profit,
        100.0 if win else 0.0,
        trained_at
    ))


def brain_training_is_stale(cursor,email):

    cursor.execute("""
        SELECT finished_at
        FROM brain_training_runs
        WHERE email=? AND status='finished'
        ORDER BY id DESC
        LIMIT 1
    """,(email,))
    row=cursor.fetchone()

    if not row or not row[0]:
        return True

    try:
        finished=datetime.strptime(row[0],"%Y-%m-%d %H:%M:%S")
    except Exception:
        return True

    return datetime.now()-finished>timedelta(hours=BRAIN_TRAINING_HOURS)


def train_pattern_brain(cursor,conn,email):

    if not brain_training_is_stale(cursor,email):
        return

    started=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO brain_training_runs(email,started_at,status,note)
        VALUES(?,?,?,?)
    """,(email,started,"running","Training historical 1-minute pattern brain"))
    run_id=cursor.lastrowid
    conn.commit()

    symbols_done=0
    samples=0

    try:
        for symbol in BRAIN_TRAINING_SYMBOLS[:BRAIN_SYMBOL_LIMIT]:
            market=next(
                (
                    name for name,items in WATCHLISTS.items()
                    if symbol in items
                ),
                "Unknown"
            )

            try:
                data=yf.download(
                    symbol,
                    period=BRAIN_TRAINING_PERIOD,
                    interval=BRAIN_TRAINING_INTERVAL,
                    progress=False,
                    auto_adjust=True
                )

                if data.empty:
                    continue

                data=clean_data(data).dropna()

                if len(data)<100:
                    continue

                symbols_done+=1

                for i in range(60,len(data)-25,3):
                    for direction in ["LONG","SHORT"]:
                        candidate=historical_candidate_from_data(
                            symbol,
                            market,
                            data,
                            i,
                            direction
                        )

                        if not candidate:
                            continue

                        candidate["Setup Type"]=detect_setup_type(
                            candidate.get("Reason")
                        )
                        profit=simulate_historical_trade(
                            candidate,
                            data,
                            i
                        )
                        upsert_brain_sample(
                            cursor,
                            email,
                            candidate,
                            profit,
                            started
                        )
                        samples+=1

                        if samples%100==0:
                            conn.commit()

                conn.commit()

            except Exception:
                continue

        finished=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            UPDATE brain_training_runs
            SET finished_at=?,symbols=?,samples=?,status=?,note=?
            WHERE id=?
        """,(
            finished,
            symbols_done,
            samples,
            "finished",
            f"Brain trained on {samples} historical setup samples across {symbols_done} symbols.",
            run_id
        ))
        conn.commit()

    except Exception as exc:
        cursor.execute("""
            UPDATE brain_training_runs
            SET finished_at=?,symbols=?,samples=?,status=?,note=?
            WHERE id=?
        """,(
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            symbols_done,
            samples,
            "error",
            str(exc),
            run_id
        ))
        conn.commit()

def update_bot_state(
    cursor,
    conn,
    email,
    status,
    running=True,
    best_ticker=None,
    best_score=None,
    open_positions_count=0,
    today_profit=0.0,
    session_start_time=None
):

    cursor.execute("""
        INSERT INTO bot_state(
            email,running,pid,status,last_heartbeat,best_ticker,best_score,
            open_positions_count,today_profit,session_start_time
        )
        VALUES(?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(email) DO UPDATE SET
            running=excluded.running,
            pid=excluded.pid,
            status=excluded.status,
            last_heartbeat=excluded.last_heartbeat,
            best_ticker=excluded.best_ticker,
            best_score=excluded.best_score,
            open_positions_count=excluded.open_positions_count,
            today_profit=excluded.today_profit,
            session_start_time=COALESCE(excluded.session_start_time,bot_state.session_start_time)
    """,(
        email,
        1 if running else 0,
        os.getpid(),
        status,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        best_ticker,
        best_score,
        open_positions_count,
        today_profit,
        session_start_time
    ))

    conn.commit()


def session_totals(cursor,email,start_time,end_time=None):

    if not start_time:
        return 0.0,0

    if end_time:
        cursor.execute("""
            SELECT COALESCE(SUM(profit),0),COUNT(*)
            FROM trades
            WHERE email=? AND time>=? AND time<=?
        """,(
            email,
            start_time,
            end_time
        ))
    else:
        cursor.execute("""
            SELECT COALESCE(SUM(profit),0),COUNT(*)
            FROM trades
            WHERE email=? AND time>=?
        """,(
            email,
            start_time
        ))

    profit,trades=cursor.fetchone()

    return float(profit or 0),int(trades or 0)


def ensure_session_record(cursor,conn,email,start_time):

    if not start_time:
        return

    cursor.execute("""
        SELECT id
        FROM ai_sessions
        WHERE email=? AND start_time=? AND end_time IS NULL
        LIMIT 1
    """,(
        email,
        start_time
    ))

    if cursor.fetchone():
        return

    cursor.execute("""
        UPDATE ai_sessions
        SET end_time=?,
            status='interrupted'
        WHERE email=? AND end_time IS NULL
    """,(
        start_time,
        email
    ))

    cursor.execute("""
        INSERT INTO ai_sessions(email,start_time,status)
        VALUES(?,?,?)
    """,(
        email,
        start_time,
        "running"
    ))

    conn.commit()


def close_session_record(cursor,conn,email,end_time,status="stopped"):

    cursor.execute("""
        SELECT id,start_time
        FROM ai_sessions
        WHERE email=? AND end_time IS NULL
        ORDER BY id DESC
        LIMIT 1
    """,(
        email,
    ))

    row=cursor.fetchone()

    if not row:
        return

    session_id,start_time=row
    profit,trades=session_totals(
        cursor,
        email,
        start_time,
        end_time
    )

    cursor.execute("""
        UPDATE ai_sessions
        SET end_time=?,
            profit=?,
            trades=?,
            status=?
        WHERE id=?
    """,(
        end_time,
        profit,
        trades,
        status,
        session_id
    ))

    conn.commit()


def should_continue(cursor,email):

    cursor.execute(
        "SELECT running FROM bot_state WHERE email=?",
        (email,)
    )

    row=cursor.fetchone()

    return bool(row and row[0])


def should_search_for_new_trades(cursor,email):

    cursor.execute(
        "SELECT searching_enabled FROM bot_state WHERE email=?",
        (email,)
    )

    row=cursor.fetchone()

    return bool(row is None or row[0])


def current_worker_is_owner(cursor,email):

    cursor.execute(
        "SELECT pid FROM bot_state WHERE email=?",
        (email,)
    )

    row=cursor.fetchone()

    if not row or not row[0]:
        return True

    return int(row[0])==os.getpid()


def load_open_positions(cursor,email):

    cursor.execute("""
        SELECT id,ticker,entry,tp,sl,qty,entry_time,market,score,rsi,entry_reason,
               trigger_time,trigger_high,trigger_close,direction
        FROM open_positions_v2
        WHERE email=?
        ORDER BY id DESC
    """,(email,))

    return [
        {
            "ID":r[0],
            "Ticker":r[1],
            "Entry":float(r[2]),
            "TP":float(r[3]),
            "SL":float(r[4]),
            "Qty":float(r[5]),
            "Entry Time":r[6],
            "Market":r[7],
            "Score":r[8],
            "RSI":r[9],
            "Entry Reason":r[10],
            "Trigger Time":r[11],
            "Trigger High":r[12],
            "Trigger Close":r[13],
            "Direction":r[14] or "LONG"
        }
        for r in cursor.fetchall()
    ]


def detect_setup_type(reason):

    text=(reason or "").lower()

    if "strong 1m continuation" in text:
        return "strong_continuation"

    if "bearish" in text or "downside" in text or "below 1m" in text:
        return "bearish_trigger"

    if "bullish trigger candle" in text:
        return "bullish_trigger"

    if "ema8 pullback" in text:
        return "ema8_pullback"

    if "vwap" in text:
        return "vwap_momentum"

    return "general_1m"


def minutes_between(start_text,end_text):

    try:
        start=datetime.strptime(start_text,"%Y-%m-%d %H:%M:%S")
        end=datetime.strptime(end_text,"%Y-%m-%d %H:%M:%S")
        return round((end-start).total_seconds()/60,2)
    except Exception:
        return None


def review_closed_trade(trade):

    setup_type=detect_setup_type(
        trade.get("Entry Reason")
    )

    hold_minutes=minutes_between(
        trade.get("Entry Time"),
        trade.get("Exit Time")
    )

    move_pct=(
        (
            (
                trade["Entry"]-trade["Exit"]
                if trade.get("Direction","LONG")=="SHORT"
                else trade["Exit"]-trade["Entry"]
            )/trade["Entry"]
        )*100
        if trade.get("Entry")
        else 0
    )

    profit=trade.get("Profit",0)
    reason=trade.get("Reason","")
    entry_reason=(trade.get("Entry Reason") or "").lower()
    rsi=trade.get("RSI")

    if profit>0 and "Take profit" in reason:
        label="target_win"
        notes="I read the move correctly and price reached my full target."
    elif profit>0 and "Momentum profit" in reason:
        label="clean_scalp_win"
        notes="I caught enough momentum to close green before the move faded."
    elif profit>0:
        label="small_win"
        notes="The idea worked, but the move was not strong enough for a full target."
    elif "AI stopped" in reason:
        label="manual_stop"
        notes="Manual stop interrupted the trade, so learning impact should be small."
    elif "Stop loss" in reason:
        label="stop_loss_bad_entry"
        notes="My timing was bad: I was either late into the move or fighting stronger opposite pressure, so price reached my stop."
    elif "Early failure" in reason:
        label="early_failure"
        notes="My timing was not sharp enough. I need to catch the fresh setup before the big move, not enter in the middle after the easy part is gone."
    elif "Flat day-trade" in reason and profit<=0:
        label="flat_weak_setup"
        notes="The setup was not wrong immediately, but it failed to move enough like a real scalp."
    else:
        label="cost_or_timing_loss"
        notes="The trade could not beat spread/slippage/fees, so the timing was not good enough."

    if profit<0 and rsi is not None:
        try:
            rsi_value=float(rsi)
            if trade.get("Direction","LONG")=="LONG" and rsi_value>=70:
                notes+=" I also chased with RSI too high for a new long entry."
            elif trade.get("Direction","LONG")=="SHORT" and rsi_value<=30:
                notes+=" I also shorted after RSI was already very low."
        except Exception:
            pass

    if profit<0 and "mixed market scout" in entry_reason:
        notes+=" The mixed-market scout idea did not prove itself on this trade."

    return {
        "Setup Type":setup_type,
        "Review Label":label,
        "Review Notes":notes,
        "Hold Minutes":hold_minutes,
        "Move Pct":round(move_pct,4)
    }


def update_setup_memory(cursor,conn,email,trade):

    setup_type=trade.get("Setup Type") or detect_setup_type(
        trade.get("Entry Reason")
    )

    if trade.get("Review Label")=="manual_stop":
        return

    cursor.execute("""
        INSERT INTO setup_memory(
            email,setup_type,trades,wins,total_profit,avg_profit,last_review,updated_at
        )
        VALUES(?,?,?,?,?,?,?,?)
        ON CONFLICT(email,setup_type) DO UPDATE SET
            trades=setup_memory.trades+1,
            wins=setup_memory.wins+excluded.wins,
            total_profit=setup_memory.total_profit+excluded.total_profit,
            avg_profit=(setup_memory.total_profit+excluded.total_profit)/(setup_memory.trades+1),
            last_review=excluded.last_review,
            updated_at=excluded.updated_at
    """,(
        email,
        setup_type,
        1,
        1 if trade.get("Profit",0)>0 else 0,
        trade.get("Profit",0),
        trade.get("Profit",0),
        trade.get("Review Label"),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()


def save_closed_trade(cursor,conn,email,trade):

    review=review_closed_trade(
        trade
    )

    trade.update(review)

    cursor.execute("""
        INSERT INTO trades(
            email,time,ticker,entry,exit,profit,entry_time,exit_time,reason,
            market,score,rsi,direction,entry_reason,trigger_time,trigger_high,trigger_close,
            setup_type,review_label,review_notes,hold_minutes,move_pct
        )
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """,(
        email,
        trade["Time"],
        trade["Ticker"],
        trade["Entry"],
        trade["Exit"],
        trade["Profit"],
        trade["Entry Time"],
        trade["Exit Time"],
        trade["Reason"],
        trade.get("Market"),
        trade.get("Score"),
        trade.get("RSI"),
        trade.get("Direction","LONG"),
        trade.get("Entry Reason"),
        trade.get("Trigger Time"),
        trade.get("Trigger High"),
        trade.get("Trigger Close"),
        trade.get("Setup Type"),
        trade.get("Review Label"),
        trade.get("Review Notes"),
        trade.get("Hold Minutes"),
        trade.get("Move Pct")
    ))

    cursor.execute("""
        UPDATE users
        SET balance=balance+?,
            profit=profit+?,
            trades_taken=trades_taken+1
        WHERE email=?
    """,(
        trade["Profit"],
        trade["Profit"],
        email
    ))

    conn.commit()

    update_setup_memory(
        cursor,
        conn,
        email,
        trade
    )

    learn_from_closed_trade(
        cursor,
        conn,
        email,
        trade
    )


def delete_open_position(cursor,conn,pos_id):

    cursor.execute(
        "DELETE FROM open_positions_v2 WHERE id=?",
        (pos_id,)
    )

    conn.commit()


def save_open_position(cursor,conn,email,pos):

    cursor.execute("""
        INSERT OR IGNORE INTO open_positions_v2(
            email,ticker,entry,tp,sl,qty,entry_time,market,score,rsi,entry_reason,
            trigger_time,trigger_high,trigger_close,direction
        )
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """,(
        email,
        pos["Ticker"],
        pos["Entry"],
        pos["TP"],
        pos["SL"],
        pos["Qty"],
        pos["Entry Time"],
        pos.get("Market"),
        pos.get("Score"),
        pos.get("RSI"),
        pos.get("Entry Reason"),
        pos.get("Trigger Time"),
        pos.get("Trigger High"),
        pos.get("Trigger Close"),
        pos.get("Direction","LONG")
    ))

    conn.commit()

    return cursor.rowcount>0


def log_decision(cursor,conn,email,candidate,market,decision,reason,price=None):

    cursor.execute("""
        INSERT INTO trade_decisions(
            email,time,ticker,market,price,score,rsi,adjusted_score,decision,reason,memory_note,direction,
            trigger_time,trigger_high,trigger_close,setup_type
        )
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """,(
        email,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        candidate["Ticker"],
        market,
        price if price is not None else candidate.get("Price"),
        candidate.get("Score"),
        candidate.get("RSI"),
        candidate.get("Adjusted Score",candidate.get("Score")),
        decision,
        reason,
        candidate.get("Memory Note","No memory adjustment"),
        candidate.get("Direction","LONG"),
        candidate.get("Trigger Time"),
        candidate.get("Trigger High"),
        candidate.get("Trigger Close"),
        candidate.get("Setup Type")
    ))

    conn.commit()


def cleanup_pending_setups(cursor,conn,email,now):

    cutoff=(
        now-timedelta(seconds=PENDING_MAX_AGE_SECONDS)
    ).strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        DELETE FROM pending_setups
        WHERE email=? AND created_at<?
    """,(
        email,
        cutoff
    ))

    conn.commit()


def load_pending_setup(cursor,email,ticker,direction):

    cursor.execute("""
        SELECT id,price,score,rsi,reason,memory_note,trigger_time,trigger_high,trigger_close,created_at
        FROM pending_setups
        WHERE email=? AND ticker=? AND direction=?
        LIMIT 1
    """,(
        email,
        ticker,
        direction
    ))

    row=cursor.fetchone()

    if not row:
        return None

    return {
        "ID":row[0],
        "Price":float(row[1]),
        "Score":row[2],
        "RSI":row[3],
        "Reason":row[4],
        "Memory Note":row[5],
        "Trigger Time":row[6],
        "Trigger High":row[7],
        "Trigger Close":row[8],
        "Created At":row[9]
    }


def save_pending_setup(cursor,conn,email,candidate):

    cursor.execute("""
        INSERT OR REPLACE INTO pending_setups(
            email,ticker,market,direction,setup_type,price,score,rsi,reason,memory_note,
            trigger_time,trigger_high,trigger_close,created_at
        )
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """,(
        email,
        candidate["Ticker"],
        candidate.get("Market"),
        candidate.get("Direction","LONG"),
        candidate.get("Setup Type"),
        candidate.get("Price"),
        candidate.get("Adjusted Score",candidate.get("Score")),
        candidate.get("RSI"),
        candidate.get("Reason"),
        candidate.get("Memory Note"),
        candidate.get("Trigger Time"),
        candidate.get("Trigger High"),
        candidate.get("Trigger Close"),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()


def delete_pending_setup(cursor,conn,pending_id):

    cursor.execute(
        "DELETE FROM pending_setups WHERE id=?",
        (pending_id,)
    )

    conn.commit()


def pending_setup_ready(pending,now):

    try:
        created=datetime.strptime(
            pending["Created At"],
            "%Y-%m-%d %H:%M:%S"
        )
    except Exception:
        return True

    return (now-created).total_seconds()>=PENDING_CONFIRM_SECONDS


def pending_setup_confirmed(pending,candidate):

    direction=candidate.get("Direction","LONG")
    current_price=float(candidate.get("Price") or 0)
    pending_price=float(pending.get("Price") or 0)

    if current_price<=0 or pending_price<=0:
        return False,"Pending confirmation missing price"

    if active_learning_candidate(candidate):
        if direction=="SHORT":
            return True,"Pending setup accepted by active learning: direction control stayed valid"
        return True,"Pending setup accepted by active learning: direction control stayed valid"

    if direction=="SHORT":

        if current_price>=pending_price:
            return False,"Pending SHORT failed: price did not move lower"

        if not (
            has_direction_control(candidate) or
            qualifies_for_crypto_short_test(candidate)
        ):
            return False,"Pending SHORT failed: price moved lower but seller control was not clean enough"

        return True,"Early timing accepted: price moved lower and seller control stayed valid before the move got too late"

    if current_price<=pending_price:
        return False,"Pending LONG failed: price did not move higher"

    if not (
        has_direction_control(candidate)
    ):
        return False,"Pending LONG failed: price moved higher but buyer control was not clean enough"

    return True,"Early timing accepted: price moved higher and buyer control stayed valid before the move got too late"


def log_trade_close(cursor,conn,email,trade):

    cursor.execute("""
        INSERT INTO trade_decisions(
            email,time,ticker,market,price,score,rsi,adjusted_score,decision,reason,memory_note,direction,
            trigger_time,trigger_high,trigger_close
        )
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """,(
        email,
        trade["Exit Time"],
        trade["Ticker"],
        trade.get("Market"),
        trade["Exit"],
        trade.get("Score"),
        trade.get("RSI"),
        trade.get("Score"),
        "closed",
        f"{trade['Reason']} | P/L ${trade['Profit']:.2f}",
        trade.get("Entry Reason") or "Closed trade",
        trade.get("Direction","LONG"),
        trade.get("Trigger Time"),
        trade.get("Trigger High"),
        trade.get("Trigger Close")
    ))

    conn.commit()


def save_ai_lesson(cursor,conn,email,source,lesson):

    if not lesson:
        return

    lesson=lesson.strip()

    cursor.execute("""
        SELECT id
        FROM ai_lessons
        WHERE email=? AND lesson=? AND active=1
        LIMIT 1
    """,(
        email,
        lesson
    ))

    if cursor.fetchone():
        return

    cursor.execute("""
        INSERT INTO ai_lessons(email,created_at,source,lesson,active)
        VALUES(?,?,?,?,1)
    """,(
        email,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        source,
        lesson
    ))

    conn.commit()


def active_ai_lessons(cursor,email,limit=5):

    cursor.execute("""
        SELECT lesson
        FROM ai_lessons
        WHERE email=? AND active=1
        ORDER BY id DESC
        LIMIT ?
    """,(
        email,
        limit
    ))

    return [
        row[0]
        for row in cursor.fetchall()
        if row and row[0]
    ]


def seed_human_lessons(cursor,conn,email):

    lessons=[
        (
            "human_review",
            "BTC and ETH should not make me afraid of other coins. I should use them as lead signals: a fast BTC/ETH drop can create short opportunities on weaker altcoins, while mixed BTC/ETH is context, not a full block."
        ),
        (
            "human_review",
            "My goal is to learn like a neutral day trader, not trade with fear. Losing history should teach me what to watch, but it should not make me freeze."
        ),
        (
            "human_review",
            "In the last long session, most losses were timing failures. I should not wait until the middle of the move. I need to catch fresh 1-minute setups earlier, while buyer or seller control is just starting and before the move becomes a chase."
        )
    ]

    for source,lesson in lessons:
        save_ai_lesson(
            cursor,
            conn,
            email,
            source,
            lesson
        )


def learn_from_closed_trade(cursor,conn,email,trade):

    review_label=trade.get("Review Label")
    direction=trade.get("Direction","LONG")
    setup_type=trade.get("Setup Type") or "unknown_setup"

    if review_label=="early_failure":
        save_ai_lesson(
            cursor,
            conn,
            email,
            "closed_trade",
            (
                f"When I trade {direction} {setup_type}, early failures usually mean my timing was poor: "
                "I joined too late or in the middle of the move. Next time I should look for the fresh "
                "1-minute entry while direction control is just starting, not after the big candle is obvious."
            )
        )

    elif review_label=="stop_loss_bad_entry":
        save_ai_lesson(
            cursor,
            conn,
            email,
            "closed_trade",
            (
                f"A {direction} {setup_type} stop loss means I may have entered into a reversal. "
                "Next time I should check whether price is stretched, near support/resistance, or "
                "fighting the latest 1m momentum before trusting the setup."
            )
        )

    elif review_label in ["target_win","clean_scalp_win"]:
        save_ai_lesson(
            cursor,
            conn,
            email,
            "closed_trade",
            (
                f"{direction} {setup_type} produced a clean win. I should remember what worked, "
                "but only increase trust after the pattern repeats across more trades."
            )
        )


def pre_entry_self_check(cursor,email,candidate,quality_reason):

    lessons=active_ai_lessons(
        cursor,
        email,
        5
    )

    direction=candidate.get("Direction","LONG")
    setup_type=candidate.get("Setup Type") or "unknown_setup"
    reason=(candidate.get("Reason") or "").lower()
    rsi=candidate.get("RSI")
    applied=[]
    risk_notes=[]
    proof=[]

    cursor.execute("""
        SELECT COUNT(*)
        FROM trades
        WHERE email=?
          AND setup_type=?
          AND COALESCE(direction,'LONG')=?
          AND review_label='early_failure'
    """,(
        email,
        setup_type,
        direction
    ))
    repeated_early_failures=cursor.fetchone()[0] or 0
    brain_memory=candidate.get("Brain Memory") or get_brain_memory(
        cursor,
        email,
        candidate
    )

    for lesson in lessons:
        lower=lesson.lower()

        if "early" in lower or "follow-through" in lower:
            applied.append("early-entry lesson")
        elif "btc" in lower or "eth" in lower:
            applied.append("BTC/ETH lead-signal lesson")
        elif "fear" in lower or "freeze" in lower:
            applied.append("neutral-trader lesson")
        elif "stop loss" in lower or "reversal" in lower:
            applied.append("reversal-risk lesson")

    if candidate.get("Follow Through Confirmed"):
        proof.append("follow-through is confirmed")
    if candidate.get("Continuation Confirmed"):
        proof.append("continuation is confirmed")
    if "price holding below trigger" in reason and direction=="SHORT":
        proof.append("price is holding below the short trigger")
    if "price holding above trigger" in reason and direction=="LONG":
        proof.append("price is holding above the long trigger")
    if "below 1m vwap" in reason and direction=="SHORT":
        proof.append("price is below VWAP for a short")
    if "above 1m vwap" in reason and direction=="LONG":
        proof.append("price is above VWAP for a long")
    if "trigger volume surge" in reason:
        proof.append("volume expanded on the trigger")
    if "BTC/ETH lead signal" in candidate.get("Memory Note",""):
        proof.append("BTC/ETH lead signal supports the idea")
    if is_fresh_intraday_setup(candidate):
        proof.append("fresh 1m setup, not a late chase")
    if brain_is_good(brain_memory):
        proof.append(
            f"trained brain likes this pattern: {brain_memory['win_rate']:.0f}% win rate over {brain_memory['trades']} samples"
        )

    if not candidate.get("Follow Through Confirmed") and not candidate.get("Continuation Confirmed"):
        risk_notes.append("I must time the entry early, before the setup becomes a middle-of-move chase")
    if candidate.get("Crypto Market Caution"):
        risk_notes.append("crypto market context is mixed, so size must stay controlled")
    if candidate.get("Knowledge Grade")=="D":
        risk_notes.append("my knowledge grade is weak, so this is only a learning scout")
    if repeated_early_failures>=3:
        risk_notes.append(
            f"this same {direction} {setup_type} pattern already has {repeated_early_failures} early failures in memory"
        )
    if brain_is_bad(brain_memory):
        risk_notes.append(
            f"my trained replay brain dislikes this exact pattern: {brain_memory['win_rate']:.0f}% win rate over {brain_memory['trades']} samples"
        )
    if "near 1m support" in reason and direction=="SHORT":
        risk_notes.append("short is near support")
    if "near 1m resistance" in reason and direction=="LONG":
        risk_notes.append("long is near resistance")
    if direction=="SHORT" and "controlled 10m drop" in reason and rsi is not None and rsi<40:
        risk_notes.append("short may be late after a 10m drop with low RSI")
    if direction=="LONG" and "controlled 10m move" in reason and rsi is not None and rsi>70:
        risk_notes.append("long may be late after a 10m move with high RSI")
    if is_late_chase_setup(candidate):
        risk_notes.append("the move looks late, so this may be chasing instead of fresh day trading")

    applied_unique=list(dict.fromkeys(applied))
    proof_count=len(proof)
    risk_count=len(risk_notes)

    has_strong_followthrough=(
        candidate.get("Follow Through Confirmed") and
        candidate.get("Continuation Confirmed") and
        (
            "trigger volume surge" in reason or
            "BTC/ETH lead signal" in candidate.get("Memory Note","")
        )
    )

    strong_live_setup=(
        candidate.get("Adjusted Score",candidate.get("Score",0))>=STRONG_LIVE_MIN_SCORE and
        candidate.get("Opportunity Score",0)>=STRONG_LIVE_MIN_OPPORTUNITY and
        proof_count>=STRONG_LIVE_MIN_PROOF_COUNT and
        risk_count<=STRONG_LIVE_MAX_RISK_COUNT and
        is_fresh_intraday_setup(candidate) and
        (
            is_preferred_entry_family(candidate) or
            (
                not is_weak_breakout_family(candidate) and
                35<=float(candidate.get("RSI") or 0)<=68
            ) or
            (
                candidate.get("Opportunity Score",0)>=58 and
                proof_count>=7 and
                40<=float(candidate.get("RSI") or 0)<=65
            )
        ) and
        not is_late_chase_setup(candidate) and
        not brain_is_hard_wait(brain_memory)
    )

    opportunity_rescue_setup=(
        candidate.get("Opportunity Score",0)>=OPPORTUNITY_RESCUE_MIN_SCORE and
        proof_count>=4 and
        risk_count<=5 and
        has_direction_control(candidate) and
        not is_late_chase_setup(candidate) and
        not brain_is_hard_wait(brain_memory)
    )

    hard_wait_live_override=(
        candidate.get("Opportunity Score",0)>=OPPORTUNITY_NORMAL_MIN_SCORE and
        proof_count>=6 and
        risk_count<=4 and
        has_direction_control(candidate) and
        candidate.get("Follow Through Confirmed") and
        candidate.get("Continuation Confirmed") and
        not is_late_chase_setup(candidate)
    )

    active_learning_setup=(
        active_learning_candidate(candidate) and
        proof_count>=2 and
        risk_count<=6
    )

    direct_order_setup=(
        candidate.get("Direct Order Trade") and
        direct_order_candidate(candidate)
    )

    if (
        strong_live_setup
    ):
        candidate["Strong Live Idea"]=True
        action="ENTER"
        action_reason=(
            "This is a strong live setup: clean 1m proof, fresh entry, controlled risk, and enough score for normal size."
        )
    elif opportunity_rescue_setup:
        candidate["Strong Live Idea"]=False
        candidate["Opportunity Rescue"]=True
        action="ENTER"
        action_reason=(
            "Live opportunity rescue: old memory is cautious, but this 1m setup has enough fresh proof to take a controlled trade."
        )
    elif hard_wait_live_override:
        candidate["Strong Live Idea"]=False
        candidate["Opportunity Rescue"]=True
        candidate["Hard Wait Override"]=True
        action="ENTER"
        action_reason=(
            "Live proof override: old replay memory dislikes this pattern, but the current 1m setup has strong fresh confirmation, so I will take a controlled test trade."
        )
    elif active_learning_setup:
        candidate["Strong Live Idea"]=False
        candidate["Opportunity Rescue"]=True
        candidate["Active Learning Trade"]=True
        action="ENTER"
        action_reason=(
            "Active learning trade: the setup is controlled and directional enough to collect real trade data with small size."
        )
    elif direct_order_setup:
        candidate["Strong Live Idea"]=False
        candidate["Opportunity Rescue"]=True
        candidate["Active Learning Trade"]=True
        action="ENTER"
        action_reason=(
            f"Direct order mode: at least one trade is required every {DIRECT_ORDER_MIN_TRADE_MINUTES} idle minutes, using controlled paper risk."
        )
    elif (
        candidate.get("Brain Exploration") and
        proof_count>=1
    ):
        candidate["Strong Live Idea"]=False
        action="LEARNING_SCOUT"
        action_reason=(
            f"The brain dislikes the pattern, but I have been quiet; this is a ${BRAIN_EXPLORATION_POSITION_CASH:,.0f} exploration trade only for learning data."
        )
    elif (
        brain_is_good(brain_memory) and
        not is_late_chase_setup(candidate)
    ):
        candidate["Strong Live Idea"]=False
        action="ENTER"
        action_reason=(
            "My trained replay brain found this pattern profitable enough to hunt it."
        )
    elif brain_is_hard_wait(brain_memory) and not brain_override_allowed(candidate,brain_memory):
        candidate["Strong Live Idea"]=False
        action="WAIT"
        action_reason=(
            "My trained replay brain says this exact pattern has too low a historical win rate, so I should not enter."
        )
    elif brain_is_bad(brain_memory) and not brain_override_allowed(candidate,brain_memory):
        candidate["Strong Live Idea"]=False
        action="WAIT"
        action_reason=(
            "My trained replay brain dislikes this pattern, and the live setup is not strong enough to override that warning."
        )
    elif (
        repeated_early_failures>=6 and
        is_late_chase_setup(candidate)
    ):
        candidate["Strong Live Idea"]=False
        action="WAIT"
        action_reason=(
            "My memory shows this setup keeps failing early, and this one looks late instead of fresh."
        )
    elif (
        repeated_early_failures>=6 and
        not has_strong_followthrough and
        any("middle-of-move chase" in note for note in risk_notes)
    ):
        candidate["Strong Live Idea"]=False
        action="WAIT"
        action_reason=(
            "My memory shows this exact setup keeps failing when I enter late; I need an earlier trigger instead of joining the middle of the move."
        )
    elif "early-entry lesson" in applied_unique and proof_count==0:
        candidate["Strong Live Idea"]=False
        action="WAIT"
        action_reason="I recognized my timing mistake: I need a fresh early entry, not a late middle-of-move entry."
    elif risk_count>proof_count:
        candidate["Strong Live Idea"]=False
        action="LEARNING_SCOUT"
        action_reason="The idea is useful for learning, but risk is higher than proof, so I should use tiny size only."
    else:
        candidate["Strong Live Idea"]=False
        action="ENTER"
        action_reason="The setup has enough proof for the current mode."

    applied_text=", ".join(applied_unique) if applied_unique else "general trade memory"
    proof_text=", ".join(proof) if proof else "the setup passed the current scanner and pending confirmation"
    risk_text=", ".join(risk_notes) if risk_notes else "no major repeated mistake detected"

    text=(
        f"AI self-check before entry: I am considering {direction} {setup_type}. "
        f"Lessons applied: {applied_text}. "
        f"Why this is not blind repetition: {proof_text}. "
        f"Risk I must respect: {risk_text}. "
        f"Self-check action: {action}. "
        f"Why: {action_reason} "
        f"Gate result: {quality_reason}"
    )

    return {
        "Action":action,
        "Text":text,
        "Proof Count":proof_count,
        "Risk Count":risk_count,
        "Reason":action_reason
    }


def get_ticker_memory(cursor,email,ticker,direction=None):

    direction_filter=""
    params=[
        email,
        ticker
    ]

    if direction:
        direction_filter=" AND COALESCE(direction,'LONG')=?"
        params.append(direction)

    cursor.execute("""
        SELECT COUNT(*),
               SUM(CASE WHEN profit>0 THEN 1 ELSE 0 END),
               COALESCE(SUM(profit),0),
               COALESCE(AVG(profit),0)
        FROM trades
        WHERE email=? AND ticker=?
    """+direction_filter,params)

    total,wins,total_profit,avg_profit=cursor.fetchone()

    total=total or 0
    wins=wins or 0
    win_rate=(wins/total)*100 if total>0 else None

    return {
        "trades":total,
        "wins":wins,
        "win_rate":win_rate,
        "total_profit":total_profit,
        "avg_profit":avg_profit
    }


def get_combo_memory(cursor,email,ticker,setup_type,direction):

    cursor.execute("""
        SELECT COUNT(*),
               SUM(CASE WHEN profit>0 THEN 1 ELSE 0 END),
               COALESCE(SUM(profit),0),
               COALESCE(AVG(profit),0)
        FROM trades
        WHERE email=?
          AND ticker=?
          AND setup_type=?
          AND COALESCE(direction,'LONG')=?
    """,(
        email,
        ticker,
        setup_type,
        direction
    ))

    total,wins,total_profit,avg_profit=cursor.fetchone()
    total=total or 0
    wins=wins or 0

    return {
        "trades":total,
        "wins":wins,
        "win_rate":(wins/total)*100 if total else None,
        "total_profit":total_profit,
        "avg_profit":avg_profit
    }


def get_setup_memory(cursor,email,setup_type,market=None,direction=None):

    filters=[
        "email=?",
        "setup_type=?"
    ]
    params=[
        email,
        setup_type
    ]

    if market:
        filters.append("market=?")
        params.append(market)

    if direction:
        filters.append("COALESCE(direction,'LONG')=?")
        params.append(direction)

    cursor.execute("""
        SELECT COUNT(*),
               SUM(CASE WHEN profit>0 THEN 1 ELSE 0 END),
               COALESCE(SUM(profit),0),
               COALESCE(AVG(profit),0)
        FROM trades
        WHERE """+" AND ".join(filters),params)

    row=cursor.fetchone()

    if not row or not row[0]:
        return {
            "trades":0,
            "wins":0,
            "win_rate":None,
            "total_profit":0,
            "avg_profit":0,
            "last_review":None
        }

    trades,wins,total_profit,avg_profit=row
    trades=trades or 0
    wins=wins or 0

    return {
        "trades":trades,
        "wins":wins,
        "win_rate":(wins/trades)*100 if trades else None,
        "total_profit":total_profit or 0,
        "avg_profit":avg_profit or 0,
        "last_review":None
    }


def setup_block_reason(cursor,email,setup_type,market=None,direction=None):

    setup_memory=get_setup_memory(
        cursor,
        email,
        setup_type,
        market,
        direction
    )

    trades=setup_memory["trades"]
    win_rate=setup_memory["win_rate"]
    avg_profit=setup_memory["avg_profit"]
    total_profit=setup_memory["total_profit"]

    if trades<BAD_SETUP_MIN_TRADES or total_profit>=0:
        return None

    return None


def get_brain_memory(cursor,email,candidate):

    key=brain_pattern_key(candidate)

    return get_brain_memory_for_key(
        cursor,
        email,
        key
    )


def get_brain_memory_for_key(cursor,email,key):

    cursor.execute("""
        SELECT trades,wins,total_profit,avg_profit,win_rate,last_trained
        FROM pattern_brain
        WHERE email=? AND pattern_key=?
    """,(
        email,
        key
    ))
    row=cursor.fetchone()

    if not row:
        return {
            "key":key,
            "trades":0,
            "wins":0,
            "total_profit":0,
            "avg_profit":0,
            "win_rate":None,
            "last_trained":None
        }

    trades,wins,total_profit,avg_profit,win_rate,last_trained=row

    return {
        "key":key,
        "trades":trades or 0,
        "wins":wins or 0,
        "total_profit":total_profit or 0,
        "avg_profit":avg_profit or 0,
        "win_rate":win_rate,
        "last_trained":last_trained
    }


def brain_candidate_memory_options(cursor,email,candidate):

    reason=(candidate.get("Reason") or "").lower()
    setup_type=candidate.get("Setup Type") or detect_setup_type(
        candidate.get("Reason")
    )
    setup_options=[setup_type]

    if "vwap" in reason:
        setup_options.append("vwap_momentum")

    if "strong 1m" in reason:
        setup_options.append("strong_continuation")

    if candidate.get("Direction","LONG")=="LONG" and "bullish trigger candle" in reason:
        setup_options.append("bullish_trigger")

    if candidate.get("Direction","LONG")=="SHORT" and ("bearish" in reason or "below 1m" in reason):
        setup_options.append("bearish_trigger")

    seen=set()
    memories=[]

    for option in setup_options:
        key=brain_pattern_key_for_setup(
            candidate,
            option
        )

        if key in seen:
            continue

        seen.add(key)
        memories.append(
            get_brain_memory_for_key(
                cursor,
                email,
                key
            )
        )

    return memories


def brain_is_good(memory):

    return (
        memory.get("trades",0)>=BRAIN_MIN_PATTERN_TRADES and
        memory.get("win_rate") is not None and
        memory.get("win_rate")>=BRAIN_GOOD_WIN_RATE and
        memory.get("avg_profit",0)>0
    )


def best_brain_memory(cursor,email,candidate):

    memories=brain_candidate_memory_options(
        cursor,
        email,
        candidate
    )

    good=[
        memory for memory in memories
        if brain_is_good(memory)
    ]

    if good:
        return sorted(
            good,
            key=lambda memory:(
                memory.get("avg_profit",0),
                memory.get("win_rate") or 0,
                memory.get("trades",0)
            ),
            reverse=True
        )[0]

    family_memory=best_brain_family_memory(
        cursor,
        email,
        candidate
    )

    if brain_is_good(family_memory):
        return family_memory

    return memories[0] if memories else get_brain_memory(
        cursor,
        email,
        candidate
    )


def best_brain_family_memory(cursor,email,candidate):

    reason=(candidate.get("Reason") or "").lower()
    direction=candidate.get("Direction","LONG")
    market=candidate.get("Market","Unknown")
    setup_type=candidate.get("Setup Type") or detect_setup_type(
        candidate.get("Reason")
    )

    setup_options=[setup_type]

    if "vwap" in reason:
        setup_options.insert(
            0,
            "vwap_momentum"
        )

    setup_options=list(dict.fromkeys(setup_options))

    for option in setup_options:
        cursor.execute("""
            SELECT pattern_key,trades,wins,total_profit,avg_profit,win_rate,last_trained
            FROM pattern_brain
            WHERE email=?
              AND market=?
              AND direction=?
              AND setup_type=?
              AND trades>=?
              AND win_rate>=?
              AND avg_profit>0
            ORDER BY avg_profit DESC, win_rate DESC, trades DESC
            LIMIT 1
        """,(
            email,
            market,
            direction,
            option,
            BRAIN_MIN_PATTERN_TRADES,
            BRAIN_GOOD_WIN_RATE
        ))
        row=cursor.fetchone()

        if row:
            key,trades,wins,total_profit,avg_profit,win_rate,last_trained=row
            return {
                "key":key,
                "trades":trades or 0,
                "wins":wins or 0,
                "total_profit":total_profit or 0,
                "avg_profit":avg_profit or 0,
                "win_rate":win_rate,
                "last_trained":last_trained,
                "family_match":True
            }

    return {
        "key":brain_pattern_key(candidate),
        "trades":0,
        "wins":0,
        "total_profit":0,
        "avg_profit":0,
        "win_rate":None,
        "last_trained":None,
        "family_match":False
    }


def brain_is_bad(memory):

    return (
        memory.get("trades",0)>=BRAIN_MIN_PATTERN_TRADES and
        memory.get("win_rate") is not None and
        memory.get("win_rate")<=BRAIN_BAD_WIN_RATE and
        memory.get("avg_profit",0)<0
    )


def brain_is_hard_wait(memory):

    return (
        memory.get("trades",0)>=BRAIN_MIN_PATTERN_TRADES and
        memory.get("win_rate") is not None and
        memory.get("win_rate")<=BRAIN_HARD_WAIT_WIN_RATE and
        memory.get("avg_profit",0)<0
    )


def brain_override_allowed(candidate,memory):

    reason=(candidate.get("Reason") or "").lower()

    return (
        brain_is_bad(memory) and
        not brain_is_hard_wait(memory) and
        candidate.get("Adjusted Score",candidate.get("Score",0))>=BRAIN_OVERRIDE_SCORE and
        is_fresh_intraday_setup(candidate) and
        candidate.get("Follow Through Confirmed") and
        candidate.get("Continuation Confirmed") and
        "trigger volume surge" in reason
    )


def memory_confidence(memory):

    trades=memory.get("trades") or 0
    win_rate=memory.get("win_rate")
    avg_profit=memory.get("avg_profit") or 0
    total_profit=memory.get("total_profit") or 0

    if trades<3:
        return "new"

    if trades>=8 and total_profit>0 and avg_profit>0 and win_rate is not None and win_rate>=58:
        return "trusted"

    if trades>=6 and total_profit<0 and avg_profit<0 and win_rate is not None and win_rate<=35:
        return "learning"

    if trades>=4 and (total_profit<0 or avg_profit<0 or (win_rate is not None and win_rate<45)):
        return "learning"

    return "normal"


def confidence_note(name,memory):

    confidence=memory_confidence(
        memory
    )

    trades=memory.get("trades") or 0
    win_rate=memory.get("win_rate")
    avg_profit=memory.get("avg_profit") or 0
    total_profit=memory.get("total_profit") or 0

    if win_rate is None:
        return f"{name} confidence {confidence}: no trade history yet"

    return (
        f"{name} confidence {confidence}: {win_rate:.0f}% win rate, "
        f"${avg_profit:.2f} avg, ${total_profit:.2f} total over {trades} trades"
    )


def ticker_block_reason(memory):

    trades=memory["trades"]
    win_rate=memory["win_rate"]
    avg_profit=memory["avg_profit"]
    total_profit=memory["total_profit"]

    if trades<BAD_TICKER_MIN_TRADES:
        return None

    if (
        total_profit<=BAD_TICKER_MAX_TOTAL_PROFIT and
        avg_profit<=BAD_TICKER_MAX_AVG_PROFIT and
        win_rate is not None and
        win_rate<=BAD_TICKER_MAX_WIN_RATE
    ):
        return (
            f"Ticker memory blocked: {win_rate:.0f}% win rate, "
            f"${avg_profit:.2f} average profit over {trades} trades"
        )

    return None


def combo_block_reason(memory,ticker,setup_type,direction):

    trades=memory["trades"]
    win_rate=memory["win_rate"]
    avg_profit=memory["avg_profit"]
    total_profit=memory["total_profit"]

    if trades<BAD_COMBO_MIN_TRADES or total_profit>=0:
        return None

    if (
        avg_profit<=BAD_COMBO_MAX_AVG_PROFIT and
        win_rate is not None and
        win_rate<=BAD_COMBO_MAX_WIN_RATE
    ):
        return (
            f"Probation {ticker} {direction} {setup_type}: "
            f"{win_rate:.0f}% win rate, ${avg_profit:.2f} average over {trades} trades"
        )

    return None


def position_cash_from_memory(ticker_memory,setup_memory,blocked_combo):

    if blocked_combo:
        return PROBATION_POSITION_CASH

    ticker_confidence=memory_confidence(
        ticker_memory
    )
    setup_confidence=memory_confidence(
        setup_memory
    )

    if "learning" in [ticker_confidence,setup_confidence]:
        return SMALL_POSITION_CASH

    ticker_trusted=(
        ticker_memory["trades"]>=6 and
        ticker_memory["win_rate"] is not None and
        ticker_memory["win_rate"]>=55 and
        ticker_memory["avg_profit"]>0 and
        ticker_memory["total_profit"]>0
    )

    setup_trusted=(
        setup_memory["trades"]>=6 and
        setup_memory["win_rate"] is not None and
        setup_memory["win_rate"]>=55 and
        setup_memory["avg_profit"]>0 and
        setup_memory["total_profit"]>0
    )

    ticker_weak=(
        ticker_memory["trades"]>=BAD_TICKER_MIN_TRADES and
        ticker_memory["total_profit"]<0
    )

    setup_weak=(
        setup_memory["trades"]>=BAD_SETUP_MIN_TRADES and
        setup_memory["total_profit"]<0
    )

    if ticker_trusted and setup_trusted:
        return TRUSTED_POSITION_CASH

    if ticker_weak or setup_weak:
        return SMALL_POSITION_CASH

    return MEDIUM_POSITION_CASH


def setup_is_session_winner(cursor,email,setup_type,direction):

    session_start=latest_session_start(
        cursor,
        email
    )

    cursor.execute("""
        SELECT COUNT(*),COALESCE(SUM(profit),0),COALESCE(AVG(profit),0)
        FROM trades
        WHERE email=?
          AND time>=?
          AND setup_type=?
          AND COALESCE(direction,'LONG')=?
    """,(
        email,
        session_start,
        setup_type,
        direction
    ))

    trades,total_profit,avg_profit=cursor.fetchone()

    return (
        (trades or 0)>=2 and
        (total_profit or 0)>0 and
        (avg_profit or 0)>0
    )


def setup_is_session_loser(cursor,email,setup_type,direction):

    session_start=latest_session_start(
        cursor,
        email
    )

    cursor.execute("""
        SELECT COUNT(*),COALESCE(SUM(profit),0),COALESCE(AVG(profit),0)
        FROM trades
        WHERE email=?
          AND time>=?
          AND setup_type=?
          AND COALESCE(direction,'LONG')=?
    """,(
        email,
        session_start,
        setup_type,
        direction
    ))

    trades,total_profit,avg_profit=cursor.fetchone()

    return (
        (trades or 0)>=2 and
        (total_profit or 0)<0 and
        (avg_profit or 0)<0
    )


def recovery_raw_score_minimum(direction):

    return (
        MIN_RECOVERY_RAW_SHORT_SCORE
        if direction=="SHORT"
        else MIN_RECOVERY_RAW_LONG_SCORE
    )


def ticker_memory_is_trusted(memory):

    if memory["win_rate"] is None:
        return False

    return (
        memory["trades"]>=5 and
        memory["win_rate"]>=55 and
        memory["avg_profit"]>0 and
        memory["total_profit"]>0
    )


def qualifies_for_recovery_test(candidate):

    direction=candidate.get("Direction","LONG")
    minimum=recovery_raw_score_minimum(direction)

    if candidate.get("Ticker Recovery Trusted"):
        minimum=(
            MIN_TRUSTED_TICKER_RECOVERY_RAW_SHORT_SCORE
            if direction=="SHORT"
            else MIN_TRUSTED_TICKER_RECOVERY_RAW_LONG_SCORE
        )

    return candidate.get("Score",0)>=minimum


def qualifies_for_crypto_short_test(candidate):

    if candidate.get("Market")!="Crypto" and not str(candidate.get("Ticker","")).endswith("-USD"):
        return False

    if candidate.get("Direction","LONG")!="SHORT":
        return False

    reason=(candidate.get("Reason") or "").lower()
    rsi=float(candidate.get("RSI") or 0)

    return (
        candidate.get("Score",0)>=14 and
        "trigger candle too large" not in reason and
        (
            candidate.get("Follow Through Confirmed") or
            candidate.get("Score",0)>=18
        ) and
        (
            (
                candidate.get("Trigger Confirmed") and
                "trigger closed near low" in reason
            ) or
            candidate.get("Continuation Confirmed") or
            (
                "clean 1m downtrend strength" in reason and
                "below 1m vwap" in reason
            ) or
            (
                "price holding below trigger" in reason and
                "below 1m ema8" in reason and
                "below 1m ema21" in reason
            )
        ) and
        22<=rsi<=58
    )


def qualifies_for_mixed_market_scout(candidate):

    if candidate.get("Market")!="Crypto":
        return False

    reason=(candidate.get("Reason") or "").lower()
    direction=candidate.get("Direction","LONG")
    rsi=float(candidate.get("RSI") or 0)
    score=float(candidate.get("Adjusted Score",candidate.get("Score",0)) or 0)

    if score<MIN_MIXED_MARKET_SCOUT_SCORE:
        return False

    if "trigger candle too large" in reason:
        return False

    has_live_confirmation=(
        candidate.get("Follow Through Confirmed") or
        candidate.get("Continuation Confirmed")
    )

    if not has_live_confirmation:
        return False

    if direction=="LONG":
        return (
            42<=rsi<=72 and
            "above 1m vwap" in reason and
            (
                "price holding above trigger" in reason or
                "strong 1m continuation" in reason or
                "trigger closed near high" in reason
            )
        )

    return (
        28<=rsi<=58 and
        "below 1m vwap" in reason and
        (
            "price holding below trigger" in reason or
            "strong 1m continuation" in reason or
            "trigger closed near low" in reason or
            qualifies_for_crypto_short_test(candidate)
        )
    )


def minutes_since_last_trade(cursor,email,now):

    cursor.execute("""
        SELECT MAX(time)
        FROM trades
        WHERE email=?
    """,(email,))

    row=cursor.fetchone()

    if not row or not row[0]:
        return 9999

    try:
        last_trade_time=datetime.strptime(
            row[0],
            "%Y-%m-%d %H:%M:%S"
        )
    except Exception:
        return 9999

    return (now-last_trade_time).total_seconds()/60


def minutes_since_last_learning_scout(cursor,email,now):

    cursor.execute("""
        SELECT MAX(time)
        FROM trade_decisions
        WHERE email=? AND reason LIKE '%Learning scout%'
    """,(email,))

    row=cursor.fetchone()

    if not row or not row[0]:
        return 9999

    try:
        last_scout_time=datetime.strptime(
            row[0],
            "%Y-%m-%d %H:%M:%S"
        )
    except Exception:
        return 9999

    return (now-last_scout_time).total_seconds()/60


def minutes_since_last_alternate_scout(cursor,email,now):

    cursor.execute("""
        SELECT MAX(time)
        FROM trade_decisions
        WHERE email=? AND (
            reason LIKE '%Alternate setup scout%' OR
            memory_note LIKE '%Alternate setup scout%'
        )
    """,(email,))

    row=cursor.fetchone()

    if not row or not row[0]:
        return 9999

    try:
        last_scout_time=datetime.strptime(
            row[0],
            "%Y-%m-%d %H:%M:%S"
        )
    except Exception:
        return 9999

    return (now-last_scout_time).total_seconds()/60


def qualifies_for_learning_scout(candidate):

    if candidate.get("Market")!="Crypto":
        return False

    reason=(candidate.get("Reason") or "").lower()
    direction=candidate.get("Direction","LONG")
    rsi=float(candidate.get("RSI") or 0)
    raw_score=float(candidate.get("Score",0) or 0)
    adjusted_score=float(candidate.get("Adjusted Score",raw_score) or 0)

    if raw_score<MIN_SCORE_TO_TRADE+2 and adjusted_score<MIN_SCORE_TO_TRADE:
        return False

    if "trigger candle too large" in reason:
        return False

    has_direction_control=(
        ("above 1m vwap" in reason and direction=="LONG") or
        ("below 1m vwap" in reason and direction=="SHORT")
    )

    has_live_setup=(
        candidate.get("Follow Through Confirmed") or
        candidate.get("Continuation Confirmed") or
        "price holding above trigger" in reason or
        "price holding below trigger" in reason or
        "strong 1m continuation" in reason
    )

    if not has_direction_control or not has_live_setup:
        return False

    if direction=="LONG" and not (35<=rsi<=74):
        return False

    if direction=="SHORT" and not (30<=rsi<=68):
        return False

    if candidate.get("Setup Blocked"):
        return False

    return True


def qualifies_for_alternate_setup_scout(candidate):

    if candidate.get("Market")!="Crypto":
        return False

    reason=(candidate.get("Reason") or "").lower()
    direction=candidate.get("Direction","LONG")
    setup_type=candidate.get("Setup Type") or ""
    rsi=float(candidate.get("RSI") or 0)
    raw_score=float(candidate.get("Score",0) or 0)
    adjusted_score=float(candidate.get("Adjusted Score",raw_score) or 0)
    opportunity_score_value=float(candidate.get("Opportunity Score",0) or 0)

    if direction=="LONG" and setup_type=="ema8_pullback":
        return False

    has_enough_signal=(
        opportunity_score_value>=ALTERNATE_SETUP_SCOUT_MIN_OPPORTUNITY or
        raw_score>=ALTERNATE_SETUP_SCOUT_MIN_RAW_SCORE or
        adjusted_score>=ALTERNATE_SETUP_SCOUT_MIN_ADJUSTED_SCORE
    )

    if not has_enough_signal:
        return False

    if is_late_chase_setup(candidate):
        return False

    directional_control=has_direction_control(candidate)

    if direction=="SHORT":
        short_control=(
            directional_control or
            "below 1m vwap" in reason or
            "price holding below trigger" in reason
        )

        return short_control and 26<=rsi<=72

    long_control=(
        directional_control or
        "above 1m vwap" in reason or
        "price holding above trigger" in reason
    )

    return long_control and 35<=rsi<=74


def enable_learning_scout(candidate):

    candidate["Recovery Test Mode"]=True
    candidate["Learning Scout"]=True
    candidate["Position Cash"]=LEARNING_SCOUT_POSITION_CASH
    candidate["Memory Note"]=(
        f"{candidate.get('Memory Note','No memory adjustment')} | "
        f"Learning scout: tiny ${LEARNING_SCOUT_POSITION_CASH:,.0f} trade "
        "allowed to collect data after the AI stayed quiet too long"
    )


def enable_alternate_setup_scout(candidate):

    candidate["Recovery Test Mode"]=True
    candidate["Learning Scout"]=True
    candidate["Alternate Setup Scout"]=True
    candidate["Position Cash"]=ALTERNATE_SETUP_SCOUT_POSITION_CASH
    candidate["Memory Note"]=(
        f"{candidate.get('Memory Note','No memory adjustment')} | "
        f"Alternate setup scout: small ${ALTERNATE_SETUP_SCOUT_POSITION_CASH:,.0f} trade "
        "allowed after quiet time, avoiding the failed crypto LONG ema8_pullback idea while still collecting data"
    )


def enable_brain_exploration(candidate):

    candidate["Recovery Test Mode"]=True
    candidate["Learning Scout"]=True
    candidate["Brain Exploration"]=True
    candidate["Position Cash"]=BRAIN_EXPLORATION_POSITION_CASH
    candidate["Memory Note"]=(
        f"{candidate.get('Memory Note','No memory adjustment')} | "
        f"Brain exploration: tiny ${BRAIN_EXPLORATION_POSITION_CASH:,.0f} trade "
        "allowed only because the AI stayed quiet and needs fresh learning data"
    )


def crypto_market_is_healthy():

    checked=0
    healthy=0

    for ticker in ["BTC-USD","ETH-USD"]:

        try:

            data=yf.download(
                ticker,
                period="1d",
                interval="1m",
                progress=False,
                auto_adjust=True
            )

            if data.empty:
                continue

            data=clean_data(data)
            close=data["Close"].dropna()

            if len(close)<25:
                continue

            checked+=1

            price=float(close.iloc[-1])
            ema8=float(close.ewm(span=8,adjust=False).mean().iloc[-1])
            ema21=float(close.ewm(span=21,adjust=False).mean().iloc[-1])
            short_move=(float(close.iloc[-1])-float(close.iloc[-6]))/float(close.iloc[-6])

            if price>=ema8 and price>=ema21 and short_move>-0.001:
                healthy+=1

        except Exception:

            continue

    if checked==0:
        return True

    return healthy==checked


def crypto_market_is_strong_bullish():

    checked=0
    bullish=0

    for ticker in ["BTC-USD","ETH-USD"]:

        try:

            data=yf.download(
                ticker,
                period="1d",
                interval="1m",
                progress=False,
                auto_adjust=True
            )

            if data.empty:
                continue

            data=clean_data(data)
            close=data["Close"].dropna()
            high=data["High"].dropna()
            low=data["Low"].dropna()
            volume=data["Volume"].dropna() if "Volume" in data.columns else None

            if len(close)<60:
                continue

            checked+=1
            price=float(close.iloc[-1])
            ema3=float(close.ewm(span=3,adjust=False).mean().iloc[-1])
            ema8=float(close.ewm(span=8,adjust=False).mean().iloc[-1])
            ema21=float(close.ewm(span=21,adjust=False).mean().iloc[-1])
            three_min_move=(float(close.iloc[-1])-float(close.iloc[-4]))/float(close.iloc[-4])

            above_vwap=True

            if volume is not None and len(volume)>=60:
                recent_volume=volume.tail(60)
                recent_volume_sum=recent_volume.sum()

                if recent_volume_sum>0:
                    typical_price=(high+low+close)/3
                    vwap=float(
                        (typical_price.tail(60)*recent_volume).sum()/recent_volume_sum
                    )
                    above_vwap=price>vwap

            if price>ema3>ema8>ema21 and above_vwap and three_min_move>0.0005:
                bullish+=1

        except Exception:

            continue

    return checked>=2 and bullish==checked


def crypto_market_is_strong_bearish():

    checked=0
    bearish=0

    for ticker in ["BTC-USD","ETH-USD"]:

        try:

            data=yf.download(
                ticker,
                period="1d",
                interval="1m",
                progress=False,
                auto_adjust=True
            )

            if data.empty:
                continue

            data=clean_data(data)
            close=data["Close"].dropna()
            high=data["High"].dropna()
            low=data["Low"].dropna()
            volume=data["Volume"].dropna() if "Volume" in data.columns else None

            if len(close)<60:
                continue

            checked+=1
            price=float(close.iloc[-1])
            ema3=float(close.ewm(span=3,adjust=False).mean().iloc[-1])
            ema8=float(close.ewm(span=8,adjust=False).mean().iloc[-1])
            ema21=float(close.ewm(span=21,adjust=False).mean().iloc[-1])
            three_min_move=(float(close.iloc[-1])-float(close.iloc[-4]))/float(close.iloc[-4])

            below_vwap=True

            if volume is not None and len(volume)>=60:
                recent_volume=volume.tail(60)
                recent_volume_sum=recent_volume.sum()

                if recent_volume_sum>0:
                    typical_price=(high+low+close)/3
                    vwap=float(
                        (typical_price.tail(60)*recent_volume).sum()/recent_volume_sum
                    )
                    below_vwap=price<vwap

            if price<ema3<ema8<ema21 and below_vwap and three_min_move<-0.0005:
                bearish+=1

        except Exception:

            continue

    return checked>=2 and bearish==checked


def apply_memory_adjustment(cursor,email,candidate):

    direction=candidate.get("Direction","LONG")

    memory=get_ticker_memory(
        cursor,
        email,
        candidate["Ticker"],
        direction
    )

    adjustment=0
    notes=[]
    ticker_recovery_trusted=ticker_memory_is_trusted(
        memory
    )

    if memory["trades"]>=3:

        if memory["win_rate"]>=55 and memory["avg_profit"]>0:

            adjustment=1
            notes.append(f"Ticker boost: {memory['win_rate']:.0f}% win rate over {memory['trades']} trades")

            if ticker_recovery_trusted:
                notes.append("Ticker trusted for tiny recovery tests")

        elif memory["trades"]>=5 and memory["win_rate"]<=25 and memory["avg_profit"]<0:

            adjustment=-1
            notes.append(f"Ticker caution: {memory['win_rate']:.0f}% win rate over {memory['trades']} trades")

        if memory["trades"]>=8 and memory["total_profit"]<=-25:

            adjustment=min(adjustment,-2)
            notes.append(f"Ticker strong caution: ${memory['total_profit']:.2f} total profit over {memory['trades']} trades")

    setup_type=detect_setup_type(
        candidate.get("Reason")
    )

    combo_memory=get_combo_memory(
        cursor,
        email,
        candidate["Ticker"],
        setup_type,
        direction
    )

    setup_memory=get_setup_memory(
        cursor,
        email,
        setup_type,
        candidate.get("Market"),
        direction
    )
    setup_confidence=memory_confidence(
        setup_memory
    )
    ticker_confidence=memory_confidence(
        memory
    )
    brain_memory=best_brain_memory(
        cursor,
        email,
        candidate
    )
    candidate["Brain Memory"]=brain_memory

    block_reason=setup_block_reason(
        cursor,
        email,
        setup_type,
        candidate.get("Market"),
        direction
    )

    ticker_block=ticker_block_reason(
        memory
    )

    combo_block=combo_block_reason(
        combo_memory,
        candidate["Ticker"],
        setup_type,
        direction
    )

    setup_probation=bool(
        setup_memory["trades"]>=BAD_SETUP_MIN_TRADES and
        setup_memory["total_profit"]<0 and
        (
            setup_memory["avg_profit"]<0 or
            (
                setup_memory["win_rate"] is not None and
                setup_memory["win_rate"]<=35
            )
        )
    )

    memory_warning=bool(
        combo_block or
        setup_probation or
        ticker_block
    )
    bad_combo=False

    if setup_memory["trades"]>=4:

        if setup_memory["win_rate"]>=60 and setup_memory["avg_profit"]>0:
            adjustment+=2
            notes.append(f"Setup boost: {setup_type} is working")

        elif setup_memory["win_rate"]<=35 or setup_memory["avg_profit"]<0:
            adjustment-=2
            notes.append(f"Setup caution: {setup_type} has weak memory")

    if (
        direction=="LONG" and
        setup_type=="ema8_pullback"
    ):
        adjustment+=EMA8_PULLBACK_LONG_BOOST
        notes.append(
            f"EMA8 pullback LONG focus: +{EMA8_PULLBACK_LONG_BOOST} because recent sessions showed better profit quality"
        )

    if setup_is_session_winner(
        cursor,
        email,
        setup_type,
        direction
    ):
        adjustment+=2
        notes.append(
            f"Session momentum: {direction} {setup_type} is profitable in this session, allowed to press the edge"
        )

    if setup_is_session_loser(
        cursor,
        email,
        setup_type,
        direction
    ):
        adjustment-=2
        notes.append(
            f"Session defense: {direction} {setup_type} is losing in this session, require stronger proof"
        )

    if setup_confidence=="trusted" and ticker_confidence in ["trusted","normal"]:
        adjustment+=1
        notes.append("Memory confidence: setup/ticker are trusted enough for normal sizing")
    elif "learning" in [setup_confidence,ticker_confidence]:
        adjustment-=1
        notes.append("Memory confidence: learning mode, keep size controlled but do not block the trade")

    if brain_memory["trades"]>=BRAIN_MIN_PATTERN_TRADES:
        if brain_is_good(brain_memory):
            adjustment+=BRAIN_HUNT_SCORE_BOOST
            candidate["Brain Hunting Match"]=True
            match_type="family" if brain_memory.get("family_match") else "exact"
            notes.append(
                f"AI brain boost: historical replay likes this {match_type} pattern "
                f"({brain_memory['win_rate']:.0f}% win rate over {brain_memory['trades']} samples)"
            )
        elif (
            brain_is_bad(brain_memory)
        ):
            adjustment-=2
            notes.append(
                f"AI brain warning: historical replay dislikes this pattern "
                f"({brain_memory['win_rate']:.0f}% win rate over {brain_memory['trades']} samples)"
            )
    else:
        notes.append("AI brain: not enough replay samples yet for this exact pattern")

    if block_reason:
        adjustment-=8
        notes.append(block_reason)

    probation_reason=None

    if memory_warning:
        adjustment-=1
        probation_reason=(
            combo_block or
            (
                f"Setup learning note {setup_type}: "
                f"${setup_memory['avg_profit']:.2f} average profit over {setup_memory['trades']} trades"
                if setup_probation
                else None
            ) or
            f"Ticker learning note: {ticker_block}"
        )
        notes.append(f"Learning note: {probation_reason}")
    elif ticker_block:
        adjustment-=1
        notes.append(f"{direction} {ticker_block}")

    notes.append(
        confidence_note("Ticker",memory)
    )
    notes.append(
        confidence_note("Setup",setup_memory)
    )

    position_cash=position_cash_from_memory(
        memory,
        setup_memory,
        bad_combo or bool(block_reason)
    )

    fresh_setup=is_fresh_intraday_setup(candidate)

    if fresh_setup:
        adjustment+=FRESH_SETUP_SCORE_BOOST
        notes.append(
            f"Fresh 1m setup boost: +{FRESH_SETUP_SCORE_BOOST} because this looks timely, not chased"
        )

    adjusted_score=max(
        0,
        candidate["Score"]+adjustment
    )

    candidate["Adjusted Score"]=adjusted_score
    candidate["Memory Adjustment"]=adjustment
    candidate["Setup Type"]=setup_type
    candidate["Probation Mode"]=False
    candidate["Probation Reason"]=probation_reason
    candidate["Ticker Confidence"]=ticker_confidence
    candidate["Setup Confidence"]=setup_confidence
    candidate["Brain Memory"]=brain_memory
    candidate["Recovery Test Mode"]=False
    candidate["Ticker Recovery Trusted"]=ticker_recovery_trusted
    candidate["Setup Blocked"]=bool(block_reason)
    candidate["Setup Block Reason"]=block_reason or (
        None
    )
    candidate["Position Cash"]=position_cash
    candidate["Memory Note"]=" | ".join(notes) if notes else "No memory adjustment"

    lessons=active_ai_lessons(
        cursor,
        email,
        3
    )

    if lessons:
        candidate["Memory Note"]=(
            f"{candidate['Memory Note']} | AI lesson memory: "+
            " / ".join(lessons)
        )

    return candidate


def todays_closed_profit(cursor,email):

    today=datetime.now().strftime("%Y-%m-%d")

    cursor.execute("""
        SELECT COALESCE(SUM(profit),0)
        FROM trades
        WHERE email=? AND substr(time,1,10)=?
    """,(
        email,
        today
    ))

    return float(cursor.fetchone()[0] or 0)


def get_session_start_time(cursor,email):

    cursor.execute(
        "SELECT session_start_time FROM bot_state WHERE email=?",
        (email,)
    )

    row=cursor.fetchone()

    return row[0] if row and row[0] else None


def session_closed_profit(cursor,email):

    session_start=get_session_start_time(
        cursor,
        email
    )

    if not session_start:
        return 0.0

    cursor.execute("""
        SELECT COALESCE(SUM(profit),0)
        FROM trades
        WHERE email=? AND time>=?
    """,(
        email,
        session_start
    ))

    return float(cursor.fetchone()[0] or 0)


def is_regular_us_market_hours(now=None):

    eastern_now=(now or datetime.now()).astimezone(
        ZoneInfo("America/New_York")
    )

    if eastern_now.weekday()>=5:
        return False

    market_open=dt_time(9,30)
    market_close=dt_time(16,0)

    return market_open<=eastern_now.time()<=market_close


def is_late_us_session(now=None):

    eastern_now=(now or datetime.now()).astimezone(
        ZoneInfo("America/New_York")
    )

    if eastern_now.weekday()>=5:
        return False

    return dt_time(15,30)<=eastern_now.time()<=dt_time(16,0)


def market_is_open_for_new_entries(market,now=None):

    if market=="Crypto":
        return True

    current=now or datetime.now()

    if market=="Stocks":
        return is_regular_us_market_hours(
            current
        )

    if market=="Europe Stocks":
        london_now=current.astimezone(
            ZoneInfo("Europe/London")
        )

        if london_now.weekday()>=5:
            return False

        return dt_time(8,0)<=london_now.time()<=dt_time(16,30)

    if market=="Asia Stocks":
        tokyo_now=current.astimezone(
            ZoneInfo("Asia/Tokyo")
        )

        if tokyo_now.weekday()>=5:
            return False

        return (
            dt_time(9,0)<=tokyo_now.time()<=dt_time(11,30) or
            dt_time(12,30)<=tokyo_now.time()<=dt_time(15,0)
        )

    return True


def is_stock_market(market):

    return market in [
        "Stocks",
        "Europe Stocks",
        "Asia Stocks"
    ]


def one_minute_index_supports_long(symbol):

    try:
        data=yf.download(
            symbol,
            period="1d",
            interval="1m",
            progress=False,
            auto_adjust=True
        )

        if data.empty:
            return None

        data=clean_data(data).dropna()

        if len(data)<25:
            return None

        close=data["Close"].dropna()

        if len(close)<25:
            return None

        latest=float(close.iloc[-1])
        ema8=float(close.ewm(span=8,adjust=False).mean().iloc[-1])
        ema21=float(close.ewm(span=21,adjust=False).mean().iloc[-1])
        move_3m=(latest/float(close.iloc[-4])-1) if len(close)>=4 else 0
        move_10m=(latest/float(close.iloc[-11])-1) if len(close)>=11 else 0

        return (
            latest>=ema8 and
            ema8>=ema21 and
            move_3m>-0.001 and
            move_10m>-0.002
        )

    except Exception:
        return None


def us_stock_market_supports_long(now=None):

    global US_STOCK_MARKET_CONFIRM_CACHE

    current=now or datetime.now()
    cached_time=US_STOCK_MARKET_CONFIRM_CACHE.get("time")

    if (
        cached_time and
        US_STOCK_MARKET_CONFIRM_CACHE.get("value") is not None and
        (current-cached_time).total_seconds()<US_STOCK_MARKET_CONFIRM_CACHE_SECONDS
    ):
        return US_STOCK_MARKET_CONFIRM_CACHE["value"]

    spy=one_minute_index_supports_long("SPY")
    qqq=one_minute_index_supports_long("QQQ")

    if spy is None and qqq is None:
        value=False
    else:
        value=bool(spy) and bool(qqq)

    US_STOCK_MARKET_CONFIRM_CACHE={
        "time":current,
        "value":value
    }

    return value


def stock_long_has_strong_confirmation(candidate):

    reason_text=(candidate.get("Reason") or "").lower()

    return (
        candidate.get("Direction","LONG")=="LONG" and
        candidate.get("Trigger Confirmed") and
        candidate.get("Follow Through Confirmed") and
        "above 1m vwap" in reason_text and
        candidate.get("Adjusted Score",candidate.get("Score",0))>=22 and
        45<=float(candidate.get("RSI") or 0)<=68
    )


def is_late_chase_setup(candidate):

    reason=(candidate.get("Reason") or "").lower()
    direction=candidate.get("Direction","LONG")
    rsi=float(candidate.get("RSI") or 0)

    if direction=="SHORT":
        return (
            (
                "controlled 10m drop" in reason and
                rsi<=35
            ) or
            rsi<=20
        )

    return (
        (
            "controlled 10m move" in reason and
            rsi>=66
        ) or
        rsi>=76
    )


def is_fresh_intraday_setup(candidate):

    reason=(candidate.get("Reason") or "").lower()
    direction=candidate.get("Direction","LONG")
    trigger_age=candidate.get("Trigger Age Seconds")

    if trigger_age is not None and trigger_age>180:
        return False

    if is_late_chase_setup(candidate):
        return False

    if not candidate.get("Follow Through Confirmed"):
        return False

    if direction=="SHORT":
        return (
            "price holding below trigger" in reason and
            "below 1m vwap" in reason
        )

    return (
        "price holding above trigger" in reason and
        "above 1m vwap" in reason
    )


def has_direction_control(candidate):

    reason=(candidate.get("Reason") or "").lower()
    direction=candidate.get("Direction","LONG")

    if direction=="SHORT":
        return (
            "price holding below trigger" in reason and
            "below 1m vwap" in reason
        )

    return (
        "price holding above trigger" in reason and
        "above 1m vwap" in reason
    )


def is_weak_breakout_family(candidate):

    return candidate.get("Setup Type") in {
        "strong_continuation",
        "bullish_trigger",
        "bearish_trigger"
    }


def is_preferred_entry_family(candidate):

    return candidate.get("Setup Type") in {
        "vwap_momentum",
        "ema8_pullback"
    }


def active_learning_candidate(candidate):

    direction=candidate.get("Direction","LONG")
    rsi=float(candidate.get("RSI") or 0)

    if candidate.get("Opportunity Score",0)<ACTIVE_LEARNING_MIN_OPPORTUNITY:
        return False

    if candidate.get("Setup Blocked"):
        return False

    if not has_direction_control(candidate):
        return False

    if is_late_chase_setup(candidate):
        return False

    if direction=="LONG":
        return 32<=rsi<=82

    return 24<=rsi<=66


def direct_order_candidate(candidate):

    direction=candidate.get("Direction","LONG")
    rsi=float(candidate.get("RSI") or 0)

    if candidate.get("Opportunity Score") is None:
        return False

    if direction=="LONG":
        return 15<=rsi<=92

    return 8<=rsi<=85


def opportunity_score(candidate):

    reason=(candidate.get("Reason") or "").lower()
    direction=candidate.get("Direction","LONG")
    score=float(candidate.get("Adjusted Score",candidate.get("Score",0)) or 0)
    rsi=float(candidate.get("RSI") or 0)
    memory=candidate.get("Brain Memory") or {}

    points=score

    if candidate.get("Follow Through Confirmed"):
        points+=4
    if candidate.get("Continuation Confirmed"):
        points+=4
    if is_fresh_intraday_setup(candidate):
        points+=5
    if "trigger volume surge" in reason:
        points+=3
    if "price holding above trigger" in reason and direction=="LONG":
        points+=3
    if "price holding below trigger" in reason and direction=="SHORT":
        points+=3
    if "above 1m vwap" in reason and direction=="LONG":
        points+=3
    if "below 1m vwap" in reason and direction=="SHORT":
        points+=3
    if "1m ema8 pullback held" in reason or "1m ema8 pullback rejected" in reason:
        points+=2
    if "clean 1m trend strength" in reason or "clean 1m downtrend strength" in reason:
        points+=2
    if brain_is_good(memory):
        points+=4

    if is_late_chase_setup(candidate):
        points-=8
    if brain_is_bad(memory):
        points-=4
    if brain_is_hard_wait(memory):
        points-=10
    if candidate.get("Crypto Market Caution"):
        points-=2
    if direction=="LONG" and not (38<=rsi<=72):
        points-=3
    if direction=="SHORT" and not (28<=rsi<=62):
        points-=3

    return round(points,2)


def day_trader_knowledge_grade(candidate):

    reason=(candidate.get("Reason") or "").lower()
    direction=candidate.get("Direction","LONG")
    market=candidate.get("Market")
    score=float(candidate.get("Adjusted Score",candidate.get("Score",0)) or 0)
    opp_score=float(candidate.get("Opportunity Score",0) or 0)
    rsi=float(candidate.get("RSI") or 0)
    setup_confidence=candidate.get("Setup Confidence","new")
    ticker_confidence=candidate.get("Ticker Confidence","new")
    brain_memory=candidate.get("Brain Memory") or {}

    positives=[]
    risks=[]

    if "above 1m vwap" in reason and direction=="LONG":
        positives.append("price is above VWAP, so buyers have intraday control")
    if "below 1m vwap" in reason and direction=="SHORT":
        positives.append("price is below VWAP, so sellers have intraday control")
    if candidate.get("Follow Through Confirmed"):
        positives.append("the next candle confirmed follow-through")
    if candidate.get("Continuation Confirmed"):
        positives.append("the move has continuation instead of only one candle")
    if "price holding above trigger" in reason and direction=="LONG":
        positives.append("price is holding above the trigger")
    if "price holding below trigger" in reason and direction=="SHORT":
        positives.append("price is holding below the trigger")
    if "trigger volume surge" in reason:
        positives.append("trigger volume expanded")

    if direction=="SHORT" and rsi<=35:
        risks.append("short may be late because RSI is already low")
    if direction=="SHORT" and candidate.get("Setup Type")=="bearish_trigger":
        risks.append("bearish-trigger shorts have been the main recent loser, so this needs extra proof")
    if direction=="LONG" and rsi>=72:
        risks.append("long may be late because RSI is already high")
    if "controlled 10m drop" in reason and direction=="SHORT" and rsi<=38:
        risks.append("price already dropped for 10 minutes, so bounce risk is high")
    if "controlled 10m move" in reason and direction=="LONG" and rsi>=68:
        risks.append("price already moved for 10 minutes, so pullback risk is high")
    if "near 1m support" in reason and direction=="SHORT":
        risks.append("short is close to support")
    if "near 1m resistance" in reason and direction=="LONG":
        risks.append("long is close to resistance")
    if candidate.get("Crypto Long Defense") or candidate.get("Crypto Short Defense"):
        risks.append("BTC/ETH are not clearly supporting this direction")
    if candidate.get("Crypto Market Caution"):
        risks.append("crypto market is mixed or weak")
    if setup_confidence=="learning":
        risks.append("setup memory says to use controlled size")
    if ticker_confidence=="learning":
        risks.append("ticker memory says to use controlled size")

    grade_points=0
    grade_points+=2 if score>=MIN_KNOWLEDGE_A_SCORE else 1 if score>=MIN_KNOWLEDGE_B_SCORE else 0
    grade_points+=2 if candidate.get("Follow Through Confirmed") else 0
    grade_points+=1 if candidate.get("Continuation Confirmed") else 0
    grade_points+=1 if (
        ("above 1m vwap" in reason and direction=="LONG") or
        ("below 1m vwap" in reason and direction=="SHORT")
    ) else 0
    grade_points-=1 if "learning" in [setup_confidence,ticker_confidence] else 0
    grade_points-=1 if candidate.get("Crypto Long Defense") or candidate.get("Crypto Short Defense") else 0
    grade_points-=1 if direction=="SHORT" and rsi<=35 else 0
    grade_points-=1 if direction=="LONG" and rsi>=72 else 0
    grade_points-=1 if direction=="SHORT" and candidate.get("Setup Type")=="bearish_trigger" else 0
    grade_points+=1 if direction=="LONG" and candidate.get("Setup Type")=="ema8_pullback" else 0

    if (
        direction=="SHORT" and
        setup_confidence=="learning" and
        rsi<=35 and
        not candidate.get("Follow Through Confirmed")
    ):
        grade="D"
    elif (
        opp_score>=OPPORTUNITY_NORMAL_MIN_SCORE and
        is_fresh_intraday_setup(candidate) and
        candidate.get("Follow Through Confirmed") and
        candidate.get("Continuation Confirmed") and
        not is_late_chase_setup(candidate) and
        not brain_is_hard_wait(brain_memory) and
        len(risks)<=4
    ):
        grade="B"
    elif (
        opp_score>=OPPORTUNITY_RESCUE_MIN_SCORE and
        has_direction_control(candidate) and
        not is_late_chase_setup(candidate) and
        not brain_is_hard_wait(brain_memory) and
        len(risks)<=5
    ):
        grade="C"
    elif active_learning_candidate(candidate) and len(risks)<=6:
        grade="C"
    elif grade_points>=5 and not risks:
        grade="A"
    elif grade_points>=4 and len(risks)<=1:
        grade="B"
    elif grade_points>=2 and len(risks)<=3:
        grade="C"
    else:
        grade="D"

    if grade=="D":
        action="skip"
    elif grade=="C":
        action="tiny test only"
    elif grade=="B":
        action="small controlled trade"
    else:
        action="normal confident trade"

    note=(
        f"Day-trader knowledge grade {grade}: {action}. "
        f"Good: {', '.join(positives) if positives else 'not enough clean confirmation'}. "
        f"Risk: {', '.join(risks) if risks else 'no major warning'}."
    )

    return grade,note


def quality_gate(candidate,now):

    rsi=candidate.get("RSI")

    if rsi is None:
        return False,"Missing RSI"

    if candidate.get("Direct Order Trade") and direct_order_candidate(candidate):
        candidate["Opportunity Rescue"]=True
        candidate["Active Learning Trade"]=True
        return True,"Passed direct order gate; controlled paper-risk trade required after idle time"

    if rsi<MIN_ENTRY_RSI:
        return False,f"RSI below entry range ({rsi} < {MIN_ENTRY_RSI})"

    if rsi>MAX_ENTRY_RSI:
        return False,f"RSI above entry range ({rsi} > {MAX_ENTRY_RSI})"

    if candidate.get("Market")=="Europe Stocks":
        if candidate.get("Opportunity Score",0)<EUROPE_STOCK_MIN_OPPORTUNITY:
            return False,f"Europe stock filter: opportunity below {EUROPE_STOCK_MIN_OPPORTUNITY}"
        if not (EUROPE_STOCK_MIN_RSI<=rsi<=EUROPE_STOCK_MAX_RSI):
            return False,(
                f"Europe stock filter: RSI must be {EUROPE_STOCK_MIN_RSI}-{EUROPE_STOCK_MAX_RSI}, "
                f"got {rsi}"
            )
        if not candidate.get("Follow Through Confirmed"):
            return False,"Europe stock filter: requires next 1m follow-through confirmation"

    if candidate.get("Market")=="Asia Stocks":
        if candidate.get("Opportunity Score",0)<ASIA_STOCK_MIN_OPPORTUNITY:
            return False,f"Asia stock filter: opportunity below {ASIA_STOCK_MIN_OPPORTUNITY}"
        if not (ASIA_STOCK_MIN_RSI<=rsi<=ASIA_STOCK_MAX_RSI):
            return False,(
                f"Asia stock filter: RSI must be {ASIA_STOCK_MIN_RSI}-{ASIA_STOCK_MAX_RSI}, "
                f"got {rsi}"
            )
        if not has_direction_control(candidate):
            return False,"Asia stock filter: requires clean 1m direction control before entry"

    if is_late_chase_setup(candidate):
        return False,"Anti-chase gate: setup is too late after the 1m move; waiting for an earlier entry"

    if (
        candidate.get("Direction","LONG")=="LONG" and
        candidate.get("Setup Type")=="ema8_pullback" and
        rsi>64 and
        not (
            candidate.get("Follow Through Confirmed") and
            candidate.get("Opportunity Score",0)>=38
        )
    ):
        return False,"EMA8 pullback anti-chase gate: RSI above 64 needs stronger follow-through before entry"

    if (
        candidate.get("Direction","LONG")=="LONG" and
        candidate.get("Setup Type") in {"strong_continuation","bullish_trigger"} and
        rsi>70
    ):
        return False,"Breakout anti-chase gate: LONG continuation/trigger with RSI above 70 is too stretched"

    if (
        candidate.get("Direction","LONG")=="SHORT" and
        candidate.get("Setup Type")=="bearish_trigger" and
        rsi<30
    ):
        return False,"Breakout anti-chase gate: SHORT bearish trigger with RSI below 30 is too stretched"

    if candidate["Market"]=="Stocks" and not is_regular_us_market_hours(now):
        return False,"Stock trade skipped outside regular US market hours"

    if candidate["Market"]=="Stocks" and is_late_us_session(now):
        return False,"US stock trade skipped in final 30 minutes of regular session"

    if (
        candidate["Market"]=="Stocks" and
        candidate.get("Direction","LONG")=="LONG" and
        not us_stock_market_supports_long(now)
    ):
        return False,"US stock market filter: SPY and QQQ are not both supporting LONG entries"

    if candidate.get("Learning Scout"):
        return True,"Passed learning scout gate: tiny controlled trade for data collection"

    if (
        is_stock_market(candidate.get("Market")) and
        candidate.get("Direction","LONG")=="LONG" and
        not candidate.get("Recovery Test Mode") and
        not stock_long_has_strong_confirmation(candidate)
    ):
        return False,"Stock LONG requires stronger trigger, follow-through, VWAP, and RSI confirmation"

    if candidate.get("Direction","LONG")=="SHORT":
        if (
            not candidate.get("Recovery Test Mode") and
            candidate.get("Adjusted Score",candidate.get("Score",0))<MIN_SHORT_ADJUSTED_SCORE
        ):
            return False,f"Short adjusted score below minimum {MIN_SHORT_ADJUSTED_SCORE}"

        if not candidate.get("Trigger Confirmed") and not qualifies_for_crypto_short_test(candidate):
            return False,"Short trade requires confirmed bearish 1m trigger"

        reason_text=(candidate.get("Reason") or "").lower()

        high_confidence_short=(
            candidate.get("Adjusted Score",candidate.get("Score",0))>=18 and
            (candidate.get("Trigger Confirmed") or candidate.get("Continuation Confirmed"))
        )
        if (
            "below 1m vwap" not in reason_text and
            not candidate.get("Recovery Test Mode") and
            not high_confidence_short
        ):
            return False,"Short trade requires price below 1m VWAP (or score>=18 with trigger)"

    strong_continuation=(
        candidate.get("Continuation Confirmed") and
        candidate.get("Adjusted Score",candidate.get("Score",0))>=MIN_SCORE_TO_TRADE+2
    )

    if not candidate.get("Trigger Confirmed") and not strong_continuation:
        if candidate.get("Direct Order Trade") and direct_order_candidate(candidate):
            candidate["Opportunity Rescue"]=True
            candidate["Active Learning Trade"]=True
            return True,"Passed direct order gate; entering controlled paper-risk trade"

        if active_learning_candidate(candidate):
            candidate["Opportunity Rescue"]=True
            candidate["Active Learning Trade"]=True
            return True,"Passed active learning watch gate; waiting for 30s confirmation"

        if (
            candidate.get("Opportunity Score",0)>=OPPORTUNITY_RESCUE_MIN_SCORE and
            has_direction_control(candidate) and
            not is_late_chase_setup(candidate) and
            not brain_is_hard_wait(candidate.get("Brain Memory") or {})
        ):
            candidate["Opportunity Rescue"]=True
            return True,"Passed opportunity watch gate; waiting for 30s confirmation"

        return False,"No confirmed 1m trigger or strong continuation setup"

    trigger_age=candidate.get("Trigger Age Seconds")

    if trigger_age is None and not qualifies_for_crypto_short_test(candidate):
        return False,"Missing 1m trigger candle time"

    if trigger_age is not None and trigger_age>MAX_TRIGGER_AGE_SECONDS and not qualifies_for_crypto_short_test(candidate):
        return False,f"1m trigger candle is stale ({int(trigger_age)} seconds old)"

    if (
        candidate.get("Recovery Test Mode") and
        not qualifies_for_crypto_short_test(candidate) and
        not candidate.get("Follow Through Confirmed")
    ):
        return False,"Recovery test requires next 1m candle follow-through"

    if strong_continuation and not candidate.get("Trigger Confirmed"):
        return True,"Passed quality gate as strong 1m continuation"

    if candidate.get("Recovery Test Mode"):
        return True,"Passed recovery test gate with next 1m candle follow-through"

    return True,"Passed quality gate"


def ticker_in_loss_cooldown(cursor,email,ticker,now,direction=None):

    direction_filter=""
    params=[
        email,
        ticker
    ]

    if direction:
        direction_filter=" AND COALESCE(direction,'LONG')=?"
        params.append(direction)

    cursor.execute("""
        SELECT exit_time,profit
        FROM trades
        WHERE email=? AND ticker=? AND profit<0 AND exit_time IS NOT NULL
    """+direction_filter+"""
        ORDER BY id DESC
        LIMIT 1
    """,params)

    row=cursor.fetchone()

    if not row:
        return False,None

    try:

        exit_time=datetime.strptime(
            row[0],
            "%Y-%m-%d %H:%M:%S"
        )

    except Exception:

        return False,None

    minutes_since_loss=(now-exit_time).total_seconds()/60

    if minutes_since_loss<COOLDOWN_AFTER_LOSS_MINUTES:
        remaining=round(COOLDOWN_AFTER_LOSS_MINUTES-minutes_since_loss,1)
        return True,f"Loss cooldown active for {remaining} more minutes"

    return False,None


def same_trade_recently_opened(cursor,email,ticker,direction,now):

    cursor.execute("""
        SELECT time
        FROM trades
        WHERE email=?
          AND ticker=?
          AND COALESCE(direction,'LONG')=?
        ORDER BY id DESC
        LIMIT 1
    """,(
        email,
        ticker,
        direction
    ))

    row=cursor.fetchone()

    if not row:
        return False,None

    try:
        trade_time=datetime.strptime(row[0],"%Y-%m-%d %H:%M:%S")
    except Exception:
        return False,None

    minutes_since=(now-trade_time).total_seconds()/60

    if minutes_since<SAME_TRADE_COOLDOWN_MINUTES:
        remaining=round(SAME_TRADE_COOLDOWN_MINUTES-minutes_since,1)
        return True,f"Same ticker/direction cooldown active for {remaining} more minutes"

    return False,None


def probation_in_cooldown(cursor,email,ticker,setup_type,direction,now):

    cursor.execute("""
        SELECT exit_time,profit
        FROM trades
        WHERE email=?
          AND ticker=?
          AND setup_type=?
          AND COALESCE(direction,'LONG')=?
          AND exit_time IS NOT NULL
        ORDER BY id DESC
        LIMIT 1
    """,(
        email,
        ticker,
        setup_type,
        direction
    ))

    row=cursor.fetchone()

    if not row:
        return False,None

    try:
        exit_time=datetime.strptime(row[0],"%Y-%m-%d %H:%M:%S")
    except Exception:
        return False,None

    minutes_since=(now-exit_time).total_seconds()/60

    if minutes_since<PROBATION_COOLDOWN_MINUTES:
        remaining=round(PROBATION_COOLDOWN_MINUTES-minutes_since,1)
        return True,f"Probation cooldown active for {remaining} more minutes"

    return False,None


def latest_session_start(cursor,email):

    session_start=get_session_start_time(
        cursor,
        email
    )

    return session_start or datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def session_early_failure_pause(cursor,email,now):

    session_start=latest_session_start(
        cursor,
        email
    )
    lookback_start=(
        now-timedelta(
            minutes=SESSION_EARLY_FAILURE_LOOKBACK_MINUTES
        )
    ).strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        SELECT exit_time
        FROM trades
        WHERE email=?
          AND time>=?
          AND exit_time>=?
          AND reason LIKE 'Early failure%'
        ORDER BY id DESC
    """,(
        email,
        session_start,
        lookback_start
    ))

    rows=cursor.fetchall()

    if len(rows)<SESSION_EARLY_FAILURE_PAUSE_COUNT:
        return False,None

    try:
        last_failure=datetime.strptime(
            rows[0][0],
            "%Y-%m-%d %H:%M:%S"
        )
    except Exception:
        return False,None

    minutes_since=(now-last_failure).total_seconds()/60

    if minutes_since<SESSION_EARLY_FAILURE_PAUSE_MINUTES:
        remaining=max(
            0,
            round(SESSION_EARLY_FAILURE_PAUSE_MINUTES-minutes_since,1)
        )
        return True,(
            f"Session mistake pause active for {remaining} more minutes "
            f"after {len(rows)} early-failure trade(s) in the last "
            f"{SESSION_EARLY_FAILURE_LOOKBACK_MINUTES} minutes"
        )

    return False,None


def ticker_early_failure_cooldown(cursor,email,ticker,now):

    session_start=latest_session_start(
        cursor,
        email
    )

    cursor.execute("""
        SELECT exit_time
        FROM trades
        WHERE email=?
          AND ticker=?
          AND time>=?
          AND reason LIKE 'Early failure%'
        ORDER BY id DESC
        LIMIT 1
    """,(
        email,
        ticker,
        session_start
    ))

    row=cursor.fetchone()

    if not row:
        return False,None

    try:
        exit_time=datetime.strptime(
            row[0],
            "%Y-%m-%d %H:%M:%S"
        )
    except Exception:
        return False,None

    minutes_since=(now-exit_time).total_seconds()/60

    if minutes_since<TICKER_EARLY_FAILURE_COOLDOWN_MINUTES:
        remaining=round(TICKER_EARLY_FAILURE_COOLDOWN_MINUTES-minutes_since,1)
        return True,f"{ticker} early-failure cooldown active for {remaining} more minutes"

    return False,None


def ticker_direction_session_early_failures(cursor,email,ticker,direction):

    session_start=latest_session_start(
        cursor,
        email
    )

    cursor.execute("""
        SELECT COUNT(*)
        FROM trades
        WHERE email=?
          AND ticker=?
          AND COALESCE(direction,'LONG')=?
          AND time>=?
          AND reason LIKE 'Early failure%'
    """,(
        email,
        ticker,
        direction,
        session_start
    ))

    return int(cursor.fetchone()[0] or 0)


def ticker_setup_direction_session_early_failures(cursor,email,ticker,setup_type,direction):

    session_start=latest_session_start(
        cursor,
        email
    )

    cursor.execute("""
        SELECT COUNT(*)
        FROM trades
        WHERE email=?
          AND ticker=?
          AND setup_type=?
          AND COALESCE(direction,'LONG')=?
          AND time>=?
          AND reason LIKE 'Early failure%'
    """,(
        email,
        ticker,
        setup_type,
        direction,
        session_start
    ))

    return int(cursor.fetchone()[0] or 0)


def setup_direction_early_failure_count(cursor,email,setup_type,direction):

    session_start=latest_session_start(
        cursor,
        email
    )
    lookback_start=(
        datetime.now()-timedelta(
            minutes=SESSION_EARLY_FAILURE_LOOKBACK_MINUTES
        )
    ).strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        SELECT COUNT(*)
        FROM trades
        WHERE email=?
          AND time>=?
          AND exit_time>=?
          AND setup_type=?
          AND COALESCE(direction,'LONG')=?
          AND reason LIKE 'Early failure%'
    """,(
        email,
        session_start,
        lookback_start,
        setup_type,
        direction
    ))

    return int(cursor.fetchone()[0] or 0)


def session_loss_stats(cursor,email,where_sql="",params=()):

    session_start=latest_session_start(
        cursor,
        email
    )

    cursor.execute(f"""
        SELECT
            COUNT(*),
            COALESCE(SUM(profit),0)
        FROM trades
        WHERE email=?
          AND time>=?
          AND profit<0
          {where_sql}
    """,(
        email,
        session_start,
        *params
    ))

    row=cursor.fetchone()

    return int(row[0] or 0),float(row[1] or 0)


def session_setup_direction_stats(cursor,email,setup_type,direction):

    session_start=latest_session_start(
        cursor,
        email
    )

    cursor.execute("""
        SELECT
            COUNT(*),
            COALESCE(SUM(CASE WHEN profit>0 THEN 1 ELSE 0 END),0),
            COALESCE(SUM(profit),0)
        FROM trades
        WHERE email=?
          AND time>=?
          AND setup_type=?
          AND COALESCE(direction,'LONG')=?
    """,(
        email,
        session_start,
        setup_type,
        direction
    ))

    row=cursor.fetchone()

    return {
        "Trades":int(row[0] or 0),
        "Wins":int(row[1] or 0),
        "Profit":float(row[2] or 0)
    }


def session_brain_filter(cursor,email,candidate,session_profit):

    ticker=candidate["Ticker"]
    direction=candidate.get("Direction","LONG")
    setup_type=candidate.get("Setup Type") or "unknown"
    notes=[]
    extra_min_score=0
    max_cash=None

    if session_profit<=SESSION_BRAIN_HARD_STOP_LOSS:
        return {
            "Blocked":True,
            "Reason":(
                f"Session brain stopped new entries because session P/L is ${session_profit:.2f}. "
                "The AI needs to review this session before risking more."
            ),
            "Max Cash":None,
            "Extra Min Score":0
        }

    ticker_losses,ticker_loss_profit=session_loss_stats(
        cursor,
        email,
        "AND ticker=? AND COALESCE(direction,'LONG')=?",
        (
            ticker,
            direction
        )
    )

    if ticker_losses>=SESSION_BRAIN_TICKER_DIRECTION_LOSS_LIMIT:
        extra_min_score+=SESSION_BRAIN_REPEAT_LOSS_EXTRA_SCORE
        max_cash=SESSION_BRAIN_DEFENSE_MAX_CASH
        notes.append(
            f"Session repeat caution: {ticker} {direction} lost {ticker_losses}x this session "
            f"(${ticker_loss_profit:.2f}); score +{SESSION_BRAIN_REPEAT_LOSS_EXTRA_SCORE} required, "
            f"size capped at ${SESSION_BRAIN_DEFENSE_MAX_CASH:,.0f}"
        )

    setup_losses,setup_loss_profit=session_loss_stats(
        cursor,
        email,
        "AND setup_type=? AND COALESCE(direction,'LONG')=?",
        (
            setup_type,
            direction
        )
    )
    setup_stats=session_setup_direction_stats(
        cursor,
        email,
        setup_type,
        direction
    )

    if (
        setup_losses>=SESSION_BRAIN_SETUP_DIRECTION_LOSS_LIMIT and
        setup_stats["Profit"]<0 and
        not setup_is_session_winner(cursor,email,setup_type,direction)
    ):
        return {
            "Blocked":True,
            "Reason":(
                f"Session brain: {direction} {setup_type} has {setup_losses} losing trade(s) "
                f"this session (${setup_loss_profit:.2f}), so I am pausing this setup."
            ),
            "Max Cash":None,
            "Extra Min Score":0
        }

    if setup_losses>0 and setup_stats["Profit"]<0:
        extra_min_score+=SESSION_BRAIN_REPEAT_LOSS_EXTRA_SCORE
        max_cash=SESSION_BRAIN_DEFENSE_MAX_CASH
        notes.append(
            f"Session brain caution: {direction} {setup_type} is losing this session; "
            f"minimum score +{SESSION_BRAIN_REPEAT_LOSS_EXTRA_SCORE}, size capped"
        )

    if session_profit<=SESSION_BRAIN_DEFENSE_LOSS:
        extra_min_score+=SESSION_BRAIN_DEFENSE_EXTRA_SCORE
        max_cash=min(
            max_cash or SESSION_BRAIN_DEFENSE_MAX_CASH,
            SESSION_BRAIN_DEFENSE_MAX_CASH
        )
        notes.append(
            f"Defense mode: session P/L is ${session_profit:.2f}; "
            f"minimum score +{SESSION_BRAIN_DEFENSE_EXTRA_SCORE}, size capped"
        )

    return {
        "Blocked":False,
        "Reason":" | ".join(notes),
        "Max Cash":max_cash,
        "Extra Min Score":extra_min_score
    }


def run_once(cursor,conn,email,scan_for_new=True,searching_enabled=True):

    now=datetime.now()
    opened_count=0
    closed_count=0
    skipped_no_price=0

    cleanup_pending_setups(
        cursor,
        conn,
        email,
        now
    )

    positions=load_open_positions(
        cursor,
        email
    )

    for pos in positions:

        current=latest_price(
            pos["Ticker"]
        )

        if not current:
            continue

        effective_tp=round_market_price(
            pos["Entry"]*(1-TAKE_PROFIT_PCT)
            if pos.get("Direction","LONG")=="SHORT"
            else pos["Entry"]*(1+TAKE_PROFIT_PCT)
        )

        effective_sl=round_market_price(
            pos["Entry"]*(1+STOP_LOSS_PCT)
            if pos.get("Direction","LONG")=="SHORT"
            else pos["Entry"]*(1-STOP_LOSS_PCT)
        )

        entry_time=datetime.strptime(
            pos["Entry Time"],
            "%Y-%m-%d %H:%M:%S"
        )

        hold_minutes=(now-entry_time).total_seconds()/60

        profit_hold=now-entry_time>=timedelta(
            minutes=PROFIT_EXIT_MINUTES
        )

        profit_lock_hold=now-entry_time>=timedelta(
            minutes=PROFIT_LOCK_MINUTES
        )

        flat_exit_hold=now-entry_time>=timedelta(
            minutes=FLAT_EXIT_MINUTES
        )

        force_exit_hold=now-entry_time>=timedelta(
            minutes=FORCE_EXIT_MINUTES
        )

        stale_hold=now-entry_time>=timedelta(
            minutes=STALE_POSITION_MINUTES
        )

        early_failure_hold=now-entry_time>=timedelta(
            minutes=EARLY_FAILURE_MINUTES
        )

        direction=pos.get("Direction","LONG")

        if direction=="SHORT":
            profit_pct=(pos["Entry"]-current)/pos["Entry"]
        else:
            profit_pct=(current-pos["Entry"])/pos["Entry"]

        current_exit_fill=exit_fill_for_direction(
            direction,
            current
        )
        current_net_profit=profit_for_direction(
            direction,
            pos["Entry"],
            current_exit_fill,
            pos["Qty"],
            pos.get("Ticker")
        )

        exit_reason=None

        if direction=="SHORT":
            if current<=effective_tp:
                exit_reason="Take profit reached"
            elif current>=effective_sl:
                exit_reason="Stop loss reached"
        else:
            if current>=effective_tp:
                exit_reason="Take profit reached"
            elif current<=effective_sl:
                exit_reason="Stop loss reached"

        if exit_reason is None and early_failure_hold and profit_pct<=EARLY_FAILURE_MAX_LOSS_PCT:
            exit_reason=(
                f"Early failure exit after {EARLY_FAILURE_MINUTES} minutes"
            )
        elif (
            exit_reason is None and
            profit_hold and
            profit_pct>=PROFIT_EXIT_MIN_PCT and
            current_net_profit>0
        ):
            exit_reason=(
                f"Momentum profit exit after {PROFIT_EXIT_MINUTES} minutes "
                f"with positive net profit after fees"
            )
        elif (
            exit_reason is None and
            profit_lock_hold and
            profit_pct>=PROFIT_LOCK_MIN_PCT and
            current_net_profit>0
        ):
            exit_reason=(
                f"Profit lock exit after {PROFIT_LOCK_MINUTES} minutes "
                f"with positive net profit after fees"
            )
        elif exit_reason is None and flat_exit_hold and abs(profit_pct)<=FLAT_EXIT_MAX_ABS_PCT:
            exit_reason=(
                f"Flat day-trade exit after {FLAT_EXIT_MINUTES} minutes"
            )
        elif exit_reason is None and force_exit_hold:
            exit_reason=(
                f"Forced day-trade exit after {FORCE_EXIT_MINUTES} minutes"
            )
        elif exit_reason is None and stale_hold:
            exit_reason=(
                f"Stale safety exit after {hold_minutes:.1f} minutes"
            )

        if exit_reason:

            exit_fill=current_exit_fill

            fees=estimated_fees(
                pos["Entry"],
                exit_fill,
                pos["Qty"],
                pos.get("Ticker")
            )

            profit=profit_for_direction(
                pos.get("Direction","LONG"),
                pos["Entry"],
                exit_fill,
                pos["Qty"],
                pos.get("Ticker")
            )

            trade={
                "Time":now.strftime("%Y-%m-%d %H:%M:%S"),
                "Ticker":pos["Ticker"],
                "Entry":pos["Entry"],
                "Exit":exit_fill,
                "Profit":profit,
                "Entry Time":pos["Entry Time"],
                "Exit Time":now.strftime("%Y-%m-%d %H:%M:%S"),
                "Reason":f"{exit_reason} | estimated slippage/fees included",
                "Market":pos.get("Market"),
                "Score":pos.get("Score"),
                "RSI":pos.get("RSI"),
                "Direction":pos.get("Direction","LONG"),
                "Entry Reason":pos.get("Entry Reason"),
                "Trigger Time":pos.get("Trigger Time"),
                "Trigger High":pos.get("Trigger High"),
                "Trigger Close":pos.get("Trigger Close")
            }

            save_closed_trade(
                cursor,
                conn,
                email,
                trade
            )

            log_trade_close(
                cursor,
                conn,
                email,
                trade
            )

            delete_open_position(
                cursor,
                conn,
                pos["ID"]
            )

            closed_count+=1

    positions=load_open_positions(
        cursor,
        email
    )

    today_profit=todays_closed_profit(
        cursor,
        email
    )

    session_profit=session_closed_profit(
        cursor,
        email
    )

    if session_profit<=-DAILY_LOSS_LIMIT:

        update_bot_state(
            cursor,
            conn,
            email,
            (
                f"AI safety stop is active. Session P/L is ${session_profit:.2f}, "
                f"which reached the ${DAILY_LOSS_LIMIT:.0f} session loss limit. "
                "No new trades will open today."
            ),
            True,
            open_positions_count=len(positions),
            today_profit=today_profit
        )

        return

    if not searching_enabled:

        status=(
            f"AI search is paused. Checked open positions at {now.strftime('%H:%M:%S')}. "
            f"Closed {closed_count} trade(s). No new trades will open until search is resumed."
        )

        update_bot_state(
            cursor,
            conn,
            email,
            status,
            True,
            open_positions_count=len(load_open_positions(cursor,email)),
            today_profit=today_profit
        )

        return

    if not scan_for_new:

        status=(
            f"AI checked open positions at {now.strftime('%H:%M:%S')}. "
            f"Closed {closed_count} trade(s). Waiting for next scan."
        )

        update_bot_state(
            cursor,
            conn,
            email,
            status,
            True,
            open_positions_count=len(positions),
            today_profit=today_profit
        )

        return

    pause_active,pause_reason=session_early_failure_pause(
        cursor,
        email,
        now
    )

    if pause_active:

        update_bot_state(
            cursor,
            conn,
            email,
            (
                f"AI paused new entries at {now.strftime('%H:%M:%S')}. "
                f"{pause_reason}."
            ),
            True,
            open_positions_count=len(positions),
            today_profit=today_profit
        )

        return

    scan_started_text=now.strftime("%Y-%m-%d %H:%M:%S")

    open_tickers=[
        p["Ticker"]
        for p in positions
    ]

    slots=MAX_OPEN_POSITIONS-len(positions)
    crypto_positions=sum(
        1
        for p in positions
        if p.get("Market")=="Crypto"
    )
    mixed_market_scout_positions=sum(
        1
        for p in positions
        if "mixed market scout" in (p.get("Entry Reason") or "").lower()
    )
    learning_scout_available=(
        len(positions)==0 and
        minutes_since_last_trade(cursor,email,now)>=LEARNING_SCOUT_AFTER_IDLE_MINUTES and
        minutes_since_last_learning_scout(cursor,email,now)>=LEARNING_SCOUT_COOLDOWN_MINUTES
    )
    alternate_setup_scout_available=(
        len(positions)==0 and
        minutes_since_last_trade(cursor,email,now)>=ALTERNATE_SETUP_SCOUT_AFTER_IDLE_MINUTES and
        minutes_since_last_alternate_scout(cursor,email,now)>=ALTERNATE_SETUP_SCOUT_COOLDOWN_MINUTES
    )
    direct_order_trade_due=(
        False
    )
    crypto_healthy=crypto_market_is_healthy()
    crypto_strong_bullish=crypto_market_is_strong_bullish()
    crypto_strong_bearish=crypto_market_is_strong_bearish()
    new_trades_this_scan=0

    all_candidates=[]

    for market,symbols in WATCHLISTS.items():

        if not market_is_open_for_new_entries(
            market,
            now
        ):
            continue

        for candidate in scan(symbols):

            candidate["Market"]=market
            candidate=apply_memory_adjustment(
                cursor,
                email,
                candidate
            )

            if market=="Crypto" and not crypto_healthy:
                candidate["Adjusted Score"]=max(
                    0,
                    candidate["Adjusted Score"]-CRYPTO_MARKET_WEAK_PENALTY
                )
                candidate["Crypto Market Caution"]=True
                candidate["Memory Note"]=(
                    f"{candidate['Memory Note']} | "
                    f"Crypto market caution: -{CRYPTO_MARKET_WEAK_PENALTY} score"
                )
            else:
                candidate["Crypto Market Caution"]=False

            if (
                market=="Crypto" and
                candidate.get("Direction","LONG")=="LONG" and
                not crypto_strong_bullish
            ):
                candidate["Crypto Long Defense"]=True
                candidate["Memory Note"]=(
                    f"{candidate['Memory Note']} | "
                    "BTC/ETH are not both strongly bullish; treat as warning, not a block"
                )
            else:
                candidate["Crypto Long Defense"]=False
                if market=="Crypto" and candidate.get("Direction","LONG")=="LONG" and crypto_strong_bullish:
                    candidate["Adjusted Score"]+=2
                    candidate["Memory Note"]=(
                        f"{candidate['Memory Note']} | "
                        "BTC/ETH lead signal: bullish crypto market may help this LONG"
                    )

            if (
                market=="Crypto" and
                candidate.get("Direction","LONG")=="SHORT" and
                not crypto_strong_bearish
            ):
                candidate["Crypto Short Defense"]=True
                candidate["Memory Note"]=(
                    f"{candidate['Memory Note']} | "
                    "BTC/ETH are not both strongly bearish; judge this coin by its own short setup"
                )
            else:
                candidate["Crypto Short Defense"]=False
                if market=="Crypto" and candidate.get("Direction","LONG")=="SHORT" and crypto_strong_bearish:
                    candidate["Adjusted Score"]+=3
                    candidate["Memory Note"]=(
                        f"{candidate['Memory Note']} | "
                        "BTC/ETH lead signal: bearish crypto drop may create an altcoin SHORT opportunity"
                    )

            candidate["Opportunity Score"]=opportunity_score(
                candidate
            )
            candidate["Memory Note"]=(
                f"{candidate.get('Memory Note','No memory adjustment')} | "
                f"Opportunity score: {candidate['Opportunity Score']}"
            )

            all_candidates.append(candidate)

    all_candidates=sorted(
        all_candidates,
        key=lambda x:x.get("Opportunity Score",x["Adjusted Score"]),
        reverse=True
    )[:OPPORTUNITY_TOP_SCAN_LIMIT]

    if direct_order_trade_due:
        for candidate in all_candidates:
            if direct_order_candidate(candidate):
                candidate["Direct Order Trade"]=True
                candidate["Opportunity Rescue"]=True
                candidate["Active Learning Trade"]=True
                candidate["Recovery Test Mode"]=True
                candidate["Position Cash"]=DIRECT_ORDER_POSITION_CASH
                candidate["Memory Note"]=(
                    f"{candidate.get('Memory Note','No memory adjustment')} | "
                    f"Direct order mode: trade required after {DIRECT_ORDER_MIN_TRADE_MINUTES} idle minutes; "
                    f"position sized for about ${DIRECT_ORDER_RISK_DOLLARS:,.0f} risk at stop"
                )
                break

    if alternate_setup_scout_available:
        for candidate in all_candidates:
            if qualifies_for_alternate_setup_scout(candidate):
                enable_alternate_setup_scout(candidate)
                break

    for candidate in all_candidates:

        if new_trades_this_scan>=MAX_NEW_TRADES_PER_SCAN:
            break

        if slots<=0:

            log_decision(
                cursor,
                conn,
                email,
                candidate,
                candidate["Market"],
                "skipped",
                "Max open positions reached"
            )

            break

        if candidate["Ticker"] in open_tickers:

            log_decision(
                cursor,
                conn,
                email,
                candidate,
                candidate["Market"],
                "skipped",
                "Already open"
            )

            continue

        same_trade_cooldown,same_trade_reason=same_trade_recently_opened(
            cursor,
            email,
            candidate["Ticker"],
            candidate.get("Direction","LONG"),
            now
        )

        if same_trade_cooldown and not candidate.get("Direct Order Trade"):

            log_decision(
                cursor,
                conn,
                email,
                candidate,
                candidate["Market"],
                "skipped",
                same_trade_reason
            )

            continue

        ticker_cooldown,ticker_cooldown_reason=ticker_early_failure_cooldown(
            cursor,
            email,
            candidate["Ticker"],
            now
        )

        if ticker_cooldown and not candidate.get("Direct Order Trade"):

            log_decision(
                cursor,
                conn,
                email,
                candidate,
                candidate["Market"],
                "skipped",
                ticker_cooldown_reason
            )

            continue

        ticker_session_failures=ticker_direction_session_early_failures(
            cursor,
            email,
            candidate["Ticker"],
            candidate.get("Direction","LONG")
        )

        if (
            not candidate.get("Direct Order Trade") and
            candidate.get("Direction","LONG")=="SHORT" and
            candidate.get("Setup Type")=="bearish_trigger" and
            ticker_session_failures>=SESSION_SHORT_FAILURE_HARD_LIMIT
        ):
            log_decision(
                cursor,
                conn,
                email,
                candidate,
                candidate["Market"],
                "skipped",
                (
                    f"Short defense: {candidate['Ticker']} bearish-trigger SHORT already failed "
                    "once this session, so I will not repeat it"
                )
            )

            continue
 
        if (
            ticker_session_failures>=SESSION_TICKER_EARLY_FAILURE_LIMIT and
            not candidate.get("Direct Order Trade")
        ):

            log_decision(
                cursor,
                conn,
                email,
                candidate,
                candidate["Market"],
                "skipped",
                (
                    f"{candidate['Ticker']} {candidate.get('Direction','LONG')} blocked "
                    f"for this session after {ticker_session_failures} early failures"
                )
            )

            continue

        brain_filter=session_brain_filter(
            cursor,
            email,
            candidate,
            session_profit
        )

        if brain_filter["Blocked"] and not candidate.get("Direct Order Trade"):
            log_decision(
                cursor,
                conn,
                email,
                candidate,
                candidate["Market"],
                "skipped",
                brain_filter["Reason"]
            )

            continue

        if brain_filter["Extra Min Score"]:
            candidate["Session Brain Extra Min Score"]=brain_filter["Extra Min Score"]
            candidate["Session Brain Max Cash"]=brain_filter["Max Cash"]
            candidate["Memory Note"]=(
                f"{candidate.get('Memory Note','No memory adjustment')} | "
                f"{brain_filter['Reason']}"
            )

        if candidate.get("Setup Blocked") and not candidate.get("Direct Order Trade"):

            log_decision(
                cursor,
                conn,
                email,
                candidate,
                candidate["Market"],
                "skipped",
                candidate.get("Setup Block Reason") or "Setup blocked by AI review memory"
            )

            continue

        if candidate.get("Brain Exploration"):
            exploration_failures=ticker_setup_direction_session_early_failures(
                cursor,
                email,
                candidate["Ticker"],
                candidate.get("Setup Type"),
                candidate.get("Direction","LONG")
            )

            if exploration_failures>=1:
                log_decision(
                    cursor,
                    conn,
                    email,
                    candidate,
                    candidate["Market"],
                    "skipped",
                    (
                        f"Brain exploration will not repeat {candidate['Ticker']} "
                        f"{candidate.get('Direction','LONG')} {candidate.get('Setup Type')} "
                        "after it already failed early this session"
                    )
                )

                continue

        if candidate.get("Crypto Market Caution"):
            candidate["Position Cash"]=min(
                candidate.get("Position Cash") or LEARNING_SCOUT_POSITION_CASH,
                LEARNING_SCOUT_POSITION_CASH
            )
            candidate["Memory Note"]=(
                f"{candidate.get('Memory Note','No memory adjustment')} | "
                "Crypto market caution is now a size warning, not a trade blocker"
            )

        if False and candidate.get("Crypto Market Caution"):

            if candidate.get("Direction","LONG")=="SHORT":

                if candidate.get("Crypto Short Defense"):

                    if candidate.get("Learning Scout"):
                        pass

                    elif (
                        mixed_market_scout_positions<MAX_MIXED_MARKET_SCOUT_POSITIONS and
                        qualifies_for_mixed_market_scout(candidate)
                    ):
                        candidate["Recovery Test Mode"]=True
                        candidate["Mixed Market Scout"]=True
                        candidate["Position Cash"]=RECOVERY_TEST_POSITION_CASH
                        candidate["Memory Note"]=(
                            f"{candidate.get('Memory Note','No memory adjustment')} | "
                            f"Mixed market scout: tiny ${RECOVERY_TEST_POSITION_CASH:,.0f} SHORT "
                            "allowed because the setup is strongly confirmed even though BTC/ETH are mixed"
                        )
                    else:
                        log_decision(
                            cursor,
                            conn,
                            email,
                            candidate,
                            candidate["Market"],
                            "skipped",
                            "Crypto SHORT blocked because BTC/ETH are not both strongly bearish"
                        )

                        continue

                if candidate.get("Mixed Market Scout"):
                    pass

                elif qualifies_for_crypto_short_test(candidate):

                    candidate["Recovery Test Mode"]=True
                    candidate["Position Cash"]=RECOVERY_TEST_POSITION_CASH
                    candidate["Memory Note"]=(
                        f"{candidate.get('Memory Note','No memory adjustment')} | "
                        f"Crypto market is weak: qualified SHORT allowed only "
                        f"as tiny ${RECOVERY_TEST_POSITION_CASH:,.0f} test trade"
                    )

                else:

                    log_decision(
                        cursor,
                        conn,
                        email,
                        candidate,
                        candidate["Market"],
                        "skipped",
                        "Weak crypto SHORT did not pass tiny test-trade quality"
                    )

                    continue

            elif candidate.get("Learning Scout"):
                pass

            elif (
                candidate.get("Crypto Long Defense") and
                mixed_market_scout_positions<MAX_MIXED_MARKET_SCOUT_POSITIONS and
                qualifies_for_mixed_market_scout(candidate)
            ):

                candidate["Recovery Test Mode"]=True
                candidate["Mixed Market Scout"]=True
                candidate["Position Cash"]=RECOVERY_TEST_POSITION_CASH
                candidate["Memory Note"]=(
                    f"{candidate.get('Memory Note','No memory adjustment')} | "
                    f"Mixed market scout: tiny ${RECOVERY_TEST_POSITION_CASH:,.0f} LONG "
                    "allowed because the setup is strongly confirmed even though BTC/ETH are mixed"
                )

            elif qualifies_for_recovery_test(candidate):

                candidate["Recovery Test Mode"]=True
                candidate["Position Cash"]=RECOVERY_TEST_POSITION_CASH
                candidate["Memory Note"]=(
                    f"{candidate.get('Memory Note','No memory adjustment')} | "
                    f"Crypto caution rule: only tiny ${RECOVERY_TEST_POSITION_CASH:,.0f} "
                    "recovery trade allowed"
                )

            else:

                log_decision(
                    cursor,
                    conn,
                    email,
                    candidate,
                    candidate["Market"],
                    "skipped",
                    "Crypto market caution active; requires recovery-test strength"
                )

                continue

        if False and candidate.get("Crypto Long Defense"):

            if candidate.get("Learning Scout"):
                pass

            elif (
                mixed_market_scout_positions<MAX_MIXED_MARKET_SCOUT_POSITIONS and
                qualifies_for_mixed_market_scout(candidate)
            ):
                candidate["Recovery Test Mode"]=True
                candidate["Mixed Market Scout"]=True
                candidate["Position Cash"]=RECOVERY_TEST_POSITION_CASH
                candidate["Memory Note"]=(
                    f"{candidate.get('Memory Note','No memory adjustment')} | "
                    f"Mixed market scout: tiny ${RECOVERY_TEST_POSITION_CASH:,.0f} LONG "
                    "allowed because the setup is strongly confirmed even though BTC/ETH are mixed"
                )
            else:
                log_decision(
                    cursor,
                    conn,
                    email,
                    candidate,
                    candidate["Market"],
                    "skipped",
                    "Crypto LONG blocked because BTC/ETH are not both strongly bullish"
                )

                continue

        if False and candidate.get("Crypto Short Defense"):

            if candidate.get("Learning Scout"):
                pass

            elif (
                mixed_market_scout_positions<MAX_MIXED_MARKET_SCOUT_POSITIONS and
                qualifies_for_mixed_market_scout(candidate)
            ):
                candidate["Recovery Test Mode"]=True
                candidate["Mixed Market Scout"]=True
                candidate["Position Cash"]=RECOVERY_TEST_POSITION_CASH
                candidate["Memory Note"]=(
                    f"{candidate.get('Memory Note','No memory adjustment')} | "
                    f"Mixed market scout: tiny ${RECOVERY_TEST_POSITION_CASH:,.0f} SHORT "
                    "allowed because the setup is strongly confirmed even though BTC/ETH are mixed"
                )
            else:
                log_decision(
                    cursor,
                    conn,
                    email,
                    candidate,
                    candidate["Market"],
                    "skipped",
                    "Crypto SHORT blocked because BTC/ETH are not both strongly bearish"
                )

                continue

        setup_failure_count=setup_direction_early_failure_count(
            cursor,
            email,
            candidate.get("Setup Type"),
            candidate.get("Direction","LONG")
        )

        if (
            candidate.get("Market")=="Crypto" and
            candidate.get("Direction","LONG")=="LONG" and
            candidate.get("Setup Type")=="ema8_pullback"
        ):
            crypto_long_losses,_=session_loss_stats(
                cursor,
                email,
                "AND market='Crypto' AND COALESCE(direction,'LONG')='LONG' AND setup_type='ema8_pullback'"
            )

            if crypto_long_losses>=CRYPTO_EMA8_PULLBACK_SESSION_LOSS_LIMIT:
                log_decision(
                    cursor,
                    conn,
                    email,
                    candidate,
                    candidate["Market"],
                    "skipped",
                    (
                        "Crypto LONG ema8_pullback paused for this session after "
                        f"{crypto_long_losses} loss(es). The AI should look for a fresh different setup "
                        "or a SHORT opportunity instead of repeating the same losing idea."
                    )
                )

                continue

        if setup_failure_count>=SETUP_DIRECTION_EARLY_FAILURE_LIMIT:

            if (
                candidate.get("Learning Scout") or
                qualifies_for_recovery_test(candidate) or
                qualifies_for_crypto_short_test(candidate)
            ):

                candidate["Recovery Test Mode"]=True
                candidate["Position Cash"]=RECOVERY_TEST_POSITION_CASH
                candidate["Memory Note"]=(
                    f"{candidate.get('Memory Note','No memory adjustment')} | "
                    f"Session mistake rule: {candidate.get('Setup Type')} "
                    f"{candidate.get('Direction','LONG')} had {setup_failure_count} early failures, "
                    f"using tiny ${RECOVERY_TEST_POSITION_CASH:,.0f} recovery size"
                )

            else:

                log_decision(
                    cursor,
                    conn,
                    email,
                    candidate,
                    candidate["Market"],
                    "skipped",
                    (
                        f"Session mistake rule: {candidate.get('Setup Type')} "
                        f"{candidate.get('Direction','LONG')} had {setup_failure_count} early failures; "
                        "requires recovery-test strength"
                    )
                )

                continue

        if candidate.get("Probation Mode"):

            probation_min_score=(
                MIN_PROBATION_SHORT_SCORE
                if candidate.get("Direction","LONG")=="SHORT"
                else MIN_PROBATION_LONG_SCORE
            )

            if candidate["Adjusted Score"]<probation_min_score:

                if qualifies_for_recovery_test(candidate) or qualifies_for_crypto_short_test(candidate):

                    candidate["Recovery Test Mode"]=True
                    candidate["Position Cash"]=RECOVERY_TEST_POSITION_CASH
                    recovery_reason=(
                        "trusted ticker live setup"
                        if candidate.get("Ticker Recovery Trusted")
                        else "crypto short test signal"
                        if qualifies_for_crypto_short_test(candidate)
                        else "raw score is strong enough"
                    )
                    candidate["Memory Note"]=(
                        f"{candidate.get('Memory Note','No memory adjustment')} | "
                        f"Recovery test: {recovery_reason}, raw score {candidate.get('Score')}, "
                        f"using tiny ${RECOVERY_TEST_POSITION_CASH:,.0f} size"
                    )

                else:

                    log_decision(
                        cursor,
                        conn,
                        email,
                        candidate,
                        candidate["Market"],
                        "skipped",
                        f"Probation score below minimum {probation_min_score}: {candidate.get('Probation Reason')}"
                    )

                    continue

            probation_cooldown,probation_reason=probation_in_cooldown(
                cursor,
                email,
                candidate["Ticker"],
                candidate.get("Setup Type"),
                candidate.get("Direction","LONG"),
                now
            )

            if probation_cooldown:

                log_decision(
                    cursor,
                    conn,
                    email,
                    candidate,
                    candidate["Market"],
                    "skipped",
                    probation_reason
                )

                continue

        if candidate["Market"]=="Crypto" and crypto_positions>=MAX_CRYPTO_POSITIONS:

            log_decision(
                cursor,
                conn,
                email,
                candidate,
                candidate["Market"],
                "skipped",
                f"Max crypto exposure reached ({MAX_CRYPTO_POSITIONS})"
            )

            continue

        if (
            is_stock_market(candidate.get("Market")) and
            candidate.get("Direction","LONG")=="LONG" and
            not stock_long_has_strong_confirmation(candidate)
        ):

            candidate["Recovery Test Mode"]=True
            candidate["Position Cash"]=RECOVERY_TEST_POSITION_CASH
            candidate["Memory Note"]=(
                f"{candidate.get('Memory Note','No memory adjustment')} | "
                f"Stock LONG defense: tiny ${RECOVERY_TEST_POSITION_CASH:,.0f} "
                "recovery-test size until stock longs prove themselves"
            )

        in_cooldown,cooldown_reason=ticker_in_loss_cooldown(
            cursor,
            email,
            candidate["Ticker"],
            now,
            candidate.get("Direction","LONG")
        )

        if in_cooldown and not candidate.get("Direct Order Trade"):

            log_decision(
                cursor,
                conn,
                email,
                candidate,
                candidate["Market"],
                "skipped",
                cooldown_reason
            )

            continue

        min_required_score=(
            (
                MIN_PROBATION_SHORT_SCORE
                if candidate.get("Direction","LONG")=="SHORT"
                else MIN_PROBATION_LONG_SCORE
            )
            if candidate.get("Probation Mode")
            else (
                MIN_SHORT_ADJUSTED_SCORE
                if candidate.get("Direction","LONG")=="SHORT"
                else MIN_LONG_ADJUSTED_SCORE
            )
        )

        if (
            candidate.get("Direction","LONG")=="SHORT" and
            candidate.get("Setup Type")=="bearish_trigger" and
            setup_is_session_loser(
                cursor,
                email,
                candidate.get("Setup Type"),
                candidate.get("Direction","LONG")
            )
        ):
            min_required_score+=WEAK_SHORT_EXTRA_MIN_SCORE
            candidate["Memory Note"]=(
                f"{candidate.get('Memory Note','No memory adjustment')} | "
                f"Short defense: bearish-trigger shorts are losing this session, "
                f"minimum score raised by {WEAK_SHORT_EXTRA_MIN_SCORE}"
            )

        if candidate.get("Session Brain Extra Min Score"):
            min_required_score+=candidate["Session Brain Extra Min Score"]

        can_trade=(
            candidate.get("Direct Order Trade") or
            candidate["Adjusted Score"]>=min_required_score or
            active_learning_candidate(candidate) or
            (
                candidate.get("Recovery Test Mode") and
                not candidate.get("Session Brain Extra Min Score")
            )
        )

        if not can_trade:

            log_decision(
                cursor,
                conn,
                email,
                candidate,
                candidate["Market"],
                "skipped",
                f"Adjusted score below minimum {min_required_score}"
            )

            continue

        passed_quality,quality_reason=quality_gate(
            candidate,
            now
        )

        if not passed_quality:

            log_decision(
                cursor,
                conn,
                email,
                candidate,
                candidate["Market"],
                "skipped",
                quality_reason
            )

            continue

        knowledge_grade,knowledge_note=day_trader_knowledge_grade(
            candidate
        )
        candidate["Knowledge Grade"]=knowledge_grade
        candidate["Knowledge Note"]=knowledge_note
        candidate["Memory Note"]=(
            f"{candidate.get('Memory Note','No memory adjustment')} | {knowledge_note}"
        )

        if candidate.get("Direct Order Trade") and knowledge_grade=="D":
            knowledge_grade="C"
            candidate["Knowledge Grade"]=knowledge_grade
            candidate["Knowledge Note"]=(
                f"{knowledge_note} Direct order override: paper trade required after idle time."
            )
            candidate["Memory Note"]=(
                f"{candidate.get('Memory Note','No memory adjustment')} | "
                "Direct order override changed grade D to controlled grade C so the AI can collect real trade data."
            )

        if knowledge_grade=="D" and candidate.get("Learning Scout"):
            candidate["Position Cash"]=min(
                candidate.get("Position Cash") or LEARNING_SCOUT_POSITION_CASH,
                LEARNING_SCOUT_POSITION_CASH
            )
            candidate["Memory Note"]=(
                f"{candidate.get('Memory Note','No memory adjustment')} | "
                "Knowledge grade D would normally skip, but learning scout is allowed "
                "with tiny size to collect data"
            )

        elif knowledge_grade=="D":

            log_decision(
                cursor,
                conn,
                email,
                candidate,
                candidate["Market"],
                "skipped",
                knowledge_note
            )

            continue

        if knowledge_grade=="C" and not candidate.get("Direct Order Trade"):
            candidate["Recovery Test Mode"]=True
            candidate["Position Cash"]=min(
                candidate.get("Position Cash") or RECOVERY_TEST_POSITION_CASH,
                RECOVERY_TEST_POSITION_CASH
            )

        pending=load_pending_setup(
            cursor,
            email,
            candidate["Ticker"],
            candidate.get("Direction","LONG")
        )

        if candidate.get("Direct Order Trade"):
            quality_reason=f"{quality_reason}; direct order bypassed pending confirmation"

        elif not pending:

            save_pending_setup(
                cursor,
                conn,
                email,
                candidate
            )

            log_decision(
                cursor,
                conn,
                email,
                candidate,
                candidate["Market"],
                "skipped",
                (
                    f"Pending setup saved. Waiting {PENDING_CONFIRM_SECONDS}s "
                    "for next 1m confirmation before entry"
                )
            )

            if candidate.get("Learning Scout"):
                learning_scout_available=False

            continue

        elif not pending_setup_ready(
            pending,
            now
        ):

            log_decision(
                cursor,
                conn,
                email,
                candidate,
                candidate["Market"],
                "skipped",
                "Pending setup is waiting for next 1m confirmation"
            )

            continue

        if candidate.get("Direct Order Trade"):
            pending_reason="direct order entry does not wait for the next confirmation candle"

        else:
            pending_confirmed,pending_reason=pending_setup_confirmed(
                pending,
                candidate
            )

            delete_pending_setup(
                cursor,
                conn,
                pending["ID"]
            )

            if not pending_confirmed:

                log_decision(
                    cursor,
                    conn,
                    email,
                    candidate,
                    candidate["Market"],
                    "skipped",
                    pending_reason
                )

                continue

        quality_reason=f"{quality_reason}; {pending_reason}"

        market_entry=latest_price(
            candidate["Ticker"]
        )

        if not market_entry:
            skipped_no_price+=1

            log_decision(
                cursor,
                conn,
                email,
                candidate,
                candidate["Market"],
                "skipped",
                "No live price"
            )

            continue

        direction=candidate.get("Direction","LONG")

        if direction=="SHORT":
            entry=simulated_sell_fill(
                market_entry
            )
            take_profit=round_market_price(entry*(1-TAKE_PROFIT_PCT))
            stop_loss=round_market_price(entry*(1+STOP_LOSS_PCT))
        else:
            entry=simulated_buy_fill(
                market_entry
            )
            take_profit=round_market_price(entry*(1+TAKE_PROFIT_PCT))
            stop_loss=round_market_price(entry*(1-STOP_LOSS_PCT))

        position_cash=candidate.get("Position Cash") or SMALL_POSITION_CASH

        if setup_is_session_loser(
            cursor,
            email,
            candidate.get("Setup Type"),
            candidate.get("Direction","LONG")
        ):
            position_cash=min(
                position_cash,
                RECOVERY_TEST_POSITION_CASH
            )
            candidate["Recovery Test Mode"]=True
            candidate["Memory Note"]=(
                f"{candidate.get('Memory Note','No memory adjustment')} | "
                f"Session loser sizing: {candidate.get('Direction','LONG')} {candidate.get('Setup Type')} "
                f"is losing now, size capped at ${RECOVERY_TEST_POSITION_CASH:,.0f}"
            )

        if (
            setup_is_session_winner(
                cursor,
                email,
                candidate.get("Setup Type"),
                candidate.get("Direction","LONG")
            ) and
            not candidate.get("Learning Scout") and
            not candidate.get("Recovery Test Mode")
        ):
            position_cash=max(
                position_cash,
                MEDIUM_POSITION_CASH
            )
            candidate["Memory Note"]=(
                f"{candidate.get('Memory Note','No memory adjustment')} | "
                "Session winner sizing: this setup is profitable in the current session"
            )

        if (
            is_stock_market(candidate.get("Market")) and
            not setup_is_session_winner(
                cursor,
                email,
                candidate.get("Setup Type"),
                candidate.get("Direction","LONG")
            )
        ):
            position_cash=min(
                position_cash,
                RECOVERY_TEST_POSITION_CASH
            )
            candidate["Recovery Test Mode"]=True
            candidate["Memory Note"]=(
                f"{candidate.get('Memory Note','No memory adjustment')} | "
                f"Stock safety: stocks stay tiny at ${RECOVERY_TEST_POSITION_CASH:,.0f} "
                "until this setup proves itself in the current session"
            )

        if (
            candidate.get("Market")=="Stocks" and
            session_profit<0 and
            candidate.get("Direction","LONG")=="LONG"
        ):
            position_cash=min(
                position_cash,
                US_STOCK_LOSS_DEFENSE_CASH
            )
            candidate["Recovery Test Mode"]=True
            candidate["Memory Note"]=(
                f"{candidate.get('Memory Note','No memory adjustment')} | "
                f"US stock loss defense: session is red, so new US stock LONGs are capped "
                f"at ${US_STOCK_LOSS_DEFENSE_CASH:,.0f} until the session recovers"
            )

        if candidate.get("Market")=="Europe Stocks":
            position_cash=min(
                position_cash,
                EUROPE_STOCK_POSITION_CASH
            )
            candidate["Recovery Test Mode"]=True
            candidate["Memory Note"]=(
                f"{candidate.get('Memory Note','No memory adjustment')} | "
                f"Europe stock protection: capped at ${EUROPE_STOCK_POSITION_CASH:,.0f} "
                "until this market proves it can win in live paper trading"
            )

        if candidate.get("Market")=="Asia Stocks":
            position_cash=min(
                position_cash,
                ASIA_STOCK_POSITION_CASH
            )
            candidate["Recovery Test Mode"]=True
            candidate["Memory Note"]=(
                f"{candidate.get('Memory Note','No memory adjustment')} | "
                f"Asia stock protection: capped at ${ASIA_STOCK_POSITION_CASH:,.0f} "
                "until this market proves it can win in live paper trading"
            )

        if candidate.get("Crypto Market Caution") or candidate.get("Crypto Long Defense") or candidate.get("Crypto Short Defense"):
            position_cash=RECOVERY_TEST_POSITION_CASH
            candidate["Recovery Test Mode"]=True

        if candidate.get("Session Brain Max Cash"):
            position_cash=min(
                position_cash,
                candidate["Session Brain Max Cash"]
            )
            candidate["Recovery Test Mode"]=True

        if candidate.get("Brain Exploration"):
            position_cash=BRAIN_EXPLORATION_POSITION_CASH
        elif candidate.get("Learning Scout"):
            position_cash=LEARNING_SCOUT_POSITION_CASH

        self_check=pre_entry_self_check(
            cursor,
            email,
            candidate,
            quality_reason
        )
        self_check_text=self_check["Text"]
        self_check_action=self_check["Action"]

        log_decision(
            cursor,
            conn,
            email,
            candidate,
            candidate["Market"],
            "self_check",
            self_check_text,
            market_entry
        )

        if self_check_action=="WAIT":
            log_decision(
                cursor,
                conn,
                email,
                candidate,
                candidate["Market"],
                "skipped",
                self_check_text,
                market_entry
            )

            continue

        if self_check_action=="LEARNING_SCOUT":
            scout_cash=(
                BRAIN_EXPLORATION_POSITION_CASH
                if candidate.get("Brain Exploration")
                else LEARNING_SCOUT_POSITION_CASH
            )
            position_cash=min(
                position_cash,
                scout_cash
            )
            candidate["Learning Scout"]=True
            candidate["Memory Note"]=(
                f"{candidate.get('Memory Note','No memory adjustment')} | "
                f"Self-check reduced this to tiny ${scout_cash:,.0f} learning scout size"
            )

        if candidate.get("Strong Live Idea"):
            if is_weak_breakout_family(candidate):
                position_cash=min(
                    position_cash,
                    OPPORTUNITY_RESCUE_POSITION_CASH
                )
                candidate["Recovery Test Mode"]=True
                candidate["Memory Note"]=(
                    f"{candidate.get('Memory Note','No memory adjustment')} | "
                    f"Breakout family sizing: this setup type is still proving itself, "
                    f"so size is capped at ${OPPORTUNITY_RESCUE_POSITION_CASH:,.0f}"
                )
            else:
                position_cash=max(
                    position_cash,
                    SMALL_POSITION_CASH
                )
            candidate["Brain Exploration"]=False
            candidate["Learning Scout"]=False
            if not is_weak_breakout_family(candidate):
                candidate["Recovery Test Mode"]=False
            candidate["Memory Note"]=(
                f"{candidate.get('Memory Note','No memory adjustment')} | "
                f"Strong live idea sizing: clean confirmed setup, position size ${position_cash:,.0f}"
            )

        if candidate.get("Opportunity Rescue"):
            rescue_cash=(
                DIRECT_ORDER_POSITION_CASH
                if candidate.get("Direct Order Trade")
                else
                ACTIVE_LEARNING_POSITION_CASH
                if candidate.get("Active Learning Trade")
                else
                BRAIN_EXPLORATION_POSITION_CASH
                if candidate.get("Hard Wait Override")
                else OPPORTUNITY_RESCUE_POSITION_CASH
            )
            position_cash=min(position_cash,rescue_cash)
            candidate["Recovery Test Mode"]=True
            candidate["Memory Note"]=(
                f"{candidate.get('Memory Note','No memory adjustment')} | "
                f"Opportunity rescue sizing: fresh live setup, controlled ${position_cash:,.0f} size"
            )

        if candidate.get("Direct Order Trade"):
            position_cash=DIRECT_ORDER_POSITION_CASH
            candidate["Recovery Test Mode"]=False
            candidate["Learning Scout"]=False
            candidate["Brain Exploration"]=False
            candidate["Memory Note"]=(
                f"{candidate.get('Memory Note','No memory adjustment')} | "
                f"Direct order sizing: forced ${position_cash:,.0f} paper position, "
                f"about ${DIRECT_ORDER_RISK_DOLLARS:,.0f} risk at the stop"
            )

        candidate["Memory Note"]=(
            f"{candidate.get('Memory Note','No memory adjustment')} | {self_check_text}"
        )

        pos={
            "Ticker":candidate["Ticker"],
            "Entry":entry,
            "TP":take_profit,
            "SL":stop_loss,
            "Qty":round(
                position_cash/(entry*currency_to_usd_factor(candidate["Ticker"])),
                4
            ),
            "Entry Time":now.strftime("%Y-%m-%d %H:%M:%S"),
            "Market":candidate["Market"],
            "Score":candidate["Adjusted Score"],
            "RSI":candidate["RSI"],
            "Direction":direction,
            "Entry Reason":(
                f"{candidate['Reason']} | {candidate['Memory Note']} | "
                f"{quality_reason} | position size ${position_cash:,.0f} | "
                "simulated fill includes slippage"
            ),
            "Setup Type":candidate.get("Setup Type"),
            "Trigger Time":candidate.get("Trigger Time"),
            "Trigger High":candidate.get("Trigger High"),
            "Trigger Close":candidate.get("Trigger Close")
        }

        position_saved=save_open_position(
            cursor,
            conn,
            email,
            pos
        )

        if not position_saved:

            log_decision(
                cursor,
                conn,
                email,
                candidate,
                candidate["Market"],
                "skipped",
                "Duplicate open position blocked"
            )

            continue

        open_tickers.append(
            candidate["Ticker"]
        )

        log_decision(
            cursor,
            conn,
            email,
            candidate,
            candidate["Market"],
            "opened",
            (
                f"{direction} | {candidate['Reason']} | {quality_reason} | "
                f"position size ${position_cash:,.0f} | simulated fill includes slippage"
            ),
            entry
        )

        slots-=1
        opened_count+=1
        new_trades_this_scan+=1

        if candidate["Market"]=="Crypto":
            crypto_positions+=1

        if candidate.get("Mixed Market Scout"):
            mixed_market_scout_positions+=1

        if candidate.get("Learning Scout"):
            learning_scout_available=False

    best_candidate=all_candidates[0] if all_candidates else None
    best_ticker=best_candidate["Ticker"] if best_candidate else None
    best_score=best_candidate["Adjusted Score"] if best_candidate else None

    if opened_count>0 or closed_count>0:
        status=(
            f"AI checked the market at {now.strftime('%H:%M:%S')}. "
            f"Opened {opened_count} trade(s), closed {closed_count} trade(s)."
        )
    elif slots<=0:
        status=(
            f"AI checked the market at {now.strftime('%H:%M:%S')}. "
            "No new trades because the max open positions limit is reached."
        )
    else:
        best_score_text=best_score if best_score is not None else "N/A"
        status=(
            f"AI checked the market at {now.strftime('%H:%M:%S')}. "
            f"No new trades. Best adjusted score: {best_score_text} "
            f"(long min: {MIN_LONG_ADJUSTED_SCORE}, short min: {MIN_SHORT_ADJUSTED_SCORE})."
        )

        cursor.execute("""
            SELECT ticker,direction,reason,adjusted_score
            FROM trade_decisions
            WHERE email=? AND decision='skipped' AND time>=?
            ORDER BY adjusted_score DESC
            LIMIT 3
        """,(
            email,
            scan_started_text
        ))

        top_skips=cursor.fetchall()

        if top_skips:
            skip_parts=[]
            for row in top_skips:
                skip_ticker,skip_direction,skip_reason,skip_score=row
                skip_parts.append(
                    f"{skip_ticker} {skip_direction} (score {skip_score}): {skip_reason}"
                )
            status+=" Why no trade — "+"; | ".join(skip_parts)+"."

        if not crypto_healthy:
            status+=" Crypto market caution is active."

        if not is_regular_us_market_hours(now):
            status+=" US stock market is closed."

        if skipped_no_price>0:
            status+=f" {skipped_no_price} candidate(s) had no live price."

    if not should_continue(
        cursor,
        email
    ):
        return

    update_bot_state(
        cursor,
        conn,
        email,
        status,
        True,
        best_ticker=best_ticker,
        best_score=best_score,
        open_positions_count=len(load_open_positions(cursor,email)),
        today_profit=today_profit
    )


def main():

    if len(sys.argv)<2:
        return

    email=sys.argv[1]

    # Optional --duration N (seconds) for cloud/CI runs
    duration_limit=None
    if "--duration" in sys.argv:
        idx=sys.argv.index("--duration")
        if idx+1<len(sys.argv):
            try:
                duration_limit=int(sys.argv[idx+1])
            except ValueError:
                pass
    run_start=time.time()

    conn,cursor=connect_db()
    existing_start=get_session_start_time(
        cursor,
        email
    )
    session_start=existing_start or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    ensure_session_record(
        cursor,
        conn,
        email,
        session_start
    )

    seed_human_lessons(
        cursor,
        conn,
        email
    )

    update_bot_state(
        cursor,
        conn,
        email,
        "AI is training its replay brain from recent 1-minute candles.",
        True,
        session_start_time=session_start
    )

    train_pattern_brain(
        cursor,
        conn,
        email
    )

    update_bot_state(
        cursor,
        conn,
        email,
        "AI worker is running in the background.",
        True,
        session_start_time=session_start
    )

    try:

        last_scan_time=0

        while should_continue(cursor,email) and (
            duration_limit is None or (time.time()-run_start)<duration_limit
        ):

            if not current_worker_is_owner(cursor,email):
                break

            current_time=time.time()
            searching_enabled=should_search_for_new_trades(
                cursor,
                email
            )

            scan_for_new=(
                searching_enabled and
                current_time-last_scan_time>=NEW_TRADE_SCAN_SECONDS
            )

            run_once(
                cursor,
                conn,
                email,
                scan_for_new=scan_for_new,
                searching_enabled=searching_enabled
            )

            if scan_for_new:

                last_scan_time=current_time

            for _ in range(POSITION_CHECK_SECONDS):

                if not should_continue(cursor,email):
                    break

                time.sleep(1)

    except Exception as exc:

        update_bot_state(
            cursor,
            conn,
            email,
            f"AI worker stopped because of an error: {exc}",
            False
        )

        close_session_record(
            cursor,
            conn,
            email,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "error"
        )

    finally:

        if should_continue(cursor,email):

            update_bot_state(
                cursor,
                conn,
                email,
                "AI worker stopped.",
                False
            )

            close_session_record(
                cursor,
                conn,
                email,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "stopped"
            )

        conn.close()


if __name__=="__main__":
    main()
