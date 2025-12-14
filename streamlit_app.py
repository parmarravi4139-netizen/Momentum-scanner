def scan_stock(df):
    # ✅ Basic checks
    if df is None or len(df) < 260:
        return False

    # ✅ Fix multi-index (Yahoo sometimes returns multi-index)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # ✅ Required columns check
    required = ["Open", "High", "Low", "Close", "Volume"]
    for col in required:
        if col not in df.columns:
            return False

    df = df.copy()

    # ✅ Indicators
    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()
    df["AvgVol20"] = df["Volume"].rolling(20).mean()
    df["RollMax252"] = df["Close"].rolling(252).max()
    df["RS"] = df["Close"] / df["Close"].rolling(50).mean()

    df = df.dropna().reset_index(drop=True)

    # ✅ If still empty, skip
    if len(df) < 20:
        return False

    i = len(df) - 1
    row = df.iloc[i]
    prev = df.iloc[i - 1]

    # ✅ Ensure RS is float
    try:
        rs_value = float(row["RS"])
    except:
        return False

    # ✅ RS filter
    if rs_value < 1.02:
        return False

    # ✅ Base range
    base = df.iloc[i-10:i]
    base_range = (base["High"].max() - base["Low"].min()) / row["Close"]
    if base_range > 0.07:
        return False

    # ✅ Trend filter
    if not (
        row["Close"] > row["EMA20"] and
        row["Close"] > row["EMA50"] and
        row["Close"] >= 0.9 * row["RollMax252"]
    ):
        return False

    # ✅ Breakout + Volume spike
    if not (
        row["Close"] > prev["High"] and
        row["Volume"] > 1.5 * row["AvgVol20"]
    ):
        return False

    return True
