import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="Momentum Scanner", layout="wide")
st.title("📈 Daily Momentum Breakout Scanner (Live Data + Auto Symbols)")

# ✅ Fetch NIFTY 500 + Smallcap 250 symbols from GitHub (100% reliable)
@st.cache_data(ttl=86400)
def get_index_symbols():
    url1 = "https://raw.githubusercontent.com/saikr789/NSE-Stock-Indices/main/ind_nifty500list.csv"
    url2 = "https://raw.githubusercontent.com/saikr789/NSE-Stock-Indices/main/ind_niftysmallcap250list.csv"

    df1 = pd.read_csv(url1)
    df2 = pd.read_csv(url2)

    symbols = list(df1["Symbol"].unique()) + list(df2["Symbol"].unique())
    return list(set(symbols))  # unique list


# ✅ Fetch live OHLCV data (cached for 24 hours)
@st.cache_data(ttl=86400)
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

    # ✅ RS filter
    if row["RS"] < 1.02:
        return False

    # ✅ Base range (last 10 candles)
    base = df.iloc[i-10:i]
    base_range = (base["High"].max() - base["Low"].min()) / row["Close"]
    if base_range > 0.07:
        return False

    # ✅ Trend filter
    if not ((row["Close"] > row["EMA20"]) and
            (row["Close"] > row["EMA50"]) and
            (row["Close"] >= 0.9 * row["RollMax252"])):
        return False

    # ✅ Breakout + Volume spike
    if not ((row["Close"] > prev["High"]) and (row["Volume"] > 1.5 * row["AvgVol20"])):
        return False

    return True


# ✅ MAIN APP FLOW
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
