import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
import hashlib
import os
import subprocess
import sys
from dotenv import load_dotenv
import requests
try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh=None

try:
    from trading_v2.repository import StrategyLabRepository
except Exception:
    StrategyLabRepository=None

st.set_page_config(page_title="AI Trader", layout="wide")

# Hide Streamlit toolbar (Stop/Deploy buttons)
st.markdown("""
<style>
header[data-testid="stHeader"] { display: none !important; }
#MainMenu { visibility: hidden !important; }
footer { visibility: hidden !important; }
</style>
""", unsafe_allow_html=True)

# Auto-refresh every 10 seconds
if st_autorefresh is not None:
    st_autorefresh(interval=10000, key="dashboard_refresh")

# ---------------- SETTINGS ----------------

START_BALANCE=50000.0
MAX_OPEN_POSITIONS=10
POSITION_CASH=15000.0
MIN_SCORE_TO_TRADE=6
MAX_HOLD_MINUTES=20
REFRESH_SECONDS=20
POSITION_CHECK_SECONDS=5
NEW_TRADE_SCAN_SECONDS=5
TAKE_PROFIT_PCT=0.003
STOP_LOSS_PCT=0.0025
DAILY_LOSS_LIMIT=750.0
MIN_ENTRY_RSI=25
MAX_ENTRY_RSI=88
PROFIT_EXIT_MINUTES=5
PROFIT_EXIT_MIN_PCT=0.0015
COOLDOWN_AFTER_LOSS_MINUTES=3
SLIPPAGE_PCT=0.0004
BROKER_FEE_PCT=0.0002
# ---------------- TWELVE DATA ----------------

load_dotenv()

TWELVE_DATA_API_KEY=os.getenv("TWELVE_DATA_API_KEY")

twelvedata_ready=False

if TWELVE_DATA_API_KEY:
    twelvedata_ready=True

# ---------------- DATABASE ----------------

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
CREATE TABLE IF NOT EXISTS users(
    email TEXT PRIMARY KEY,
    password TEXT,
    balance REAL DEFAULT 50000,
    profit REAL DEFAULT 0,
    trades_taken INTEGER DEFAULT 0
)
""")

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
CREATE TABLE IF NOT EXISTS evaluation_windows(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    start_time TEXT NOT NULL,
    planned_end_time TEXT NOT NULL,
    end_time TEXT,
    profit REAL DEFAULT 0,
    trades INTEGER DEFAULT 0,
    status TEXT DEFAULT 'running',
    note TEXT
)
""")

cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_evaluation_windows_email
ON evaluation_windows(email,start_time)
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

cursor.execute("PRAGMA table_info(trades)")
trade_cols=[c[1] for c in cursor.fetchall()]

if "entry_time" not in trade_cols:
    cursor.execute("ALTER TABLE trades ADD COLUMN entry_time TEXT")

if "exit_time" not in trade_cols:
    cursor.execute("ALTER TABLE trades ADD COLUMN exit_time TEXT")

if "reason" not in trade_cols:
    cursor.execute("ALTER TABLE trades ADD COLUMN reason TEXT")

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

conn.commit()

# ---------------- HELPERS ----------------

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def clean_data(data):

    if isinstance(data.columns,pd.MultiIndex):
        data.columns=data.columns.get_level_values(0)

    return data


def calculate_rsi(close,period=14):

    delta=close.diff()

    gain=delta.where(delta>0,0).rolling(period).mean()

    loss=(-delta.where(delta<0,0)).rolling(period).mean()

    rs=gain/loss

    rsi=100-(100/(1+rs))

    return rsi


def twelvedata_latest_price(ticker):

    if not TWELVE_DATA_API_KEY:
        return None

    try:

        url=f"https://api.twelvedata.com/price?symbol={ticker}&apikey={TWELVE_DATA_API_KEY}"

        response=requests.get(url)

        data=response.json()

        if "price" in data:

            return round_market_price(float(data["price"]))

        return None

    except:

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

    except:

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


def format_market_price(price):

    if price is None:
        return "N/A"

    decimals=price_decimals(price)

    return f"${float(price):,.{decimals}f}"


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


def estimated_fees(entry,exit_price,qty,ticker=None):

    return (
        ((entry*qty)+(exit_price*qty))*
        currency_to_usd_factor(ticker)*
        BROKER_FEE_PCT
    )


def estimated_net_profit(entry,current,qty,ticker=None):

    exit_fill=simulated_sell_fill(current)

    return round(
        ((exit_fill-entry)*qty*currency_to_usd_factor(ticker))-
        estimated_fees(entry,exit_fill,qty,ticker),
        2
    )


def estimated_net_profit_for_direction(direction,entry,current,qty,ticker=None):

    exit_fill=exit_fill_for_direction(
        direction,
        current
    )

    return profit_for_direction(
        direction,
        entry,
        exit_fill,
        qty,
        ticker
    )


def twelvedata_symbol(ticker):

    if ticker.endswith("-USD"):
        return ticker.replace("-USD","/USD")

    return ticker


def twelvedata_chart_data(ticker):

    if not TWELVE_DATA_API_KEY:
        return pd.DataFrame()

    try:

        url="https://api.twelvedata.com/time_series"
        response=requests.get(
            url,
            params={
                "symbol":twelvedata_symbol(ticker),
                "interval":"1min",
                "outputsize":500,
                "apikey":TWELVE_DATA_API_KEY
            },
            timeout=10
        )

        payload=response.json()
        values=payload.get("values",[])

        if not values:
            return pd.DataFrame()

        data=pd.DataFrame(values)
        data["datetime"]=pd.to_datetime(data["datetime"])
        data=data.set_index("datetime").sort_index()

        for col in ["open","high","low","close"]:
            data[col]=pd.to_numeric(data[col],errors="coerce")

        data=data.rename(columns={
            "open":"Open",
            "high":"High",
            "low":"Low",
            "close":"Close"
        })

        if "volume" in data.columns:
            data["Volume"]=pd.to_numeric(data["volume"],errors="coerce")

        return data.dropna(subset=["Open","High","Low","Close"])

    except Exception:

        return pd.DataFrame()


def get_chart_data(ticker):

    data=pd.DataFrame()

    for period in ["1d","5d"]:

        data=yf.download(
            ticker,
            period=period,
            interval="1m",
            progress=False,
            auto_adjust=True,
            threads=False
        )

        if not data.empty:
            break

    if data.empty:
        data=twelvedata_chart_data(ticker)

    if data.empty:
        return data

    data=clean_data(data)

    return data


def trade_duration_minutes(trade):

    try:

        start=datetime.strptime(
            trade.get("Entry Time"),
            "%Y-%m-%d %H:%M:%S"
        )

        end=datetime.strptime(
            trade.get("Exit Time"),
            "%Y-%m-%d %H:%M:%S"
        )

        return round((end-start).total_seconds()/60,1)

    except Exception:

        return None


def trade_move_pct(trade):

    try:
        if trade.get("Direction","LONG")=="SHORT":
            return ((trade["Entry"]-trade["Exit"])/trade["Entry"])*100

        return ((trade["Exit"]-trade["Entry"])/trade["Entry"])*100
    except Exception:
        return None


def estimated_position_size(trade):

    try:

        if trade.get("Direction","LONG")=="SHORT":
            price_move=trade["Entry"]-trade["Exit"]
        else:
            price_move=trade["Exit"]-trade["Entry"]

        if price_move==0:
            return None

        qty=trade["Profit"]/price_move

        return abs(qty*trade["Entry"])

    except Exception:

        return None


def split_strategy_reason(reason):

    if not reason:
        return []

    parts=[]

    for block in str(reason).split("|"):

        for item in block.split(","):

            text=item.strip()

            if text:
                parts.append(text)

    return parts


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


def review_trade_for_app(trade):

    if trade.get("Review Label"):
        return trade

    setup_type=detect_setup_type(
        trade.get("Entry Reason")
    )

    label="manual_stop" if "AI stopped" in trade.get("Reason","") else "pending"
    notes=(
        "Manual stop interrupted the trade."
        if label=="manual_stop"
        else "Review will be created when the worker closes future trades."
    )

    trade["Setup Type"]=setup_type
    trade["Review Label"]=label
    trade["Review Notes"]=notes
    trade["Hold Minutes"]=trade_duration_minutes(trade)
    trade["Move Pct"]=trade_move_pct(trade)

    return trade


def nearest_chart_time(data,time_text):

    if not time_text:
        return None

    try:

        target=pd.Timestamp(time_text)

        if data.index.tz is not None:
            target=target.tz_localize("Asia/Jerusalem").tz_convert(data.index.tz)

        index_position=data.index.get_indexer(
            [target],
            method="nearest"
        )[0]

        if index_position<0:
            return None

        return data.index[index_position]

    except Exception:

        return None


def crop_trade_window(data,entry_time,exit_time):

    if entry_time is None and exit_time is None:
        return data.tail(180)

    start_time=entry_time or exit_time
    end_time=exit_time or entry_time

    start_time=start_time-pd.Timedelta(minutes=20)

    if exit_time is not None:
        end_time=min(
            end_time+pd.Timedelta(minutes=5),
            data.index.max()
        )
    else:
        end_time=data.index.max()

    cropped=data[
        (data.index>=start_time) &
        (data.index<=end_time)
    ]

    if len(cropped)<20:
        return data.tail(180)

    return cropped
# ---------------- SESSION ----------------

