import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Momentum Scanner", layout="wide")

st.title("📈 Daily Momentum Breakout Scanner (Auto-Run + Auto Symbol Detection)")

# ✅ Your GitHub raw data folder URL
DATA_SOURCE = "https://api.github.com/repos/parmarravi4139-netizen/momentum-scanner/contents/"

RAW_BASE = "https://raw.githubusercontent.com/parmarravi4139-netizen/momentum-scanner/main/"

@st.cache_data
def get_all_csv_files():
    """Fetch all CSV filenames from GitHub repo automatically."""
    try:
        response = requests.get(DATA_SOURCE)
        data = response.json()
        csv_files = [item["name"] for item in data if item["name"].lower().endswith(".csv")]
        return csv_files
    except:
        return []

@st.cache_data
def load_csv(file_name):
    url = RAW_BASE + file_name
    try:
        df = pd.read_csv(url)
        return df
    except:
        return None


def scan_stock(df):
    if not set(["Open", "High", "Low", "Close", "Volume"]).issubset(df.columns):
        return False

    df = df.copy()
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['AvgVol20'] = df['Volume'].rolling(20).mean()
    df['RollMax252'] = df['Close'].rolling(252).max()
    df["RS"] = df["Close"] / df["Close"].rolling(50).mean()

    if len(df) < 260:
        return False

    df = df.dropna().reset_index(drop=True)
    if len(df) == 0:
        return False

    i = len(df) - 1
    row = df.iloc[i]
    prev = df.iloc[i - 1]

    if row["RS"] < 1.02:
        return False

    if i < 10:
        return False
    base = df.iloc[i-10:i]
    base_range = (base["High"].max() - base["Low"].min()) / row["Close"]
    if base_range > 0.07:
        return False

    if not ((row['Close'] > row['EMA20']) and
            (row['Close'] > row['EMA50']) and
            (row['Close'] >= 0.9 * row['RollMax252'])):
        return False

    if not ((row['Close'] > prev['High']) and (row['Volume'] > 1.5 * row['AvgVol20'])):
        return False

    return True


st.info("⏳ Auto-detecting symbols and scanning…")

# ✅ Auto-detect CSV files from GitHub
symbol_files = get_all_csv_files()

st.write(f"✅ Total symbols detected: {len(symbol_files)}")

results = []
failed = []

for file_name in symbol_files:
    df = load_csv(file_name)
    if df is None:
        failed.append(file_name)
        continue

    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df.sort_values("Date").reset_index(drop=True)

    if scan_stock(df):
        results.append(file_name.replace(".csv", ""))

st.success("✅ Scan Completed")

st.subheader("📌 Breakout Stocks Today")
st.write(results if results else "No breakouts today.")

if failed:
    with st.expander("⚠️ Files that could not be loaded"):
        st.write(failed)
