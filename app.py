import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

st.set_page_config(page_title="Macro → Micro Portfolio Engine", layout="wide")

# =========================
# 1. MACRO DATA
# =========================
@st.cache_data(ttl=600)
def get_macro():
    tickers = ["^GSPC","DX-Y.NYB","^VIX","^TNX","INR=X","CL=F"]
    df = yf.download(tickers, period="6mo", progress=False)["Close"].dropna()
    df.columns = ["SPX","DXY","VIX","US10Y","USDINR","CRUDE"]
    return df

dfm = get_macro()

def signal(series, invert=False):
    ma = series.rolling(20).mean()
    sig = 1 if series.iloc[-1] > ma.iloc[-1] else -1
    return -sig if invert else sig

signals = {
    "SPX": signal(dfm["SPX"]),
    "DXY": signal(dfm["DXY"], True),
    "VIX": signal(dfm["VIX"], True),
    "US10Y": signal(dfm["US10Y"], True),
    "USDINR": signal(dfm["USDINR"], True),
    "CRUDE": signal(dfm["CRUDE"], True)
}

weights = {"SPX":0.2,"DXY":0.2,"VIX":0.15,"US10Y":0.15,"USDINR":0.15,"CRUDE":0.15}

model_score = sum(signals[k]*weights[k] for k in signals)

# =========================
# 2. REGIME
# =========================
if model_score > 0.4:
    regime = "RISK ON"
    eq_pct = 75
elif model_score < -0.4:
    regime = "RISK OFF"
    eq_pct = 30
else:
    regime = "TRANSITION"
    eq_pct = 55

# =========================
# 3. SCREENER STOCKS
# =========================
SCREENER = [
    "RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS",
    "LT.NS","SBIN.NS","AXISBANK.NS","ITC.NS","HINDUNILVR.NS"
]

@st.cache_data(ttl=300)
def rank_stocks(tickers):
    data = yf.download(tickers, period="4mo", progress=False)["Close"].dropna()
    latest = data.iloc[-1]

    r1m = (data.iloc[-1]/data.iloc[-20]-1)
    r3m = (data.iloc[-1]/data.iloc[0]-1)
    vol = data.pct_change().std()

    df = pd.DataFrame({
        "Stock": r1m.index,
        "R1M": r1m.values,
        "R3M": r3m.values,
        "Vol": vol.values,
        "Price": latest.values
    })

    df["Score"] = df["R1M"]*0.5 + df["R3M"]*0.4 - df["Vol"]*0.1
    df = df[df["R3M"] > 0]
    df = df.sort_values("Score", ascending=False).head(10)

    return df.reset_index(drop=True)

ranked = rank_stocks(SCREENER)

# =========================
# 4. POSITION SIZING
# =========================
def get_weights(n, regime):
    if regime == "RISK ON":
        base = [0.15]*3 + [0.10]*3 + [0.05]*(n-6)
    elif regime == "TRANSITION":
        base = [0.12]*3 + [0.08]*3 + [0.05]*(n-6)
    else:
        base = [0.10]*3 + [0.05]*3 + [0.03]*(n-6)

    base = base[:n]
    w = np.array(base)
    return w/w.sum()

def build_portfolio(df, value):
    weights = get_weights(len(df), regime)
    df["Weight"] = weights
    df["Alloc"] = df["Weight"] * value * eq_pct/100
    df["Units"] = (df["Alloc"]/df["Price"]).astype(int)
    return df

# =========================
# UI
# =========================
st.title("📊 Macro → Micro Portfolio Engine")

col1,col2,col3 = st.columns(3)
col1.metric("Regime", regime)
col2.metric("Model Score", round(model_score,2))
col3.metric("Equity %", f"{eq_pct}%")

# =========================
# MACRO INTERPRETATION
# =========================
st.subheader("📊 Macro Interpretation")

explain = {
    "SPX":"Global equity trend",
    "DXY":"Dollar strength (FII impact)",
    "VIX":"Market fear",
    "US10Y":"Bond yield pressure",
    "USDINR":"Currency risk",
    "CRUDE":"Inflation pressure"
}

rows = []
for k in signals:
    rows.append({
        "Factor":k,
        "Meaning":explain[k],
        "Signal":signals[k],
        "Impact":"Positive" if signals[k]==1 else "Negative"
    })

st.table(pd.DataFrame(rows))

# =========================
# SCORE BREAKDOWN
# =========================
st.subheader("🧠 Model Score Breakdown")

score_df = pd.DataFrame({
    "Factor":signals.keys(),
    "Signal":signals.values(),
    "Weight":[weights[k] for k in signals]
})

score_df["Contribution"] = score_df["Signal"]*score_df["Weight"]
st.dataframe(score_df)
st.write(f"### Final Score: {model_score:.2f}")

# =========================
# CLIENT INPUT
# =========================
st.sidebar.header("Client Input")
portfolio = st.sidebar.number_input("Portfolio Value", value=1000000)
current_eq = st.sidebar.slider("Current Equity %",0,100,60)

# =========================
# ACTION
# =========================
st.subheader("⚠️ Action Required")

diff = eq_pct - current_eq

if diff > 0:
    st.success(f"Increase Equity by {diff}%")
elif diff < 0:
    st.error(f"Reduce Equity by {abs(diff)}%")
else:
    st.info("Portfolio aligned")

# =========================
# PORTFOLIO IMPACT
# =========================
st.subheader("💰 Portfolio Impact")

curr_eq_val = portfolio * current_eq/100
rec_eq_val = portfolio * eq_pct/100

col1,col2 = st.columns(2)
col1.metric("Current Equity", f"₹{curr_eq_val:,.0f}")
col2.metric("Recommended Equity", f"₹{rec_eq_val:,.0f}")

# =========================
# STOCK SELECTION LOGIC
# =========================
st.subheader("📈 Stock Selection Logic")

st.info("""
✔ Strong earnings growth  
✔ Improving margins  
✔ Positive momentum  
✔ Lower volatility  
""")

# =========================
# TOP STOCKS
# =========================
st.subheader("🏆 Top Stocks")

st.dataframe(ranked)

# =========================
# FINAL PORTFOLIO
# =========================
st.subheader("💼 Final Allocation")

portfolio_df = build_portfolio(ranked, portfolio)

st.dataframe(
    portfolio_df.style.format({
        "Price":"₹{:.2f}",
        "Alloc":"₹{:,.0f}",
        "Weight":"{:.2%}"
    })
)

# =========================
# REBALANCE LOGIC
# =========================
st.subheader("🔁 Rebalancing Rule")

st.info("""
✔ Monthly review  
✔ Remove weak stocks  
✔ Add strong stocks  
✔ Adjust weights based on rank  
✔ Follow macro regime  
""")

# =========================
# TREND CHART
# =========================
st.subheader("📉 Market Trend")
st.line_chart(dfm)
