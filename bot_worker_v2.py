import os
import sys
import time
import sqlite3
from datetime import datetime

import pandas as pd
import yfinance as yf
from dotenv import load_dotenv

# ============================================
# STRATEGY V2: 5-minute RSI bounce swing trades
# ============================================

TICKERS=[
    "SPY","QQQ","BTC-USD","ETH-USD","AAPL","NVDA","TSLA"
]

POSITION_CASH=5000.0
MAX_OPEN_POSITIONS=4
TAKE_PROFIT_PCT=0.015
STOP_LOSS_PCT=0.005
MAX_HOLD_MINUTES=60

RSI_OVERSOLD=35
RSI_OVERBOUGHT=65
VOLUME_THRESHOLD=1.3

SCAN_INTERVAL_SECONDS=30
POSITION_CHECK_SECONDS=5

load_dotenv()
DB_PATH="users.db"

_trend_cache={}
TREND_CACHE_SECONDS=180


def connect_db():
    conn=sqlite3.connect(DB_PATH,timeout=30,check_same_thread=False)
    cursor=conn.cursor()
    try:
        cursor.execute("PRAGMA journal_mode=WAL")
    except sqlite3.OperationalError:
        pass
    cursor.execute("PRAGMA busy_timeout=30000")
    ensure_tables(cursor,conn)
    return conn,cursor


