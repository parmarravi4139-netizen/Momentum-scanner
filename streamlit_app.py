import streamlit as st
import pandas as pd
import os

st.title("📈 Daily Momentum Breakout Scanner")

folder_path = st.text_input("Enter folder path:", r"D:\Small cap becktest data\daily data")

def scan_stock(df):
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['AvgVol20'] = df['Volume'].rolling(20).mean()
    df['RollMax252'] = df['Close'].rolling(252).max()
    df["RS"] = df["Close"] / df["Close"].rolling(50).mean()

    i = len(df) - 1
    row = df.iloc[i]
    prev = df.iloc[i - 1]

    if row["RS"] < 1.02:
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


if st.button("Scan Now"):
    if not os.path.exists(folder_path):
        st.error("Invalid folder path")
    else:
        files = [f for f in os.listdir(folder_path) if f.lower().endswith(".csv")]
        results = []

        for file in files:
            symbol = file.replace(".csv", "")
            df = pd.read_csv(os.path.join(folder_path, file))

            if len(df) < 260:
                continue

            df['Date'] = pd.to_datetime(df['Date'])
            df = df.sort_values('Date').reset_index(drop=True)

            if scan_stock(df):
                results.append(symbol)

        st.success("Scan Completed")
        st.write("### ✅ Breakout Stocks:")
        st.write(results)