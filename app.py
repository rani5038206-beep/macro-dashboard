@st.cache_data(ttl=3600)
def load_data():
    tickers = [
        "^NSEI","^NSEBANK","^CNXIT",
        "INR=X","BZ=F","DX-Y.NYB",
        "^GSPC","^INDIAVIX","^TNX"
    ]

    df = yf.download(tickers, start=start, group_by='ticker', threads=False)

    data = {}

    mapping = {
        "^NSEI":"NIFTY",
        "^NSEBANK":"BANK",
        "^CNXIT":"IT",
        "INR=X":"USD",
        "BZ=F":"CRUDE",
        "DX-Y.NYB":"DXY",
        "^GSPC":"SPX",
        "^INDIAVIX":"VIX",
        "^TNX":"US10Y"
    }

    for ticker in tickers:
        try:
            sub = df[ticker]
            col = "Adj Close" if "Adj Close" in sub.columns else "Close"
            data[mapping[ticker]] = sub[col]
        except:
            continue

    if len(data) < 5:
        return pd.DataFrame()

    return pd.concat(data.values(), axis=1).dropna()
