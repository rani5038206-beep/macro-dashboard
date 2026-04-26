import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import os
from datetime import datetime

st.set_page_config(page_title="Macro → Micro Portfolio Engine", layout="wide")

# =========================
# 0. CONFIG
# =========================
REB_FILE = "last_portfolio.csv"   # for monthly rebalance diff

# =========================
# 1. MACRO DATA (20D TREND)
# =========================
@st.cache_data(ttl=600)
def get_macro():
    tickers = ["^GSPC","DX-Y.NYB","^VIX","^TNX","INR=X","CL=F"]
    df = yf.download(tickers, period="6mo", progress=False)["Close"].dropna()
    df.columns = ["SPX","DXY","VIX","US10Y","USDINR","CRUDE"]
    return df

def trend_signal(series, window=20, invert=False):
    ma = series.rolling(window).mean()
    sig = np.where(series > ma, 1, -1)
    if invert:  # for indicators where rise is bad
        sig = -sig
    return pd.Series(sig, index=series.index)

dfm = get_macro()

# Build signals (use last value)
signals = {
    "SPX": trend_signal(dfm["SPX"], 20, invert=False).iloc[-1],       # ↑ good
    "DXY": trend_signal(dfm["DXY"], 20, invert=True).iloc[-1],        # ↑ bad
    "VIX": trend_signal(dfm["VIX"], 20, invert=True).iloc[-1],        # ↑ bad
    "US10Y": trend_signal(dfm["US10Y"], 20, invert=True).iloc[-1],    # ↑ bad
    "USDINR": trend_signal(dfm["USDINR"], 20, invert=True).iloc[-1],  # ₹ weak (↑) bad
    "CRUDE": trend_signal(dfm["CRUDE"], 20, invert=True).iloc[-1],    # ↑ bad
}

# Weighted score (simple, stable)
weights = {
    "SPX": 0.2, "DXY": 0.2, "US10Y": 0.15,
    "USDINR": 0.15, "CRUDE": 0.15, "VIX": 0.15
}
model_score = sum(signals[k]*weights[k] for k in signals)

# Regime → Equity %
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
# 2. SCREENER UNIVERSE (PASTE YOUR 61 HERE)
# =========================
SCREENER = [
    # 🔴 IMPORTANT: Replace with your 61 stocks from Screener
    "RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS",
    "LT.NS","SBIN.NS","AXISBANK.NS","BAJFINANCE.NS","SUNPHARMA.NS",
    "MARUTI.NS","ULTRACEMCO.NS","HINDUNILVR.NS","ITC.NS","POWERGRID.NS",
    "NTPC.NS","ADANIPORTS.NS","ADANIENT.NS","KOTAKBANK.NS","ASIANPAINT.NS"
]

# =========================
# 3. STOCK ENGINE (RANKING)
# =========================
@st.cache_data(ttl=300)
def rank_stocks(tickers):
    if len(tickers) == 0:
        return pd.DataFrame()

    data = yf.download(tickers, period="4mo", progress=False)["Close"].dropna()
    latest = data.iloc[-1]

    r1m = (data.iloc[-1] / data.iloc[-20] - 1)
    r3m = (data.iloc[-1] / data.iloc[0] - 1)
    vol = data.pct_change().std()

    df = pd.DataFrame({
        "Stock": r1m.index,
        "R1M": r1m.values,
        "R3M": r3m.values,
        "Vol": vol.values,
        "Price": latest.values
    })

    # Momentum score
    df["Score"] = (df["R1M"]*0.5) + (df["R3M"]*0.4) - (df["Vol"]*0.1)

    # Keep positive momentum
    df = df[df["R3M"] > 0].copy()

    # Top 10
    df = df.sort_values("Score", ascending=False).head(10).reset_index(drop=True)

    return df

ranked = rank_stocks(SCREENER)

# =========================
# 4. POSITION SIZING (TIERED BY REGIME)
# =========================
def tier_weights(n, regime):
    # returns list of weights summing to 1 for n<=10
    if n == 0:
        return []

    if regime == "RISK ON":
        # 3x15%, 3x10%, rest 5%
        base = [0.15]*min(3,n) + [0.10]*max(0, min(6,n)-3) + [0.05]*max(0, n-6)
    elif regime == "TRANSITION":
        base = [0.12]*min(3,n) + [0.08]*max(0, min(6,n)-3) + [0.05]*max(0, n-6)
    else:  # RISK OFF
        base = [0.10]*min(3,n) + [0.05]*max(0, min(6,n)-3) + [0.03]*max(0, n-6)

    w = np.array(base[:n], dtype=float)
    w = w / w.sum()  # normalize to 1
    return w.tolist()

