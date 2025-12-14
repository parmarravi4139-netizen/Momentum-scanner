import streamlit as st
import pandas as pd
import yfinance as yf
import requests

st.set_page_config(page_title="Momentum Scanner", layout="wide")
st.title("📈 Daily Momentum Breakout Scanner (Live Data + Auto Symbols)")

# ✅ Fetch NIFTY 500 + Smallcap 250 symbols from NSE website
@st.cache_data
def get_index_symbols():
    urls = {
        "NIFTY500": "https://www1.nseindia.com/content/indices/ind_nifty500list.csv",
        "SMALLCAP250": "https://www1.nseindia.com/content/indices/ind_niftysmallcap250list.csv"
    }

    headers = {"User-Agent": "Mozilla/5.0"}
    symbols = []

    for name, url in urls.items():
        try:
            df = pd.read_csv(url, headers=headers)
            df.columns = df.columns.str.strip()
            symbols.extend(df["Symbol"].tolist())
        except:
            pass

    return list(set(symbols))  # unique symbols


# ✅ Fetch live OHLCV data
@st.cache_data
def get_live_data(symbol):
    try:
        df = yf.download(symbol + ".NS", period="400d")
        df = df.reset_index()
        df = df.rename(columns={
            "Date": "Date",
            "Open": "Open",
            "High": "High",
            "Low": "Low",
            "Close": "Close",
            "Volume": "Volume"
        })
        return df
    except:
        return None


# ✅ Strategy logic
def scan_stock(df):
    if len(df) < 260:
        return False

    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()
    df["AvgVol20"] = df["Volume"].rolling(20).mean()
    df["RollMax252"] = df["Close"].rolling(252).max()
    df["RS"] = df["Close"] / df["Close"].rolling(50).mean()

    df = df.dropna().reset_index(drop=True)
    i = len(df) - 1
    row = df.iloc[i]
    prev = df.iloc[i - 1]

    if row["RS"] < 1.02:
        return False

    base = df.iloc[i-10:i]
    base_range = (base["High"].max() - base["Low"].min()) / row["Close"]
    if base_range > 0.07:
        return False

    if not ((row["Close"] > row["EMA20"]) and
            (row["Close"] > row["EMA50"]) and
            (row["Close"] >= 0.9 * row["RollMax252"])):
        return False

    if not ((row["Close"] > prev["High"]) and (row["Volume"] > 1.5 * row["AvgVol20"])):
        return False

    return True


st.info("⏳ Fetching symbols from NIFTY 500 + Smallcap 250…")
symbols = get_index_symbols()
st.write(f"✅ Total symbols loaded: {len(symbols)}")

st.info("⏳ Running live scanner…")

results = []
failed = []

for sym in symbols:
    df = get_live_data(sym)
    if df is None or df.empty:
        failed.append(sym)
        continue

    if scan_stock(df):
        results.append(sym)

st.success("✅ Scan Completed")

st.subheader("📌 Breakout Stocks Today")
st.write(results if results else "No breakouts today.")

if failed:
    with st.expander("⚠️ Failed to fetch data for"):
        st.write(failed)