defaults={
    "balance":START_BALANCE,
    "profit":0.0,
    "trades_taken":0,
    "history":[],
    "open_positions":[],
    "running":False,
    "selected_trade":None,
    "selected_trade_id":None,
    "selected_session_review":False,
    "logged_in":False,
    "user_email":"",
    "show_profile_menu":False,
    "ai_status":"AI is stopped."
}

for k,v in defaults.items():
    if k not in st.session_state:
        st.session_state[k]=v

# ---------------- WATCHLISTS ----------------

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

# ---------------- SAVE / LOAD ----------------

def load_user_data(email):

    cursor.execute(
        "SELECT balance, profit, trades_taken FROM users WHERE email=?",
        (email,)
    )

    row=cursor.fetchone()

    if row:
        st.session_state.balance=float(row[0])
        st.session_state.profit=float(row[1])
        st.session_state.trades_taken=int(row[2])

    cursor.execute("""
        SELECT id,time,ticker,entry,exit,profit,entry_time,exit_time,reason,
               market,score,rsi,direction,entry_reason,trigger_time,trigger_high,trigger_close,
               setup_type,review_label,review_notes,hold_minutes,move_pct
        FROM trades
        WHERE email=?
        ORDER BY id DESC
        LIMIT 50
    """,(email,))

    rows=cursor.fetchall()

    st.session_state.history=[
        {
            "ID":r[0],
            "Time":r[1],
            "Ticker":r[2],
            "Entry":float(r[3]),
            "Exit":float(r[4]),
            "Profit":float(r[5]),
            "Entry Time":r[6],
            "Exit Time":r[7],
            "Reason":r[8],
            "Market":r[9],
            "Score":r[10],
            "RSI":r[11],
            "Direction":r[12] or "LONG",
            "Entry Reason":r[13],
            "Trigger Time":r[14],
            "Trigger High":r[15],
            "Trigger Close":r[16],
            "Setup Type":r[17],
            "Review Label":r[18],
            "Review Notes":r[19],
            "Hold Minutes":r[20],
            "Move Pct":r[21]
        }
        for r in rows
    ]

    cursor.execute("""
        SELECT id,ticker,entry,tp,sl,qty,entry_time,market,score,rsi,entry_reason,
               trigger_time,trigger_high,trigger_close,direction
        FROM open_positions_v2
        WHERE email=?
        ORDER BY id DESC
    """,(email,))

    rows=cursor.fetchall()

    st.session_state.open_positions=[
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
        for r in rows
    ]

    state=get_bot_state(email)

    st.session_state.running=state["running"]
    st.session_state.ai_status=state["status"]


def get_bot_state(email):

    cursor.execute("""
        SELECT running,pid,status,last_heartbeat,best_ticker,best_score,
               open_positions_count,today_profit,searching_enabled,session_start_time
        FROM bot_state
        WHERE email=?
    """,(email,))

    row=cursor.fetchone()

    if not row:

        cursor.execute("""
            INSERT INTO bot_state(email,running,pid,status,last_heartbeat)
            VALUES(?,?,?,?,?)
        """,(
            email,
            0,
            None,
            "AI is stopped.",
            None
        ))

        conn.commit()

        return {
            "running":False,
            "pid":None,
            "status":"AI is stopped.",
            "last_heartbeat":None,
            "best_ticker":None,
            "best_score":None,
            "open_positions_count":0,
            "today_profit":0.0,
            "searching_enabled":False,
            "session_start_time":None
        }

    running=bool(row[0])
    pid=row[1]

    if running and not is_process_alive(pid):

        return {
            "running":False,
            "pid":pid,
            "status":"Always-on supervisor is restarting the worker.",
            "last_heartbeat":row[3],
            "best_ticker":row[4],
            "best_score":row[5],
            "open_positions_count":row[6] or 0,
            "today_profit":float(row[7] or 0),
            "searching_enabled":bool(row[8]),
            "session_start_time":row[9]
        }

    return {
        "running":running,
        "pid":pid,
        "status":row[2] or "AI is stopped.",
        "last_heartbeat":row[3],
        "best_ticker":row[4],
        "best_score":row[5],
        "open_positions_count":row[6] or 0,
        "today_profit":float(row[7] or 0),
        "searching_enabled":bool(row[8]),
        "session_start_time":row[9]
    }