def build_portfolio(df, total_value, eq_pct, regime):
    if df.empty:
        return pd.DataFrame()

    equity_cap = total_value * (eq_pct/100.0)

    w = tier_weights(len(df), regime)
    df = df.copy()
    df["Weight"] = w
    df["Alloc_₹"] = df["Weight"] * equity_cap
    df["Units"] = (df["Alloc_₹"] / df["Price"]).fillna(0).astype(int)
    df["Invested_₹"] = df["Units"] * df["Price"]
    df["Name"] = df["Stock"].str.replace(".NS","", regex=False)

    cols = ["Name","Price","R1M","R3M","Score","Weight","Alloc_₹","Units","Invested_₹"]
    return df[cols]

# =========================
# 5. UI
# =========================
st.title("📊 Macro → Micro Portfolio Engine")

c1,c2,c3 = st.columns(3)
c1.metric("Regime", regime)
c2.metric("Model Score", f"{model_score:.2f}")
c3.metric("Equity %", f"{eq_pct}%")

st.subheader("Macro Signals (20D trend)")
st.table(pd.DataFrame(signals, index=["Signal"]).T)

st.subheader("Market Trend (Macro)")
st.line_chart(dfm)

# Sidebar inputs
st.sidebar.header("Client Input")
portfolio_value = st.sidebar.number_input("Portfolio Value (₹)", value=1_000_000, step=10000)
client_eq = st.sidebar.slider("Current Equity %", 0, 100, 60)

# Action
st.subheader("Action Required")
diff = eq_pct - client_eq
if diff > 0:
    st.success(f"Increase equity by {diff}%")
elif diff < 0:
    st.error(f"Reduce equity by {abs(diff)}%")
else:
    st.info("Portfolio aligned")

# Build portfolio
st.subheader("Top 10 Stocks (Screener → Ranked)")
port = build_portfolio(ranked, portfolio_value, eq_pct, regime)

if port.empty:
    st.warning("No stocks after ranking. Check screener list or data.")
else:
    # display table
    st.dataframe(
        port.style.format({
            "Price":"₹{:.2f}",
            "R1M":"{:.2%}",
            "R3M":"{:.2%}",
            "Score":"{:.3f}",
            "Weight":"{:.2%}",
            "Alloc_₹":"₹{:,.0f}",
            "Invested_₹":"₹{:,.0f}",
        }),
        use_container_width=True
    )

    # totals
    st.write(f"**Total Equity Allocation:** ₹{port['Alloc_₹'].sum():,.0f}")
    st.write(f"**Total Invested (rounded by units):** ₹{port['Invested_₹'].sum():,.0f}")

# =========================
# 6. MONTHLY REBALANCE (SAVE / COMPARE)
# =========================
st.subheader("Monthly Rebalance")

colA, colB = st.columns(2)

with colA:
    if st.button("💾 Save Current Portfolio"):
        if not port.empty:
            port.to_csv(REB_FILE, index=False)
            st.success("Saved as last portfolio")
        else:
            st.warning("Nothing to save")

with colB:
    if st.button("🔁 Compare vs Last (Generate Trades)"):
        if not os.path.exists(REB_FILE):
            st.warning("No saved portfolio found")
        elif port.empty:
            st.warning("No current portfolio")
        else:
            prev = pd.read_csv(REB_FILE)
            curr = port.copy()

            # align by Name
            prev = prev.set_index("Name")
            curr = curr.set_index("Name")

            all_names = sorted(set(prev.index).union(set(curr.index)))
            trades = []

            for n in all_names:
                prev_w = prev["Weight"].get(n, 0.0)
                curr_w = curr["Weight"].get(n, 0.0)

                change = curr_w - prev_w

                if abs(change) > 0.01:  # threshold 1%
                    action = "BUY" if change > 0 else "SELL"
                    trades.append({
                        "Stock": n,
                        "Action": action,
                        "Δ Weight": change
                    })

            if trades:
                st.dataframe(pd.DataFrame(trades))
            else:
                st.success("No significant changes")

# =========================
# 7. REFRESH
# =========================
if st.button("🔄 Refresh Market Data"):
    st.cache_data.clear()
    st.success("Refreshed")