def ensure_tables(cursor,conn):
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
    CREATE TABLE IF NOT EXISTS bot_state(
        email TEXT PRIMARY KEY,
        running INTEGER DEFAULT 0,
        pid INTEGER,
        status TEXT,
        last_heartbeat TEXT,
        best_ticker TEXT,
        best_score REAL,
        open_positions_count INTEGER DEFAULT 0,
        today_profit REAL DEFAULT 0,
        session_start_time TEXT,
        searching_enabled INTEGER DEFAULT 1
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
        entry_time TEXT,
        market TEXT,
        score REAL,
        rsi REAL,
        direction TEXT DEFAULT 'LONG',
        entry_reason TEXT,
        trigger_time TEXT,
        trigger_high REAL,
        trigger_close REAL
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
        reason TEXT,
        market TEXT,
        score REAL,
        rsi REAL,
        direction TEXT DEFAULT 'LONG',
        entry_reason TEXT
    )
    """)
    conn.commit()


def calculate_rsi(close,period=14):
    delta=close.diff()
    gain=delta.where(delta>0,0).rolling(period).mean()
    loss=-delta.where(delta<0,0).rolling(period).mean()
    rs=gain/loss
    return 100-(100/(1+rs))


def get_15min_trend(ticker):
    now_ts=time.time()
    if ticker in _trend_cache:
        cache_ts,trend=_trend_cache[ticker]
        if now_ts-cache_ts<TREND_CACHE_SECONDS:
            return trend
    try:
        data=yf.download(
            ticker,period="5d",interval="15m",
            progress=False,auto_adjust=True
        )
        if data.empty or len(data)<50:
            _trend_cache[ticker]=(now_ts,"flat")
            return "flat"
        close=data["Close"].squeeze()
        ema20=close.rolling(20).mean()
        ema50=close.rolling(50).mean()
        last_close=float(close.iloc[-1])
        last_ema20=float(ema20.iloc[-1])
        last_ema50=float(ema50.iloc[-1])
        if last_ema20>last_ema50 and last_close>last_ema20:
            trend="up"
        elif last_ema20<last_ema50 and last_close<last_ema20:
            trend="down"
        else:
            trend="flat"
        _trend_cache[ticker]=(now_ts,trend)
        return trend
    except Exception:
        _trend_cache[ticker]=(now_ts,"flat")
        return "flat"


def scan_for_signal(ticker):
    try:
        data=yf.download(
            ticker,period="2d",interval="5m",
            progress=False,auto_adjust=True
        )
        if data.empty or len(data)<30:
            return None

        close=data["Close"].squeeze()
        open_p=data["Open"].squeeze()
        volume=data["Volume"].squeeze() if "Volume" in data.columns else None

        rsi_series=calculate_rsi(close)
        rsi_now=float(rsi_series.iloc[-1])
        rsi_prev=float(rsi_series.iloc[-2])

        price=float(close.iloc[-1])
        last_close=float(close.iloc[-1])
        last_open=float(open_p.iloc[-1])
        prev_close=float(close.iloc[-2])

        vol_surge=False
        vol_ratio=1.0
        if volume is not None:
            avg_vol=float(volume.rolling(20).mean().iloc[-1])
            current_vol=float(volume.iloc[-1])
            if avg_vol>0:
                vol_ratio=current_vol/avg_vol
                vol_surge=vol_ratio>VOLUME_THRESHOLD

        trend=get_15min_trend(ticker)

        long_signal=(
            rsi_prev<RSI_OVERSOLD and
            rsi_now>rsi_prev and
            last_close>last_open and
            last_close>prev_close and
            trend in ("up","flat") and
            vol_surge
        )

        short_signal=(
            rsi_prev>RSI_OVERBOUGHT and
            rsi_now<rsi_prev and
            last_close<last_open and
            last_close<prev_close and
            trend in ("down","flat") and
            vol_surge
        )

        if long_signal:
            return {
                "ticker":ticker,
                "direction":"LONG",
                "price":price,
                "rsi":rsi_now,
                "trend":trend,
                "volume_ratio":vol_ratio,
                "reason":(
                    f"5m RSI bounce ({rsi_prev:.0f}->{rsi_now:.0f}), "
                    f"15m {trend}, vol {vol_ratio:.1f}x avg"
                )
            }
        if short_signal:
            return {
                "ticker":ticker,
                "direction":"SHORT",
                "price":price,
                "rsi":rsi_now,
                "trend":trend,
                "volume_ratio":vol_ratio,
                "reason":(
                    f"5m RSI rejection ({rsi_prev:.0f}->{rsi_now:.0f}), "
                    f"15m {trend}, vol {vol_ratio:.1f}x avg"
                )
            }
        return None
    except Exception:
        return None


def get_open_positions(cursor,email):
    cursor.execute("""
        SELECT id,ticker,entry,tp,sl,qty,entry_time,direction,score,rsi,entry_reason
        FROM open_positions_v2 WHERE email=?
    """,(email,))
    rows=cursor.fetchall()
    return [
        {
            "id":r[0],"ticker":r[1],"entry":r[2],"tp":r[3],"sl":r[4],
            "qty":r[5],"entry_time":r[6],"direction":r[7] or "LONG",
            "score":r[8] or 20.0,"rsi":r[9] or 50.0,"entry_reason":r[10]
        }
        for r in rows
    ]


def get_latest_price(ticker):
    try:
        data=yf.download(
            ticker,period="1d",interval="1m",
            progress=False,auto_adjust=True
        )
        if data.empty:
            return None
        return float(data["Close"].iloc[-1])
    except Exception:
        return None


def open_position(cursor,conn,email,signal):
    direction=signal["direction"]
    price=signal["price"]

    if direction=="LONG":
        tp=price*(1+TAKE_PROFIT_PCT)
        sl=price*(1-STOP_LOSS_PCT)
    else:
        tp=price*(1-TAKE_PROFIT_PCT)
        sl=price*(1+STOP_LOSS_PCT)

    qty=POSITION_CASH/price
    now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO open_positions_v2(
            email,ticker,entry,tp,sl,qty,entry_time,market,score,rsi,
            direction,entry_reason,trigger_time,trigger_high,trigger_close
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """,(
        email,signal["ticker"],price,tp,sl,qty,now,"V2",
        20.0,signal["rsi"],direction,signal["reason"],
        now,price,price
    ))
    conn.commit()

    print(f"[OPEN] {direction} {signal['ticker']} @ ${price:.2f} | {signal['reason']}")


def close_position(cursor,conn,email,pos,exit_price,reason,profit_dollars):
    now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("DELETE FROM open_positions_v2 WHERE id=?",(pos["id"],))

    cursor.execute("""
        INSERT INTO trades(
            email,time,ticker,entry,exit,profit,entry_time,exit_time,reason,
            market,score,rsi,direction,entry_reason
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """,(
        email,now,pos["ticker"],pos["entry"],exit_price,profit_dollars,
        pos["entry_time"],now,reason,"V2",pos["score"],
        pos["rsi"],pos["direction"],pos.get("entry_reason")
    ))

    cursor.execute("""
        UPDATE users
        SET balance=balance+?,profit=profit+?,trades_taken=trades_taken+1
        WHERE email=?
    """,(profit_dollars,profit_dollars,email))

    conn.commit()

    print(f"[CLOSE] {pos['direction']} {pos['ticker']} @ ${exit_price:.2f} P/L: ${profit_dollars:.2f} | {reason}")


