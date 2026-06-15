import os, time, json, traceback, requests
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

_cache = {}
_cache_time = 0
CACHE_TTL = 300  # 5 minutes

# ── NSE India official API (no auth needed, public) ──────────────────────────
NSE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/",
}

def nse_session():
    s = requests.Session()
    s.headers.update(NSE_HEADERS)
    # Hit homepage first to get cookies
    try:
        s.get("https://www.nseindia.com", timeout=10)
    except:
        pass
    return s

def fetch_nse_indices(session):
    """Fetch Nifty 50, Bank Nifty, Nifty IT from NSE"""
    prices = {}
    try:
        r = session.get("https://www.nseindia.com/api/allIndices", timeout=10)
        data = r.json().get("data", [])
        MAP = {
            "NIFTY 50": "NIFTY50",
            "NIFTY BANK": "BANKNIFTY",
            "NIFTY IT": "NIFTYIT",
            "NIFTY NEXT 50": "NIFTYNEXT50",
        }
        for idx in data:
            name = idx.get("index", "")
            key = MAP.get(name)
            if key:
                last = float(idx.get("last", 0))
                prev = float(idx.get("previousClose", last))
                prices[key] = {
                    "p": round(last, 2),
                    "c": round(last - prev, 2),
                    "pct": round((last - prev) / prev * 100, 2) if prev else 0,
                }
    except Exception as e:
        print(f"NSE indices error: {e}", flush=True)
    return prices

def fetch_nse_stocks(session, symbols):
    """Fetch stock quotes from NSE in batches"""
    prices = {}
    # NSE market quotes endpoint
    for i in range(0, len(symbols), 50):
        batch = symbols[i:i+50]
        try:
            sym_str = ",".join(batch)
            r = session.get(
                f"https://www.nseindia.com/api/quote-equity?symbol={batch[0]}",
                timeout=10
            )
            # Use the marketStatus + quote endpoint
        except Exception as e:
            print(f"NSE stock batch {i} error: {e}", flush=True)
        time.sleep(0.5)

    # Better: use NSE's live market data endpoint
    try:
        r = session.get("https://www.nseindia.com/api/equity-stockIndices?index=SECURITIES%20IN%20F%26O", timeout=15)
        if r.status_code == 200:
            data = r.json().get("data", [])
            for item in data:
                sym = item.get("symbol", "")
                if sym and sym in symbols:
                    last = float(item.get("lastPrice", 0))
                    prev = float(item.get("previousClose", last))
                    if last > 0:
                        prices[sym] = {
                            "p": round(last, 2),
                            "c": round(last - prev, 2),
                            "pct": round((last - prev) / prev * 100, 2) if prev else 0,
                        }
    except Exception as e:
        print(f"NSE F&O stocks error: {e}", flush=True)

    return prices

def fetch_fx_gold():
    """Fetch USD/INR and Gold from exchangerate and metals API"""
    prices = {}
    # USD/INR from free API
    try:
        r = requests.get("https://open.er-api.com/v6/latest/USD", timeout=8)
        data = r.json()
        inr = data.get("rates", {}).get("INR", 0)
        if inr:
            prices["USDINR"] = {"p": round(inr, 2), "c": 0, "pct": 0}
    except Exception as e:
        print(f"FX error: {e}", flush=True)

    # Gold from metals-api alternative
    try:
        r = requests.get("https://forex-data-feed.swissquote.com/public-quotes/bboquotes/instrument/XAU/USD", timeout=8)
        data = r.json()
        if data and len(data) > 0:
            gold = float(data[0].get("spreadProfilePrices", [{}])[0].get("ask", 0))
            if gold > 0:
                prices["GOLD"] = {"p": round(gold, 2), "c": 0, "pct": 0}
    except Exception as e:
        print(f"Gold error: {e}", flush=True)

    return prices

def fetch_sensex():
    """Fetch Sensex from BSE"""
    try:
        r = requests.get(
            "https://api.bseindia.com/BseIndiaAPI/api/getScripHeaderData/w?Scode=SENSEX&seriesid=",
            headers={"Referer": "https://www.bseindia.com/"},
            timeout=10
        )
        data = r.json()
        last = float(data.get("CurrRate", 0))
        prev = float(data.get("PrevClose", last))
        if last > 0:
            return {"SENSEX": {
                "p": round(last, 2),
                "c": round(last - prev, 2),
                "pct": round((last - prev) / prev * 100, 2) if prev else 0,
            }}
    except Exception as e:
        print(f"Sensex error: {e}", flush=True)
    return {}

def fetch_all():
    global _cache, _cache_time
    if time.time() - _cache_time < CACHE_TTL and _cache:
        return _cache

    print("Fetching prices...", flush=True)
    prices = {}

    # Load symbols
    symbols = []
    if os.path.exists("symbols.json"):
        with open("symbols.json") as f:
            symbols = json.load(f)

    # Create NSE session
    session = nse_session()

    # Fetch all sources in parallel-ish
    prices.update(fetch_nse_indices(session))
    prices.update(fetch_sensex())
    prices.update(fetch_fx_gold())
    prices.update(fetch_nse_stocks(session, symbols))

    if prices:
        _cache = prices
        _cache_time = time.time()
        print(f"Fetched {len(prices)} prices successfully", flush=True)
    else:
        print("All sources failed", flush=True)

    return _cache

@app.route("/")
def health():
    age = round(time.time() - _cache_time)
    return jsonify({"status": "ok", "cached": len(_cache), "age_seconds": age})

@app.route("/prices")
def get_prices():
    data = fetch_all()
    return jsonify({"prices": data, "ts": int(time.time()), "n": len(data)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    fetch_all()
    app.run(host="0.0.0.0", port=port)