def get_current_evaluation_window(email):

    cursor.execute("""
        SELECT id,start_time,planned_end_time,end_time,profit,trades,status,note
        FROM evaluation_windows
        WHERE email=?
        ORDER BY id DESC
        LIMIT 1
    """,(email,))

    row=cursor.fetchone()

    if not row:
        return None

    start_time=row[1]
    planned_end=row[2]
    end_time=row[3]
    effective_end=end_time or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        SELECT COALESCE(SUM(profit),0),COUNT(*)
        FROM trades
        WHERE email=? AND time>=? AND time<=?
    """,(
        email,
        start_time,
        effective_end
    ))

    live_profit,live_trades=cursor.fetchone()

    try:
        start_dt=datetime.strptime(start_time,"%Y-%m-%d %H:%M:%S")
        planned_end_dt=datetime.strptime(planned_end,"%Y-%m-%d %H:%M:%S")
        elapsed_seconds=max(0,(datetime.now()-start_dt).total_seconds())
        total_seconds=max(1,(planned_end_dt-start_dt).total_seconds())
        progress=min(1.0,elapsed_seconds/total_seconds)
        remaining=max(timedelta(0),planned_end_dt-datetime.now())
    except Exception:
        progress=0.0
        remaining=timedelta(0)

    return {
        "id":row[0],
        "start_time":start_time,
        "planned_end_time":planned_end,
        "end_time":end_time,
        "profit":float(live_profit or row[4] or 0),
        "trades":int(live_trades or row[5] or 0),
        "status":row[6] or "unknown",
        "note":row[7],
        "progress":progress,
        "remaining":str(remaining).split(".")[0]
    }


def is_process_alive(pid):

    if not pid:
        return False

    try:
        pid=int(pid)

        if os.name=="nt":
            result=subprocess.run(
                [
                    "tasklist",
                    "/FI",
                    f"PID eq {pid}",
                    "/FO",
                    "CSV",
                    "/NH"
                ],
                capture_output=True,
                text=True,
                timeout=5
            )

            return str(pid) in result.stdout

        os.kill(pid,0)
        return True

    except Exception:

        return False


def update_bot_state(email,running,pid,status,searching_enabled=None,session_start_time=None):

    cursor.execute("""
        INSERT INTO bot_state(email,running,pid,status,last_heartbeat,searching_enabled,session_start_time)
        VALUES(?,?,?,?,?,?,?)
        ON CONFLICT(email) DO UPDATE SET
            running=excluded.running,
            pid=excluded.pid,
            status=excluded.status,
            last_heartbeat=excluded.last_heartbeat,
            searching_enabled=COALESCE(excluded.searching_enabled,bot_state.searching_enabled),
            session_start_time=COALESCE(excluded.session_start_time,bot_state.session_start_time)
    """,(
        email,
        1 if running else 0,
        pid,
        status,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        None if searching_enabled is None else 1 if searching_enabled else 0,
        session_start_time
    ))

    conn.commit()


def session_totals(email,start_time,end_time=None):

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


def start_session_record(email,start_time):

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


def close_session_record(email,end_time,status="stopped"):

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


def latest_session_record(email):

    cursor.execute("""
        SELECT id,start_time,end_time,profit,trades,status
        FROM ai_sessions
        WHERE email=?
        ORDER BY id DESC
        LIMIT 1
    """,(
        email,
    ))

    return cursor.fetchone()


def set_searching_enabled(email,enabled):

    cursor.execute("""
        UPDATE bot_state
        SET searching_enabled=?,
            status=?,
            last_heartbeat=?
        WHERE email=?
    """,(
        1 if enabled else 0,
        (
            "AI is searching for new trades and managing open positions."
            if enabled
            else "AI search is paused. Existing open positions are still being managed."
        ),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        email
    ))

    conn.commit()


def start_background_ai(email):

    state=get_bot_state(email)

    if state["running"]:

        set_searching_enabled(
            email,
            True
        )
        st.session_state.running=True
        st.session_state.ai_status="AI is searching for new trades and managing open positions."
        return

    worker_path=os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "bot_worker.py"
    )

    creationflags=0

    if os.name=="nt":
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP|subprocess.DETACHED_PROCESS

    process=subprocess.Popen(
        [
            sys.executable,
            worker_path,
            email
        ],
        cwd=os.path.dirname(worker_path),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creationflags
    )

    session_start=datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    start_session_record(
        email,
        session_start
    )

    update_bot_state(
        email,
        True,
        process.pid,
        "AI worker is running in the background.",
        True,
        session_start
    )

    st.session_state.running=True
    st.session_state.ai_status="AI worker is running in the background."


def stop_background_ai(email):

    state=get_bot_state(email)

    update_bot_state(
        email,
        False,
        state["pid"],
        "AI is stopped.",
        False
    )

    close_all_open_positions(
        "AI stopped manually"
    )

    close_session_record(
        email,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "stopped"
    )

    pid=state.get("pid")

    if pid and is_process_alive(pid):

        try:

            if os.name=="nt":
                subprocess.run(
                    [
                        "taskkill",
                        "/PID",
                        str(pid),
                        "/F"
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:
                os.kill(
                    int(pid),
                    15
                )

        except Exception:
            pass

    st.session_state.running=False
    st.session_state.ai_status="AI is stopped."


def reset_trade_counter(email):

    cursor.execute("""
        UPDATE users
        SET trades_taken=?
        WHERE email=?
    """,(
        0,
        email
    ))

    conn.commit()

    st.session_state.trades_taken=0


def get_live_ai_status(email):

    bot_state=get_bot_state(email)

    cursor.execute(
        "SELECT COUNT(*) FROM open_positions_v2 WHERE email=?",
        (email,)
    )

    open_count=cursor.fetchone()[0] or 0

    today=datetime.now().strftime("%Y-%m-%d")

    cursor.execute("""
        SELECT COALESCE(SUM(profit),0)
        FROM trades
        WHERE email=? AND substr(time,1,10)=?
    """,(
        email,
        today
    ))

    today_profit=float(cursor.fetchone()[0] or 0)

    session_start=bot_state.get("session_start_time")

    if session_start:

        cursor.execute("""
            SELECT COALESCE(SUM(profit),0)
            FROM trades
            WHERE email=? AND time>=?
        """,(
            email,
            session_start
        ))

        session_profit=float(cursor.fetchone()[0] or 0)

    else:

        session_profit=0.0

    cursor.execute("""
        SELECT time,ticker,decision,reason,adjusted_score
        FROM trade_decisions
        WHERE email=?
        ORDER BY id DESC
        LIMIT 1
    """,(
        email,
    ))

    last_decision=cursor.fetchone()

    cursor.execute("""
        SELECT ticker,adjusted_score,decision,reason,time
        FROM trade_decisions
        WHERE email=? AND adjusted_score IS NOT NULL
        ORDER BY id DESC
        LIMIT 25
    """,(
        email,
    ))

    recent_decisions=cursor.fetchall()

    best_recent=None

    if recent_decisions:
        best_recent=max(
            recent_decisions,
            key=lambda r:r[1] if r[1] is not None else -1
        )

    return {
        "worker":"Running" if bot_state["running"] else "Stopped",
        "searching":"Searching" if bot_state["searching_enabled"] else "Paused",
        "status":bot_state["status"],
        "last_check":bot_state["last_heartbeat"] or "N/A",
        "open_count":open_count,
        "today_profit":today_profit,
        "session_profit":session_profit,
        "session_start":session_start,
        "last_activity":last_decision,
        "best_recent":best_recent
    }


def get_live_account_summary(email):

    cursor.execute(
        "SELECT balance,profit,trades_taken FROM users WHERE email=?",
        (email,)
    )

    row=cursor.fetchone()

    if not row:
        return {
            "balance":st.session_state.balance,
            "profit":st.session_state.profit,
            "trades_taken":st.session_state.trades_taken
        }

    return {
        "balance":float(row[0]),
        "profit":float(row[1]),
        "trades_taken":int(row[2])
    }


def get_last_closed_trade(email):

    cursor.execute("""
        SELECT id,time,ticker,entry,exit,profit,entry_time,exit_time,reason,
               market,score,rsi,direction,entry_reason,trigger_time,trigger_high,trigger_close,
               setup_type,review_label,review_notes,hold_minutes,move_pct
        FROM trades
        WHERE email=?
        ORDER BY id DESC
        LIMIT 1
    """,(
        email,
    ))

    r=cursor.fetchone()

    if not r:
        return None

    return {
        "ID":r[0],
        "Time":r[1],
        "Ticker":r[2],
        "Entry":float(r[3]),
        "Exit":float(r[4]),
        "Profit":float(r[5]),
        "Entry Time":r[6],
        "Exit Time":r[7],
        "Reason":r[8],
        "Market":r[9],
        "Score":r[10],
        "RSI":r[11],
        "Direction":r[12] or "LONG",
        "Entry Reason":r[13],
        "Trigger Time":r[14],
        "Trigger High":r[15],
        "Trigger Close":r[16],
        "Setup Type":r[17],
        "Review Label":r[18],
        "Review Notes":r[19],
        "Hold Minutes":r[20],
        "Move Pct":r[21]
    }


def get_trade_by_id(email,trade_id):

    if not trade_id:
        return None

    cursor.execute("""
        SELECT id,time,ticker,entry,exit,profit,entry_time,exit_time,reason,
               market,score,rsi,direction,entry_reason,trigger_time,trigger_high,trigger_close,
               setup_type,review_label,review_notes,hold_minutes,move_pct
        FROM trades
        WHERE email=? AND id=?
        LIMIT 1
    """,(
        email,
        trade_id
    ))

    r=cursor.fetchone()

    if not r:
        return None

    return {
        "ID":r[0],
        "Time":r[1],
        "Ticker":r[2],
        "Entry":float(r[3]),
        "Exit":float(r[4]),
        "Profit":float(r[5]),
        "Entry Time":r[6],
        "Exit Time":r[7],
        "Reason":r[8],
        "Market":r[9],
        "Score":r[10],
        "RSI":r[11],
        "Direction":r[12] or "LONG",
        "Entry Reason":r[13],
        "Trigger Time":r[14],
        "Trigger High":r[15],
        "Trigger Close":r[16],
        "Setup Type":r[17],
        "Review Label":r[18],
        "Review Notes":r[19],
        "Hold Minutes":r[20],
        "Move Pct":r[21]
    }


def get_live_open_positions(email):

    cursor.execute("""
        SELECT id,ticker,entry,tp,sl,qty,entry_time,market,score,rsi,entry_reason,
               trigger_time,trigger_high,trigger_close,direction
        FROM open_positions_v2
        WHERE email=?
        ORDER BY id DESC
    """,(
        email,
    ))

    rows=cursor.fetchall()

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
        for r in rows
    ]


def parse_app_time(value):

    if not value:
        return None

    try:
        return pd.to_datetime(value).to_pydatetime()
    except Exception:
        return None


def format_duration_between(start_value,end_value):

    start=parse_app_time(start_value)
    end=parse_app_time(end_value)

    if not start or not end or end<start:
        return "N/A"

    total_minutes=int((end-start).total_seconds()//60)
    hours=total_minutes//60
    minutes=total_minutes%60

    if hours and minutes:
        return f"{hours}h {minutes}m"

    if hours:
        return f"{hours}h"

    return f"{minutes}m"


def session_end_time(ai_status,trades):

    if ai_status.get("worker")=="Running":
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    candidates=[
        ai_status.get("last_check")
    ]

    for trade in trades:
        candidates.append(
            trade.get("Exit Time") or trade.get("Time")
        )

    parsed=[
        parse_app_time(value)
        for value in candidates
    ]

    parsed=[
        value
        for value in parsed
        if value
    ]

    if not parsed:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return max(parsed).strftime("%Y-%m-%d %H:%M:%S")


def get_session_trades(email,session_start):

    if not session_start:
        return []

    cursor.execute("""
        SELECT id,time,ticker,entry,exit,profit,entry_time,exit_time,reason,
               market,score,rsi,direction,entry_reason,trigger_time,trigger_high,trigger_close,
               setup_type,review_label,review_notes,hold_minutes,move_pct
        FROM trades
        WHERE email=? AND time>=?
        ORDER BY id DESC
    """,(
        email,
        session_start
    ))

    rows=cursor.fetchall()

    return [
        {
            "ID":r[0],
            "Time":r[1],
            "Ticker":r[2],
            "Entry":float(r[3]),
            "Exit":float(r[4]),
            "Profit":float(r[5]),
            "Entry Time":r[6],
            "Exit Time":r[7],
            "Reason":r[8],
            "Market":r[9],
            "Score":r[10],
            "RSI":r[11],
            "Direction":r[12] or "LONG",
            "Entry Reason":r[13],
            "Trigger Time":r[14],
            "Trigger High":r[15],
            "Trigger Close":r[16],
            "Setup Type":r[17],
            "Review Label":r[18],
            "Review Notes":r[19],
            "Hold Minutes":r[20],
            "Move Pct":r[21]
        }
        for r in rows
    ]


def summarize_group(trades,key):

    rows=[]

    for name in sorted({trade.get(key) or "Unknown" for trade in trades}):
        group=[
            trade
            for trade in trades
            if (trade.get(key) or "Unknown")==name
        ]
        profits=[
            float(trade.get("Profit") or 0)
            for trade in group
        ]
        wins=[
            profit
            for profit in profits
            if profit>0
        ]

        rows.append({
            key:name,
            "Trades":len(group),
            "Win Rate":round(len(wins)/len(group)*100,2) if group else 0,
            "Total P/L":round(sum(profits),2),
            "Average P/L":round(sum(profits)/len(group),2) if group else 0
        })

    return sorted(
        rows,
        key=lambda row:row["Total P/L"]
    )


def confidence_from_row(row):

    trades=row.get("Trades") or 0
    win_rate=row.get("Win Rate")
    avg_profit=row.get("Average P/L") or 0
    total_profit=row.get("Total P/L") or 0

    if trades<3:
        return "new"

    if trades>=8 and total_profit>0 and avg_profit>0 and win_rate is not None and win_rate>=58:
        return "trusted"

    if trades>=6 and total_profit<0 and avg_profit<0 and win_rate is not None and win_rate<=35:
        return "danger"

    if trades>=4 and (total_profit<0 or avg_profit<0 or (win_rate is not None and win_rate<45)):
        return "probation"

    return "normal"


def add_confidence(rows):

    updated=[]

    for row in rows:
        next_row=dict(row)
        next_row["Confidence"]=confidence_from_row(
            next_row
        )
        updated.append(
            next_row
        )

    return updated


def build_session_learning(email):

    ai_status=get_live_ai_status(
        email
    )
    session_record=latest_session_record(
        email
    )
    session_note=None

    if ai_status.get("worker")=="Running":
        session_start=ai_status.get("session_start")
        stored_end=None
    elif session_record:
        session_start=session_record[1]
        stored_end=session_record[2]
    else:
        session_start=ai_status.get("session_start")
        stored_end=None
        session_note=(
            "Older sessions were not saved with their own start/end record yet. "
            "From now on, every Start AI run will keep its own duration."
        )

    trades=get_session_trades(
        email,
        session_start
    )
    end_time=stored_end or session_end_time(
        ai_status,
        trades
    )
    profits=[
        float(trade.get("Profit") or 0)
        for trade in trades
    ]
    wins=[
        profit
        for profit in profits
        if profit>0
    ]
    losses=[
        profit
        for profit in profits
        if profit<0
    ]
    session_profit=round(
        sum(profits),
        2
    )
    win_rate=round(
        len(wins)/len(trades)*100,
        2
    ) if trades else 0.0
    average_win=round(
        sum(wins)/len(wins),
        2
    ) if wins else 0.0
    average_loss=round(
        sum(losses)/len(losses),
        2
    ) if losses else 0.0

    by_direction=summarize_group(
        trades,
        "Direction"
    )
    by_setup=add_confidence(
        summarize_group(
            trades,
            "Setup Type"
        )
    )
    by_ticker=add_confidence(
        summarize_group(
            trades,
            "Ticker"
        )
    )
    by_review=summarize_group(
        trades,
        "Review Label"
    )

    best_trade=max(
        trades,
        key=lambda trade:trade.get("Profit") or 0,
        default=None
    )
    worst_trade=min(
        trades,
        key=lambda trade:trade.get("Profit") or 0,
        default=None
    )

    thoughts=[]
    mistakes=[]
    improvement_plan=[]
    rule_requests=[]
    confidence_thoughts=[]

    if not trades:
        thoughts.append(
            "I did not close any trades in this session, so I do not have enough new trade evidence to judge myself."
        )
        mistakes.append(
            "I stayed too quiet, or my filters were too strict for the market I was watching."
        )
        improvement_plan.append(
            "Next session I will keep scanning, but I need to create enough small, controlled tests to learn from real outcomes."
        )
        rule_requests.append(
            "If I keep producing no trades, lower only the recovery-test threshold, not the normal trade threshold."
        )
    else:
        thoughts.append(
            f"I closed {len(trades)} trade(s) and finished this session with ${session_profit:.2f} P/L."
        )

        if session_profit>0:
            thoughts.append(
                "I ended green, so my next job is to repeat only the setups that produced clean profit without increasing risk too fast."
            )
            improvement_plan.append(
                "I will keep the winning setup sizes stable and check if they repeat well next session."
            )
        else:
            mistakes.append(
                "I lost money, which means my entries were not selective enough for this market."
            )
            improvement_plan.append(
                "I will make weak setups trade only as tiny recovery tests until they prove themselves."
            )

        if abs(average_loss)>average_win and losses:
            mistakes.append(
                "My average loss was bigger than my average win, so I was not getting enough reward for the risk I took."
            )
            improvement_plan.append(
                "I should not increase size until my average win is clearly larger than my average loss."
            )
            rule_requests.append(
                "Keep position size small until average win is greater than average loss for at least one full session."
            )

        early_failures=[
            trade
            for trade in trades
            if "Early failure" in (trade.get("Reason") or "")
        ]
        stop_losses=[
            trade
            for trade in trades
            if "Stop loss" in (trade.get("Reason") or "")
        ]
        tiny_wins=[
            trade
            for trade in trades
            if float(trade.get("Profit") or 0)>0 and "Take profit" not in (trade.get("Reason") or "")
        ]

        if early_failures:
            mistakes.append(
                f"I had {len(early_failures)} early-failure trade(s). I entered before the move had enough follow-through."
            )
            improvement_plan.append(
                "After repeated recent early failures, I will pause briefly, then only allow tiny recovery tests for the weak setup/direction."
            )
            rule_requests.append(
                "If I get 3 early failures in 30 minutes, pause new entries for 10 minutes instead of freezing for hours."
            )

        if stop_losses:
            mistakes.append(
                f"I hit stop loss {len(stop_losses)} time(s). That means my entry was too close to a reversal or I ignored stronger opposite pressure."
            )
            improvement_plan.append(
                "Before entering, I will demand that the confirmation candle still holds VWAP/trigger in my direction."
            )

        if tiny_wins and average_win>0 and average_win<abs(average_loss):
            mistakes.append(
                "My winners were too small compared with my losers, so I was not getting paid enough for the risk."
            )
            improvement_plan.append(
                "I should only scale size after the same setup proves it can produce wins larger than its losses."
            )

        if by_direction:
            weakest_direction=by_direction[0]
            strongest_direction=by_direction[-1]
            thoughts.append(
                f"My best direction was {strongest_direction['Direction']} (${strongest_direction['Total P/L']:.2f}). My weakest direction was {weakest_direction['Direction']} (${weakest_direction['Total P/L']:.2f})."
            )

            if weakest_direction["Total P/L"]<0:
                mistakes.append(
                    f"I handled {weakest_direction['Direction']} trades poorly; that direction lost ${abs(weakest_direction['Total P/L']):.2f}."
                )
                improvement_plan.append(
                    f"I will require stricter confirmation for {weakest_direction['Direction']} trades until my memory improves."
                )

        if by_setup:
            weakest_setup=by_setup[0]
            strongest_setup=by_setup[-1]
            thoughts.append(
                f"My best setup was {strongest_setup['Setup Type']} (${strongest_setup['Total P/L']:.2f}). My weakest setup was {weakest_setup['Setup Type']} (${weakest_setup['Total P/L']:.2f})."
            )

            if weakest_setup["Total P/L"]<0:
                mistakes.append(
                    f"I did not trade {weakest_setup['Setup Type']} well; it lost ${abs(weakest_setup['Total P/L']):.2f}."
                )
                improvement_plan.append(
                    f"I will keep {weakest_setup['Setup Type']} on probation sizing unless the live score is much stronger."
                )

        danger_setups=[
            row
            for row in by_setup
            if row.get("Confidence")=="danger"
        ]
        probation_setups=[
            row
            for row in by_setup
            if row.get("Confidence")=="probation"
        ]
        trusted_setups=[
            row
            for row in by_setup
            if row.get("Confidence")=="trusted"
        ]

        if trusted_setups:
            confidence_thoughts.append(
                "I trust these setups most right now: "+
                ", ".join(row["Setup Type"] for row in trusted_setups[:3])
            )

        if probation_setups:
            confidence_thoughts.append(
                "I will keep these setups small until they improve: "+
                ", ".join(row["Setup Type"] for row in probation_setups[:3])
            )

        if danger_setups:
            confidence_thoughts.append(
                "I will only use tiny test size for these dangerous setups: "+
                ", ".join(row["Setup Type"] for row in danger_setups[:3])
            )
            rule_requests.append(
                "Do not fully block danger setups; keep them tiny so I can still learn if they recover."
            )

    if not mistakes:
        mistakes.append(
            "I do not see a major mistake from the closed trades yet."
        )

    if not improvement_plan:
        improvement_plan.append(
            "I will keep collecting trades and compare the next session against this one."
        )

    if not rule_requests:
        rule_requests.append(
            "I do not need a new rule yet; I need another session to confirm if this behavior repeats."
        )

    return {
        "start":session_start,
        "end":end_time,
        "duration":format_duration_between(
            session_start,
            end_time
        ),
        "profit":session_profit,
        "trades":trades,
        "trade_count":len(trades),
        "win_rate":win_rate,
        "average_win":average_win,
        "average_loss":average_loss,
        "by_direction":by_direction,
        "by_setup":by_setup,
        "by_ticker":by_ticker,
        "by_review":by_review,
        "best_trade":best_trade,
        "worst_trade":worst_trade,
        "thoughts":thoughts,
        "mistakes":mistakes,
        "improvement_plan":improvement_plan,
        "rule_requests":rule_requests,
        "confidence_thoughts":confidence_thoughts,
        "session_note":session_note
    }


def get_ai_lessons(email,limit=8):

    conn,cursor=connect_db()

    cursor.execute("""
        SELECT created_at,source,lesson
        FROM ai_lessons
        WHERE email=? AND active=1
        ORDER BY id DESC
        LIMIT ?
    """,(
        email,
        limit
    ))

    rows=cursor.fetchall()
    conn.close()

    return [
        {
            "Created":row[0],
            "Source":row[1],
            "Lesson":row[2]
        }
        for row in rows
    ]


def render_live_account_metrics(email):

    summary=get_live_account_summary(
        email
    )

    st.session_state.balance=summary["balance"]
    st.session_state.profit=summary["profit"]
    st.session_state.trades_taken=summary["trades_taken"]

    a,b,c,d=st.columns(4)

    a.metric(
        "Balance",
        f"${summary['balance']:,.2f}"
    )

    b.metric(
        "Trades Taken",
        summary["trades_taken"]
    )

    c.metric(
        "Overall Profit",
        f"${summary['profit']:.2f}"
    )

def render_live_ai_panel(email):

    ai_status=get_live_ai_status(
        email
    )

    st.subheader("AI Status")

    best_recent=ai_status["best_recent"]
    last_activity=ai_status["last_activity"]

    h1,h2,h3,h4,h5=st.columns(5)

    h1.metric(
        "Worker",
        ai_status["worker"]
    )

    h2.metric(
        "Search",
        ai_status["searching"]
    )

    h3.metric(
        "Open Positions",
        ai_status["open_count"]
    )

    h4.metric(
        "Best Recent Setup",
        best_recent[0] if best_recent else "N/A"
    )

    h5.metric(
        "Best Recent Score",
        best_recent[1] if best_recent else "N/A"
    )

    s1,s2,s3=st.columns(3)

    s1.metric(
        "Session P/L",
        f"${ai_status['session_profit']:.2f}"
    )

    s2.metric(
        "Last Check",
        ai_status["last_check"]
    )

    s3.metric(
        "Last Activity",
        last_activity[2] if last_activity else "N/A"
    )

    st.info(
        ai_status["status"]
    )

    if ai_status["session_start"]:

        st.caption(
            f"Current simulation started at {ai_status['session_start']}"
        )

    if last_activity:

        st.caption(
            f"Latest activity: {last_activity[1]} was {last_activity[2]} at {last_activity[0]} - {last_activity[3]}"
        )

    open_positions=get_live_open_positions(
        email
    )

    if ai_status["worker"]=="Running" or open_positions:

        st.subheader("Open Positions")

        if open_positions:

            position_rows=[]

            for pos in open_positions:

                direction=pos.get("Direction","LONG")

                effective_tp=round_market_price(
                    pos["Entry"]*(1-TAKE_PROFIT_PCT)
                    if direction=="SHORT"
                    else pos["Entry"]*(1+TAKE_PROFIT_PCT)
                )

                effective_sl=round_market_price(
                    pos["Entry"]*(1+STOP_LOSS_PCT)
                    if direction=="SHORT"
                    else pos["Entry"]*(1-STOP_LOSS_PCT)
                )

                current=latest_price(
                    pos["Ticker"]
                )

                if current:

                    if direction=="SHORT":
                        price_move_profit=round(
                            (pos["Entry"]-current)*pos["Qty"],
                            2
                        )
                    else:
                        price_move_profit=round(
                            (current-pos["Entry"])*pos["Qty"],
                            2
                        )

                    unrealized_profit=estimated_net_profit_for_direction(
                        direction,
                        pos["Entry"],
                        current,
                        pos["Qty"],
                        pos.get("Ticker")
                    )

                    if direction=="SHORT":
                        distance_to_tp=round_market_price(current-effective_tp)
                        distance_to_sl=round_market_price(effective_sl-current)
                    else:
                        distance_to_tp=round_market_price(effective_tp-current)
                        distance_to_sl=round_market_price(current-effective_sl)


                    price_move_text=f"${price_move_profit:,.2f}"
                    profit_text=f"${unrealized_profit:,.2f}"
                    current_text=format_market_price(current)
                    tp_distance_text=format_market_price(distance_to_tp)
                    sl_distance_text=format_market_price(distance_to_sl)
                    status_text="In profit" if unrealized_profit>=0 else "In loss"

                else:

                    profit_text="N/A"
                    price_move_text="N/A"
                    current_text="N/A"
                    tp_distance_text="N/A"
                    sl_distance_text="N/A"
                    status_text="Waiting for price"

                position_rows.append({
                    "Ticker":pos["Ticker"],
                    "Direction":direction,
                    "Market":pos.get("Market") or "N/A",
                    "Score":pos.get("Score") if pos.get("Score") is not None else "N/A",
                    "RSI":pos.get("RSI") if pos.get("RSI") is not None else "N/A",
                    "Status":status_text,
                    "Entry":format_market_price(pos["Entry"]),
                    "Current":current_text,
                    "Price Move P/L":price_move_text,
                    "Net Open P/L":profit_text,
                    "Qty":f"{pos['Qty']:,.4f}",
                    "Position Size":(
                        f"${pos['Entry']*pos['Qty']*currency_to_usd_factor(pos.get('Ticker')):,.2f}"
                    ),
                    "Take Profit":format_market_price(effective_tp),
                    "Stop Loss":format_market_price(effective_sl),
                    "To TP":tp_distance_text,
                    "To SL":sl_distance_text,
                    "Entry Time":pos["Entry Time"]
                })

            st.dataframe(
                pd.DataFrame(position_rows),
                use_container_width=True,
                hide_index=True
            )

        else:

            st.caption("No open positions right now.")

    last_trade=get_last_closed_trade(
        email
    )

    st.subheader("Last Closed Trade")

    if last_trade:

        l1,l2,l3,l4,l5,l6=st.columns([2,2,2,2,3,1])

        l1.metric(
            "Ticker",
            last_trade["Ticker"]
        )

        l2.metric(
            "Entry",
            f"${last_trade['Entry']:,.2f}"
        )

        l3.metric(
            "Exit",
            f"${last_trade['Exit']:,.2f}"
        )

        l4.metric(
            "Profit",
            f"${last_trade['Profit']:,.2f}"
        )

        l5.write(
            last_trade["Reason"] or "N/A"
        )

        if l6.button("Replay",key=f"last_closed_{last_trade['Time']}_{last_trade['Ticker']}"):

            st.session_state.selected_trade_id=last_trade.get("ID")
            st.session_state.selected_trade=last_trade
            st.rerun()

    else:

        st.caption("No closed trades yet.")


def save_user_summary():

    if st.session_state.logged_in:

        cursor.execute("""
            UPDATE users
            SET balance=?, profit=?, trades_taken=?
            WHERE email=?
        """,(
            st.session_state.balance,
            st.session_state.profit,
            st.session_state.trades_taken,
            st.session_state.user_email
        ))

        conn.commit()

def save_open_position(pos):

    if st.session_state.logged_in:

        cursor.execute("""
            INSERT INTO open_positions_v2(
                email,ticker,entry,tp,sl,qty,entry_time,market,score,rsi,entry_reason,
                trigger_time,trigger_high,trigger_close,direction
            )
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,(
            st.session_state.user_email,
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

        pos["ID"]=cursor.lastrowid

def delete_open_position(pos_id):

    if st.session_state.logged_in and pos_id is not None:

        cursor.execute(
            "DELETE FROM open_positions_v2 WHERE id=?",
            (pos_id,)
        )

        conn.commit()

def save_closed_trade(trade):

    if st.session_state.logged_in:

        trade=review_trade_for_app(
            trade
        )

        cursor.execute("""
            INSERT INTO trades(
                email,time,ticker,entry,exit,profit,entry_time,exit_time,reason,
                market,score,rsi,direction,entry_reason,trigger_time,trigger_high,trigger_close,
                setup_type,review_label,review_notes,hold_minutes,move_pct
            )
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,(
            st.session_state.user_email,
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

        conn.commit()


def close_all_open_positions(reason):

    now=datetime.now()

    positions=(
        get_live_open_positions(st.session_state.user_email)
        if st.session_state.logged_in
        else list(st.session_state.open_positions)
    )

    for pos in positions:

        current=latest_price(
            pos["Ticker"]
        )

        if not current:
            current=pos["Entry"]

        direction=pos.get("Direction","LONG")

        exit_fill=exit_fill_for_direction(
            direction,
            current
        )

        fees=estimated_fees(
            pos["Entry"],
            exit_fill,
            pos["Qty"],
            pos.get("Ticker")
        )

        profit=profit_for_direction(
            direction,
            pos["Entry"],
            exit_fill,
            pos["Qty"],
            pos.get("Ticker")
        )

        trade={
            "Time":now.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "Ticker":pos["Ticker"],
            "Entry":pos["Entry"],
            "Exit":exit_fill,
            "Profit":profit,
            "Entry Time":pos["Entry Time"],
            "Exit Time":now.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "Reason":f"{reason} | estimated slippage/fees included",
            "Market":pos.get("Market"),
            "Score":pos.get("Score"),
            "RSI":pos.get("RSI"),
            "Direction":direction,
            "Entry Reason":pos.get("Entry Reason"),
            "Trigger Time":pos.get("Trigger Time"),
            "Trigger High":pos.get("Trigger High"),
            "Trigger Close":pos.get("Trigger Close")
        }

        st.session_state.history.insert(
            0,
            trade
        )

        st.session_state.balance+=profit
        st.session_state.profit+=profit
        st.session_state.trades_taken+=1

        save_closed_trade(
            trade
        )

        delete_open_position(
            pos.get("ID")
        )

    st.session_state.open_positions=[]

    if st.session_state.logged_in:

        cursor.execute(
            "DELETE FROM open_positions_v2 WHERE email=?",
            (st.session_state.user_email,)
        )

        cursor.execute("""
            UPDATE bot_state
            SET open_positions_count=0,
                last_heartbeat=?
            WHERE email=?
        """,(
            now.strftime("%Y-%m-%d %H:%M:%S"),
            st.session_state.user_email
        ))

        conn.commit()


def reset_guest():

    st.session_state.balance=START_BALANCE
    st.session_state.profit=0.0
    st.session_state.trades_taken=0
    st.session_state.history=[]
    st.session_state.open_positions=[]
    st.session_state.running=False
    st.session_state.selected_trade=None
    st.session_state.selected_trade_id=None
    st.session_state.selected_session_review=False

# ---------------- SESSION LEARNING PAGE ----------------

if st.session_state.selected_session_review:

    st.title("AI Learning Review")

    if st.button("Back"):

        st.session_state.selected_session_review=False
        st.rerun()

    if not st.session_state.logged_in:

        st.warning("Log in to see session learning from saved trade data.")
        st.stop()

    learning=build_session_learning(
        st.session_state.user_email
    )

    c1,c2,c3,c4=st.columns(4)

    c1.metric(
        "Session P/L",
        f"${learning['profit']:.2f}"
    )

    c2.metric(
        "Duration",
        learning["duration"]
    )

    c3.metric(
        "Closed Trades",
        learning["trade_count"]
    )

    c4.metric(
        "Win Rate",
        f"{learning['win_rate']:.2f}%"
    )

    st.caption(
        f"Session: {learning['start'] or 'N/A'} -> {learning['end'] or 'N/A'}"
    )

    if learning.get("session_note"):

        st.warning(
            learning["session_note"]
        )

    st.subheader("My Session Review")

    for thought in learning["thoughts"]:

        st.write(
            f"- {thought}"
        )

    st.subheader("What I Think I Did Wrong")

    for mistake in learning["mistakes"]:

        st.write(
            f"- {mistake}"
        )

    st.subheader("What I Will Improve Next Session")

    for plan in learning["improvement_plan"]:

        st.write(
            f"- {plan}"
        )

    st.subheader("What I Remember From Our Reviews")

    lessons=get_ai_lessons(
        st.session_state.user_email
    )

    if lessons:
        for lesson in lessons:
            st.write(
                f"- {lesson['Lesson']}"
            )
            st.caption(
                f"{lesson['Source']} | {lesson['Created']}"
            )
    else:
        st.caption(
            "No saved lessons yet."
        )

    if learning.get("confidence_thoughts"):

        st.subheader("How I Will Size The Next Trades")

        for thought in learning["confidence_thoughts"]:

            st.write(
                f"- {thought}"
            )

    st.subheader("Rules I Want You To Consider Changing")

    for request in learning["rule_requests"]:

        st.write(
            f"- {request}"
        )

    s1,s2=st.columns(2)

    s1.metric(
        "Average Win",
        f"${learning['average_win']:.2f}"
    )

    s2.metric(
        "Average Loss",
        f"${learning['average_loss']:.2f}"
    )

    best_trade=learning["best_trade"]
    worst_trade=learning["worst_trade"]

    if best_trade or worst_trade:

        b1,b2=st.columns(2)

        if best_trade:

            b1.subheader("Best Trade")
            b1.write(
                f"{best_trade['Ticker']} {best_trade.get('Direction','LONG')} | ${best_trade['Profit']:.2f}"
            )
            b1.caption(
                best_trade.get("Reason") or "No exit reason"
            )

        if worst_trade:

            b2.subheader("Worst Trade")
            b2.write(
                f"{worst_trade['Ticker']} {worst_trade.get('Direction','LONG')} | ${worst_trade['Profit']:.2f}"
            )
            b2.caption(
                worst_trade.get("Reason") or "No exit reason"
            )

    if learning["by_direction"]:

        st.subheader("Direction Review")
        st.dataframe(
            pd.DataFrame(learning["by_direction"]),
            use_container_width=True,
            hide_index=True
        )

    if learning["by_setup"]:

        st.subheader("Setup Confidence Review")
        st.dataframe(
            pd.DataFrame(learning["by_setup"]),
            use_container_width=True,
            hide_index=True
        )

    if learning["by_review"]:

        st.subheader("Mistake Pattern Review")
        st.dataframe(
            pd.DataFrame(learning["by_review"]),
            use_container_width=True,
            hide_index=True
        )

    if learning["by_ticker"]:

        st.subheader("Ticker Confidence Review")
        st.dataframe(
            pd.DataFrame(learning["by_ticker"]),
            use_container_width=True,
            hide_index=True
        )

    if learning["trades"]:

        st.subheader("Session Trades")
        rows=[
            {
                "Ticker":trade["Ticker"],
                "Direction":trade.get("Direction","LONG"),
                "Setup":trade.get("Setup Type") or "Unknown",
                "Entry":format_market_price(trade["Entry"]),
                "Exit":format_market_price(trade["Exit"]),
                "Profit":f"${trade['Profit']:.2f}",
                "AI Review":trade.get("Review Label") or "N/A",
                "AI Notes":trade.get("Review Notes") or "N/A",
                "Reason":trade.get("Reason") or "N/A",
                "Time":trade["Time"]
            }
            for trade in learning["trades"]
        ]
        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True
        )

    st.stop()

# ---------------- TRADE PAGE ----------------

if st.session_state.selected_trade_id and st.session_state.logged_in:

    st.session_state.selected_trade=get_trade_by_id(
        st.session_state.user_email,
        st.session_state.selected_trade_id
    )

if st.session_state.selected_trade:

    trade=st.session_state.selected_trade

    st.title(
        f"{trade['Ticker']} Trade"
    )

    if st.button("Back"):

        st.session_state.selected_trade=None
        st.session_state.selected_trade_id=None
        st.rerun()

    a,b,c=st.columns(3)

    a.metric(
        "Entry",
        format_market_price(trade["Entry"])
    )

    b.metric(
        "Exit",
        format_market_price(trade["Exit"])
    )

    c.metric(
        "Profit",
        f"${trade['Profit']:.2f}"
    )

    duration_minutes=trade_duration_minutes(trade)
    move_pct=trade_move_pct(trade)
    position_size=estimated_position_size(trade)

    d1,d2,d3,d4,d5,d6=st.columns(6)

    d1.metric(
        "Market",
        trade.get("Market") or "N/A"
    )

    d2.metric(
        "Score",
        trade.get("Score") if trade.get("Score") is not None else "N/A"
    )

    d3.metric(
        "RSI",
        trade.get("RSI") if trade.get("RSI") is not None else "N/A"
    )

    d4.metric(
        "Hold",
        f"{duration_minutes} min" if duration_minutes is not None else "N/A"
    )

    d5.metric(
        "Move",
        f"{move_pct:.3f}%" if move_pct is not None else "N/A"
    )

    d6.metric(
        "Direction",
        trade.get("Direction","LONG")
    )

    r1,r2=st.columns(2)

    r1.metric(
        "Setup",
        trade.get("Setup Type") or "N/A"
    )

    r2.metric(
        "AI Review",
        trade.get("Review Label") or "Pending"
    )

    if trade.get("Review Notes"):

        st.info(
            trade.get("Review Notes")
        )

    if trade.get("Trigger Time"):

        st.caption(
            f"Trigger candle: {trade.get('Trigger Time')} | "
            f"High: {trade.get('Trigger High','N/A')} | "
            f"Close: {trade.get('Trigger Close','N/A')}"
        )

    t1,t2,t3=st.columns(3)

    t1.caption(
        f"Entry time: {trade.get('Entry Time','N/A')}"
    )

    t2.caption(
        f"Exit time: {trade.get('Exit Time','N/A')}"
    )

    t3.caption(
        f"Estimated position: ${position_size:,.2f}" if position_size else "Estimated position: N/A"
    )

    strategy_parts=split_strategy_reason(
        trade.get("Entry Reason")
    )

    data=get_chart_data(
        trade["Ticker"]
    )

    if not data.empty:

        data=clean_data(data)

        entry_time=nearest_chart_time(
            data,
            trade.get("Entry Time")
        )

        exit_time=nearest_chart_time(
            data,
            trade.get("Exit Time")
        )

        trigger_time=nearest_chart_time(
            data,
            trade.get("Trigger Time")
        )

        data=crop_trade_window(
            data,
            entry_time,
            exit_time
        )

        fig=go.Figure()

        fig.add_trace(
            go.Candlestick(
                x=data.index,
                open=data["Open"],
                high=data["High"],
                low=data["Low"],
                close=data["Close"],
                increasing_line_color="green",
                decreasing_line_color="red",
                name="1m Candles"
            )
        )

        if entry_time is not None:

            entry_label="SELL SHORT" if trade.get("Direction","LONG")=="SHORT" else "BUY"
            entry_color="red" if trade.get("Direction","LONG")=="SHORT" else "blue"

            fig.add_trace(
                go.Scatter(
                    x=[entry_time],
                    y=[trade["Entry"]],
                    mode="markers+text",
                    text=[
                        f"{entry_label} {format_market_price(trade['Entry'])}"
                    ],
                    textposition="top center",
                    marker=dict(
                        size=14,
                        color=entry_color
                    ),
                    name=entry_label
                )
            )

            fig.add_vline(
                x=entry_time,
                line_width=1,
                line_dash="dot",
                line_color=entry_color
            )

        if trigger_time is not None:

            trigger_price=trade.get("Trigger Close") or trade.get("Entry")

            fig.add_trace(
                go.Scatter(
                    x=[trigger_time],
                    y=[trigger_price],
                    mode="markers+text",
                    text=["TRIGGER"],
                    textposition="top center",
                    marker=dict(
                        size=12,
                        color="orange",
                        symbol="diamond"
                    ),
                    name="TRIGGER"
                )
            )

            fig.add_vline(
                x=trigger_time,
                line_width=1,
                line_dash="dot",
                line_color="orange"
            )

        if exit_time is not None:

            exit_label="BUY COVER" if trade.get("Direction","LONG")=="SHORT" else "SELL"
            exit_color="blue" if trade.get("Direction","LONG")=="SHORT" else "red"

            fig.add_trace(
                go.Scatter(
                    x=[exit_time],
                    y=[trade["Exit"]],
                    mode="markers+text",
                    text=[
                        f"{exit_label} {format_market_price(trade['Exit'])}"
                    ],
                    textposition="bottom center",
                    marker=dict(
                        size=14,
                        color=exit_color
                    ),
                    name=exit_label
                )
            )

            fig.add_vline(
                x=exit_time,
                line_width=1,
                line_dash="dot",
                line_color=exit_color
            )

        fig.update_layout(
            height=700,
            xaxis_rangeslider_visible=False,
            title="1-minute trade window",
            xaxis_title="Time",
            yaxis_title="Price",
            xaxis=dict(
                tickformat="%H:%M",
                showgrid=True
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:

        st.warning(
            "No 1-minute chart data was available for this trade. The trade details and strategy are still shown above."
        )

    st.subheader("AI Strategy")

    if strategy_parts:

        st.dataframe(
            pd.DataFrame(
                {
                    "Signal Used By AI":strategy_parts
                }
            ),
            use_container_width=True,
            hide_index=True
        )

    else:

        st.caption("No stored strategy details for this older trade.")

    st.subheader(
        "AI Trade Explanation"
    )

    st.info(
        f"""
Trade entered because:

{trade.get("Entry Reason") or "No stored entry reason available for this older trade."}

Exit reason:
{trade.get("Reason","N/A")}
"""
    )

    st.stop()

# ---------------- MAIN PAGE ----------------

st.title("AI Trader")

left,right=st.columns([8,2])

with right:

    if st.session_state.logged_in:

        if st.button("Profile",key="profile_icon"):

            st.session_state.show_profile_menu=not st.session_state.show_profile_menu

        if st.session_state.show_profile_menu:

            st.caption(
                st.session_state.user_email
            )

            if st.button("Logout",key="logout_button"):

                save_user_summary()

                st.session_state.logged_in=False
                st.session_state.user_email=""
                st.session_state.show_profile_menu=False

                reset_guest()

                st.rerun()

    else:

        with st.expander("Sign Up"):

            signup_email=st.text_input(
                "Email",
                key="signup_email_new"
            )

            signup_password=st.text_input(
                "Password",
                type="password",
                key="signup_password_new"
            )

            if st.button(
                "Create Account",
                key="signup_button_new"
            ):

                cursor.execute(
                    "SELECT * FROM users WHERE email=?",
                    (signup_email,)
                )

                existing=cursor.fetchone()

                if existing:

                    st.error("Email already exists")

                else:

                    cursor.execute("""
                        INSERT INTO users(email,password,balance,profit,trades_taken)
                        VALUES(?,?,?,?,?)
                    """,(
                        signup_email,
                        hash_password(signup_password),
                        START_BALANCE,
                        0.0,
                        0
                    ))

                    conn.commit()

                    st.session_state.logged_in=True
                    st.session_state.user_email=signup_email
                    st.session_state.show_profile_menu=False

                    load_user_data(
                        signup_email
                    )

                    st.rerun()

        with st.expander("Log In"):

            login_email=st.text_input(
                "Email",
                key="login_email_new"
            )

            login_password=st.text_input(
                "Password",
                type="password",
                key="login_password_new"
            )

            if st.button(
                "Log In",
                key="login_button_new"
            ):

                cursor.execute("""
                    SELECT * FROM users
                    WHERE email=? AND password=?
                """,(
                    login_email,
                    hash_password(login_password)
                ))

                user=cursor.fetchone()

                if user:

                    st.session_state.logged_in=True
                    st.session_state.user_email=login_email
                    st.session_state.show_profile_menu=False

                    load_user_data(
                        login_email
                    )

                    st.rerun()

                else:

                    st.error(
                        "Wrong email or password"
                    )

if st.session_state.logged_in:

    load_user_data(
        st.session_state.user_email
    )

# ---------------- TWELVE DATA STATUS ----------------

if not twelvedata_ready:
    st.warning(
        "Twelve Data is not connected. Check your .env file."
    )
else:
    st.success(
        "Twelve Data connected"
    )

# ---------------- ACCOUNT METRICS ----------------


if st.session_state.logged_in:

    render_live_account_metrics(
        st.session_state.user_email
    )

else:

    a,b,c,d=st.columns(4)

    a.metric(
        "Balance",
        f"${st.session_state.balance:,.2f}"
    )
    b.metric(
        "Trades Taken",
        st.session_state.trades_taken
    )

    c.metric(
        "Overall Profit",
        f"${st.session_state.profit:.2f}"
    )

if st.session_state.logged_in:

    st.caption(
        "The trading worker is managed by the always-on supervisor. "
        "This dashboard only displays data."
    )

    evaluation_window=get_current_evaluation_window(
        st.session_state.user_email
    )

    if evaluation_window:

        st.subheader("Current Evaluation Window")
        w1,w2,w3,w4=st.columns(4)
        w1.metric(
            "Window P/L",
            f"${evaluation_window['profit']:.2f}"
        )
        w2.metric(
            "Trades",
            evaluation_window["trades"]
        )
        w3.metric(
            "Status",
            evaluation_window["status"].title()
        )
        w4.metric(
            "Time Remaining",
            evaluation_window["remaining"]
        )
        st.progress(
            evaluation_window["progress"]
        )
        st.caption(
            f"{evaluation_window['start_time']} -> "
            f"{evaluation_window['planned_end_time']}"
        )
    else:

        st.info(
            "The always-on supervisor has not created an evaluation window yet."
        )

    render_live_ai_panel(
        st.session_state.user_email
    )

    if StrategyLabRepository is not None:

        with st.expander("Strategy V2 Lab"):

            try:

                strategy_lab=StrategyLabRepository()
                latest_experiment=strategy_lab.latest_experiment()
                latest_backtests=strategy_lab.latest_backtests()

                st.caption(
                    "5-minute entries, 15-minute confirmation, ATR/ADX risk controls, "
                    "and champion/challenger backtesting. This lab does not change the "
                    "current paper worker until a candidate is accepted."
                )

                if latest_experiment:

                    e1,e2,e3=st.columns(3)
                    e1.metric(
                        "Last Candidate",
                        latest_experiment["candidate_version"]
                    )
                    e2.metric(
                        "Parameter",
                        latest_experiment["parameter"]
                    )
                    e3.metric(
                        "Decision",
                        "Accepted" if latest_experiment["accepted"] else "Rejected"
                    )

                    st.write(
                        f"{latest_experiment['old_value']} -> "
                        f"{latest_experiment['new_value']} | "
                        f"{latest_experiment['reason']}"
                    )
                else:

                    st.info(
                        "Version 2 is ready. No real historical experiment has been run yet."
                    )

                if latest_backtests:

                    st.dataframe(
                        pd.DataFrame(latest_backtests),
                        use_container_width=True,
                        hide_index=True
                    )

            except Exception as exc:

                st.caption(
                    f"Strategy lab is temporarily unavailable: {exc}"
                )

# ---------------- PERFORMANCE STATS ----------------

if st.session_state.history:

    df=pd.DataFrame(
        st.session_state.history
    )

    wins=len(
        df[df["Profit"]>0]
    )

    losses=len(
        df[df["Profit"]<=0]
    )

    win_rate=round(
        (wins/len(df))*100,
        2
    )

    avg_win=round(
        df[df["Profit"]>0]["Profit"].mean(),
        2
    ) if wins>0 else 0

    avg_loss=round(
        df[df["Profit"]<=0]["Profit"].mean(),
        2
    ) if losses>0 else 0

    s1,s2,s3=st.columns(3)

    s1.metric(
        "Win Rate",
        f"{win_rate}%"
    )

    s2.metric(
        "Average Win",
        f"${avg_win}"
    )

    s3.metric(
        "Average Loss",
        f"${avg_loss}"
    )

# ---------------- SCANNER ----------------

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
            signal_range=max(signal_high-signal_low,price*0.0001)
            avg_range=(high-low).tail(20).mean()
            signal_close_position=(signal_close-signal_low)/signal_range
            trend_strength=(float(ema3.iloc[-1])-float(ema21.iloc[-1]))/price
            current_holds_trigger=price>=signal_close
            pullback_to_ema8=(
                float(low.tail(5).min())<=float(ema8.iloc[-1]) and
                price>float(ema3.iloc[-1])
            )
            trigger_confirmed=(
                signal_close>signal_open and
                signal_close>previous_high and
                signal_range<=float(avg_range)*2.5
            )
            continuation_confirmed=(
                current_holds_trigger and
                price>float(ema3.iloc[-1])>float(ema8.iloc[-1]) and
                three_min_change>0 and
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

            volatility=max(
                recent_range,
                price*0.0015
            )

            results.append({
                "Ticker":symbol,
                "Price":round(price,2),
                "Score":score,
                "RSI":round(float(rsi),2),
                "Volatility":round(volatility,2),
                "Reason":", ".join(reasons) or "no 1m setup"
            })

        except:
            pass

    return sorted(
        results,
        key=lambda x:x["Score"],
        reverse=True
    )


st.subheader("1-Minute Scanner")

tab1,tab2,tab3,tab4,tab5=st.tabs([
    "Crypto",
    "Stocks",
    "Europe",
    "Asia",
    "Futures"
])

with tab1:

    crypto_results=scan(
        WATCHLISTS["Crypto"]
    )

    for x in crypto_results[:10]:

        st.write(
            f"{x['Ticker']} | Score:{x['Score']} | RSI:{x['RSI']} | {x['Reason']}"
        )

with tab2:

    stock_results=scan(
        WATCHLISTS["Stocks"]
    )

    for x in stock_results[:10]:

        st.write(
            f"{x['Ticker']} | Score:{x['Score']} | RSI:{x['RSI']} | {x['Reason']}"
        )

with tab3:

    europe_results=scan(
        WATCHLISTS["Europe Stocks"]
    )

    for x in europe_results[:10]:

        st.write(
            f"{x['Ticker']} | Score:{x['Score']} | RSI:{x['RSI']} | {x['Reason']}"
        )

with tab4:

    asia_results=scan(
        WATCHLISTS["Asia Stocks"]
    )

    for x in asia_results[:10]:

        st.write(
            f"{x['Ticker']} | Score:{x['Score']} | RSI:{x['RSI']} | {x['Reason']}"
        )

with tab5:

    futures_results=scan(
        WATCHLISTS["Futures"]
    )

    for x in futures_results[:10]:

        st.write(
            f"{x['Ticker']} | Score:{x['Score']} | RSI:{x['RSI']} | {x['Reason']}"
        )

all_candidates=stock_results+crypto_results+futures_results

all_candidates=sorted(
    all_candidates,
    key=lambda x:x["Score"],
    reverse=True
)

# ---------------- AI LEARNING ----------------

st.subheader("AI Learning")

if st.session_state.logged_in:

    learning_summary=build_session_learning(
        st.session_state.user_email
    )

    l1,l2,l3,l4,l5=st.columns([2,2,2,2,1])

    l1.metric(
        "Session P/L",
        f"${learning_summary['profit']:.2f}"
    )

    l2.metric(
        "Duration",
        learning_summary["duration"]
    )

    l3.metric(
        "Closed Trades",
        learning_summary["trade_count"]
    )

    l4.metric(
        "Win Rate",
        f"{learning_summary['win_rate']:.2f}%"
    )

    if l5.button(
        "View",
        key=f"view_session_learning_{learning_summary.get('start') or 'none'}"
    ):

        st.session_state.selected_session_review=True
        st.rerun()

    if learning_summary["thoughts"]:

        st.caption(
            learning_summary["thoughts"][0]
        )

    if learning_summary.get("confidence_thoughts"):

        st.caption(
            learning_summary["confidence_thoughts"][0]
        )

else:

    st.caption("Log in to see AI session learning.")

# ---------------- PAPER TRADE ENGINE ----------------

if False and st.session_state.running:

    now=datetime.now()

    closed_positions=[]
    opened_count=0
    skipped_no_price=0

    for pos in st.session_state.open_positions:

        current=latest_price(
            pos["Ticker"]
        )

        if not current:
            continue

        effective_tp=round(
            pos["Entry"]*(1+TAKE_PROFIT_PCT),
            2
        )

        effective_sl=round(
            pos["Entry"]*(1-STOP_LOSS_PCT),
            2
        )

        entry_time=datetime.strptime(
            pos["Entry Time"],
            "%Y-%m-%d %H:%M:%S"
        )

        max_hold=now-entry_time>=timedelta(
            minutes=MAX_HOLD_MINUTES
        )

        exit_reason=None

        if current>=effective_tp:

            exit_reason="Take profit reached"

        elif current<=effective_sl:

            exit_reason="Stop loss reached"

        elif max_hold:

            exit_reason="Max hold time reached"

        if exit_reason:

            profit=round(
                (current-pos["Entry"])*pos["Qty"],
                2
            )

            trade={
                "Time":now.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "Ticker":pos["Ticker"],
                "Entry":pos["Entry"],
                "Exit":current,
                "Profit":profit,
                "Entry Time":pos["Entry Time"],
                "Exit Time":now.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "Reason":exit_reason
            }

            st.session_state.history.insert(
                0,
                trade
            )

            st.session_state.balance+=profit
            st.session_state.profit+=profit
            st.session_state.trades_taken+=1

            save_closed_trade(
                trade
            )

            delete_open_position(
                pos.get("ID")
            )

            closed_positions.append(
                pos
            )

    for pos in closed_positions:

        if pos in st.session_state.open_positions:

            st.session_state.open_positions.remove(
                pos
            )

    open_tickers=[
        p["Ticker"]
        for p in st.session_state.open_positions
    ]

    slots=MAX_OPEN_POSITIONS-len(
        st.session_state.open_positions
    )

    start_slots=slots

    for candidate in all_candidates:

        if slots<=0:
            break

        if candidate["Ticker"] in open_tickers:
            continue

        if candidate["Score"]<MIN_SCORE_TO_TRADE:
            continue

        entry=latest_price(
            candidate["Ticker"]
        )

        if not entry:
            skipped_no_price+=1
            continue

        qty=round(
            POSITION_CASH/entry,
            4
        )

        tp=round(
            entry*(1+TAKE_PROFIT_PCT),
            2
        )

        sl=round(
            entry*(1-STOP_LOSS_PCT),
            2
        )

        pos={
            "ID":None,
            "Ticker":candidate["Ticker"],
            "Entry":entry,
            "TP":tp,
            "SL":sl,
            "Qty":qty,
            "Entry Time":now.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        }

        st.session_state.open_positions.append(
            pos
        )

        save_open_position(
            pos
        )

        slots-=1
        opened_count+=1

    save_user_summary()

    best_score=all_candidates[0]["Score"] if all_candidates else "N/A"

    if opened_count>0 or closed_positions:

        st.session_state.ai_status=(
            f"AI checked the market at {now.strftime('%H:%M:%S')}. "
            f"Opened {opened_count} trade(s), closed {len(closed_positions)} trade(s)."
        )

    elif start_slots<=0:

        st.session_state.ai_status=(
            f"AI checked the market at {now.strftime('%H:%M:%S')}. "
            f"No new trades because the max open positions limit is reached."
        )

    else:

        st.session_state.ai_status=(
            f"AI checked the market at {now.strftime('%H:%M:%S')}. "
            f"No new trades. Best scanner score is {best_score}; minimum required is {MIN_SCORE_TO_TRADE}."
        )

        if skipped_no_price>0:

            st.session_state.ai_status+=(
                f" {skipped_no_price} candidate(s) had no live price."
            )

# ---------------- OPEN POSITIONS ----------------

if False and (st.session_state.running or st.session_state.open_positions):

    st.subheader("Open Positions")

    if st.session_state.running:

        st.info(
            st.session_state.ai_status
        )

    if st.session_state.open_positions:

        position_rows=[]

        for pos in st.session_state.open_positions:

            effective_tp=round(
                pos["Entry"]*(1+TAKE_PROFIT_PCT),
                2
            )

            effective_sl=round(
                pos["Entry"]*(1-STOP_LOSS_PCT),
                2
            )

            current=latest_price(
                pos["Ticker"]
            )

            if current:

                unrealized_profit=round(
                    (current-pos["Entry"])*pos["Qty"],
                    2
                )

                distance_to_tp=round(
                    effective_tp-current,
                    2
                )

                distance_to_sl=round(
                    current-effective_sl,
                    2
                )

                profit_text=f"${unrealized_profit:,.2f}"
                current_text=f"${current:,.2f}"
                tp_distance_text=f"${distance_to_tp:,.2f}"
                sl_distance_text=f"${distance_to_sl:,.2f}"
                status_text="In profit" if unrealized_profit>=0 else "In loss"

            else:

                profit_text="N/A"
                current_text="N/A"
                tp_distance_text="N/A"
                sl_distance_text="N/A"
                status_text="Waiting for price"

            position_rows.append({
                "Ticker":pos["Ticker"],
                "Market":pos.get("Market") or "N/A",
                "Score":pos.get("Score") if pos.get("Score") is not None else "N/A",
                "RSI":pos.get("RSI") if pos.get("RSI") is not None else "N/A",
                "Status":status_text,
                "Entry":f"${pos['Entry']:,.2f}",
                "Current":current_text,
                "Open Profit":profit_text,
                "Qty":f"{pos['Qty']:,.4f}",
                "Take Profit":f"${effective_tp:,.2f}",
                "Stop Loss":f"${effective_sl:,.2f}",
                "To TP":tp_distance_text,
                "To SL":sl_distance_text,
                "Entry Time":pos["Entry Time"]
            })

        st.dataframe(
            pd.DataFrame(position_rows),
            use_container_width=True,
            hide_index=True
        )

    else:

        st.caption("No open positions right now.")
# ---------------- HISTORY ----------------

if True:

    st.subheader("Trade History")

    for i,trade in enumerate(
        st.session_state.history
    ):

        h1,h2,h3,h4,h5,h6=st.columns([
            2,2,2,2,2,1
        ])

        h1.write(
            trade["Ticker"]
        )

        h2.write(
            f"${trade['Entry']:.2f}"
        )

        h3.write(
            f"${trade['Exit']:.2f}"
        )

        h4.write(
            f"${trade['Profit']:.2f}"
        )

        h5.write(
            trade["Time"]
        )

        if h6.button(
            "View",
            key=f"view_trade_{trade.get('ID',i)}"
        ):

            st.session_state.selected_trade_id=trade.get("ID")
            st.session_state.selected_trade=trade
            st.rerun()