def check_position(cursor,conn,email,pos):
    current=get_latest_price(pos["ticker"])
    if not current:
        return

    direction=pos["direction"]
    entry_time=datetime.strptime(pos["entry_time"],"%Y-%m-%d %H:%M:%S")
    hold_minutes=(datetime.now()-entry_time).total_seconds()/60

    if direction=="LONG":
        profit_pct=(current-pos["entry"])/pos["entry"]
        hit_tp=current>=pos["tp"]
        hit_sl=current<=pos["sl"]
    else:
        profit_pct=(pos["entry"]-current)/pos["entry"]
        hit_tp=current<=pos["tp"]
        hit_sl=current>=pos["sl"]

    profit_dollars=profit_pct*(pos["entry"]*pos["qty"])

    exit_reason=None
    if hit_tp:
        exit_reason="Take profit reached"
    elif hit_sl:
        exit_reason="Stop loss reached"
    elif hold_minutes>=MAX_HOLD_MINUTES:
        exit_reason=f"Max hold time ({MAX_HOLD_MINUTES} min) reached"

    if exit_reason:
        close_position(cursor,conn,email,pos,current,exit_reason,profit_dollars)


def update_bot_state(cursor,conn,email,status,running=True):
    now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO bot_state(email,running,pid,status,last_heartbeat)
        VALUES(?,?,?,?,?)
        ON CONFLICT(email) DO UPDATE SET
            running=excluded.running,
            pid=excluded.pid,
            status=excluded.status,
            last_heartbeat=excluded.last_heartbeat
    """,(email,1 if running else 0,os.getpid(),status,now))
    conn.commit()


def ensure_user_exists(cursor,conn,email):
    cursor.execute("SELECT email FROM users WHERE email=?",(email,))
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO users(email,password,balance,profit,trades_taken)
            VALUES(?,?,?,?,?)
        """,(email,"",50000.0,0.0,0))
        conn.commit()


def main():
    if len(sys.argv)<2:
        print("Usage: python bot_worker_v2.py <email> [--duration N]")
        return

    email=sys.argv[1]

    duration_limit=None
    if "--duration" in sys.argv:
        idx=sys.argv.index("--duration")
        if idx+1<len(sys.argv):
            try:
                duration_limit=int(sys.argv[idx+1])
            except ValueError:
                pass

    run_start=time.time()

    print(f"AI Trader V2 starting for {email}")
    print(f"Strategy: 5-min RSI bounce on {', '.join(TICKERS)}")
    print(f"TP {TAKE_PROFIT_PCT*100:.1f}% | SL {STOP_LOSS_PCT*100:.1f}% | Hold up to {MAX_HOLD_MINUTES}min")

    conn,cursor=connect_db()
    ensure_user_exists(cursor,conn,email)
    update_bot_state(cursor,conn,email,"V2 bot running: 5-min RSI bounce strategy")

    last_scan=0
    iteration=0

    try:
        while True:
            if duration_limit and (time.time()-run_start)>duration_limit:
                print(f"Duration limit reached ({duration_limit}s). Exiting.")
                break

            iteration+=1
            positions=get_open_positions(cursor,email)
            for pos in positions:
                check_position(cursor,conn,email,pos)

            if time.time()-last_scan>=SCAN_INTERVAL_SECONDS:
                last_scan=time.time()
                positions=get_open_positions(cursor,email)
                held_tickers={p["ticker"] for p in positions}

                if len(positions)<MAX_OPEN_POSITIONS:
                    for ticker in TICKERS:
                        if ticker in held_tickers:
                            continue

                        signal=scan_for_signal(ticker)
                        if signal:
                            open_position(cursor,conn,email,signal)
                            held_tickers.add(ticker)
                            positions=get_open_positions(cursor,email)
                            if len(positions)>=MAX_OPEN_POSITIONS:
                                break

                update_bot_state(
                    cursor,conn,email,
                    f"Scanning {len(TICKERS)} tickers. {len(positions)} open positions. (V2 strategy)"
                )

            time.sleep(POSITION_CHECK_SECONDS)

    except KeyboardInterrupt:
        print("Stopped by user")
    except Exception as exc:
        print(f"Bot error: {exc}")
        update_bot_state(cursor,conn,email,f"V2 bot crashed: {exc}",running=False)
    finally:
        update_bot_state(cursor,conn,email,"V2 bot stopped.",running=False)
        conn.close()


if __name__=="__main__":
    main()
