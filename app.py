# =====================
# ADVANCED STOCK PICKS
# =====================
def get_stock_details(regime):
    
    universe = {
        "RELIANCE.NS": "Large cap growth",
        "TCS.NS": "Stable IT leader",
        "INFY.NS": "Tech momentum",
        "HDFCBANK.NS": "Banking leader",
        "ICICIBANK.NS": "High growth bank",
        "LT.NS": "Infra growth",
        "ITC.NS": "Defensive FMCG",
        "HINDUNILVR.NS": "Stable FMCG",
        "SBIN.NS": "PSU bank momentum",
        "AXISBANK.NS": "Private bank growth"
    }

    try:
        data = yf.download(list(universe.keys()), period="3mo", progress=False)["Close"]
        latest_prices = data.iloc[-1]

        returns = (data.iloc[-1] / data.iloc[0] - 1).sort_values(ascending=False)

        if regime == "RISK ON":
            selected = returns.head(5)

        elif regime == "RISK OFF":
            selected = returns.tail(5)

        else:
            selected = returns.iloc[2:7]

        results = []

        for stock in selected.index:
            name = stock.replace(".NS", "")
            price = round(latest_prices[stock], 2)

            if regime == "RISK ON":
                reason = "Strong momentum"
                risk = "Medium"

            elif regime == "RISK OFF":
                reason = "Defensive / stable"
                risk = "Low"

            else:
                reason = "Balanced exposure"
                risk = "Medium"

            results.append({
                "name": name,
                "price": price,
                "reason": reason,
                "risk": risk
            })

        return results

    except:
        return [
            {"name": "HDFC Bank", "price": "-", "reason": "Stable leader", "risk": "Low"},
            {"name": "Infosys", "price": "-", "reason": "Tech exposure", "risk": "Medium"},
        ]


stocks = get_stock_details(regime)

# =====================
# DISPLAY STOCKS
# =====================
st.subheader("Top Stock Picks (Actionable)")

for s in stocks:
    st.markdown(f"""
**{s['name']}**  
Price: ₹{s['price']}  
Reason: {s['reason']}  
Risk: {s['risk']}  
---
""")
