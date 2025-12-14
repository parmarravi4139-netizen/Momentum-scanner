import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="Momentum Scanner", layout="wide")
st.title("📈 Daily Momentum Breakout Scanner (Live Data)")

# ✅ 1) FIXED SYMBOL LIST (YOUR FULL LIST)
@st.cache_data(ttl=86400)
def get_index_symbols():
    symbols = [
        "ACMESOLAR","AADHARHFC","AARTIIND","AAVAS","ACE","ABFRL","ABLBL","ABREL","ABSLAMC",
        "AEGISLOG","AEGISVOPAK","AFCONS","AFFLE","AKUMS","AKZOINDIA","APLLTD","ALKYLAMINE",
        "ALOKINDS","ARE&M","AMBER","ANANDRATHI","ANANTRAJ","ANGELONE","APTUS","ASAHIINDIA",
        "ASTERDM","ASTRAZEN","ATHERENERG","ATUL","AIIL","BASF","BEML","BLS","BALRAMCHIN",
        "BANDHANBNK","BATAINDIA","BAYERCROP","BIKAJI","BSOFT","BLUEDART","BLUEJET","BBTC",
        "FIRSTCRY","BRIGADE","MAPMYINDIA","CCL","CESC","CAMPUS","CANFINHOME","CAPLIPOINT",
        "CGCL","CARBORUNIV","CASTROLIND","CEATLTD","CENTRALBK","CDSL","CENTURYPLY","CERA",
        "CHALET","CHAMBLFERT","CHENNPETRO","CHOICEIN","CHOLAHLDNG","CUB","CLEAN","COHANCE",
        "CAMS","CONCORDBIO","CRAFTSMAN","CREDITACC","CROMPTON","CYIENT","DCMSHRIRAM","DOMS",
        "DATAPATTNS","DEEPAKFERT","DELHIVERY","DEVYANI","AGARWALEYE","LALPATHLAB","DUMMYSKFIN",
        "DUMMYDBRLT","EIDPARRY","EIHOTEL","ELECON","ELGIEQUIP","EMAMILTD","EMCURE","ENGINERSIN",
        "ERIS","FINCABLES","FINPIPE","FSL","FIVESTAR","FORCEMOT","GRSE","GILLETTE","GLAND",
        "GODIGIT","GPIL","GODREJAGRO","GRANULES","GRAPHITE","GRAVITA","GESHIP","GMDCLTD","GSPL",
        "HEG","HBLENGINE","HFCL","HAPPSTMNDS","HSCL","HINDCOPPER","HOMEFIRST","HONASA","IFCI",
        "IIFL","INOXINDIA","IRCON","ITI","INDGN","INDIACEM","INDIAMART","IEX","INOXWIND",
        "INTELLECT","IGIL","IKS","JBCHEPHARM","JBMA","JKTYRE","JMFINANCIL","JPPOWER","J&KBANK",
        "JINDALSAW","JUBLINGREA","JUBLPHARMA","JWL","JYOTHYLAB","JYOTICNC","KSB","KAJARIACER",
        "KPIL","KARURVYSYA","KAYNES","KEC","KFINTECH","KIRLOSBROS","KIRLOSENG","KIMS","LTFOODS",
        "LATENTVIEW","LAURUSLABS","THELEELA","LEMONTREE","MMTC","MGL","MAHSCOOTER","MAHSEAMLES",
        "MANAPPURAM","MRPL","METROPOLIS","MINDACORP","MSUMI","MCX","NATCOPHARM","NBCC","NCC",
        "NSLNISP","NH","NAVA","NAVINFLUOR","NETWEB","NEULANDLAB","NEWGEN","NIVABUPA","NUVAMA",
        "NUVOCO","OLAELEC","OLECTRA","ONESOURCE","PCBL","PGEL","PNBHOUSING","PTCIL","PVRINOX",
        "PFIZER","PPLPHARMA","POLYMED","POONAWALLA","PRAJIND","RRKABEL","RBLBANK","RHIM","RITES",
        "RADICO","RAILTEL","RAINBOW","RKFORGE","RCF","REDINGTON","RELINFRA","RPOWER","SBFC",
        "SKFINDIA","SAGILITY","SAILIFE","SAMMAANCAP","SAPPHIRE","SARDAEN","SAREGAMA","SCHNEIDER",
        "SCI","SHYAMMETL","SIGNATURE","SOBHA","SONATSOFTW","STARHEALTH","SUMICHEM","SUNTV",
        "SUNDRMFAST","SWANCORP","SYRMA","TBOTEK","TATACHEM","TTML","TECHNOE","TEJASNET",
        "RAMCOCEM","TIMKEN","TITAGARH","TARIL","TRIDENT","TRIVENI","TRITURBINE","UTIAMC",
        "USHAMART","VGUARD","DBREALTY","VTL","MANYAVAR","VENTIVE","VIJAYA","WELCORP",
        "WELSPUNLIV","WHIRLPOOL","WOCKPHARMA","ZFCVINDIA","ZEEL","ZENTEC","ZENSARTECH","ECLERX"
    ]
    return list(sorted(set(symbols)))


# ✅ 2) LIVE DATA FETCHER
@st.cache_data(ttl=86400)
def get_live_data(symbol):
    try:
        df = yf.download(symbol + ".NS", period="400d")
        if df is None or df.empty:
            return None
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


# ✅ 3) SCANNER LOGIC
def scan_stock(df):
    if len(df) < 260:
        return False

    df = df.copy()
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


# ✅ 4) MAIN APP FLOW
st.info("⏳ Loading symbol list…")
symbols = get_index_symbols()
st.write(f"✅ Total symbols loaded: {len(symbols)}")

st.info("⏳ Fetching live data & running scanner…")

results = []
failed = []

for sym in symbols:
    df = get_live_data(sym)
    if df is None:
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
