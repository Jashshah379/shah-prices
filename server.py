#!/usr/bin/env python3
"""Shah Family Dashboard - Live Price Server"""
import os, time, json
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Will import yfinance lazily to avoid startup crash
yf = None

def get_yf():
    global yf
    if yf is None:
        import yfinance
        yf = yfinance
    return yf

INDICES = {
    "NIFTY50":   "^NSEI",
    "SENSEX":    "^BSESN",
    "BANKNIFTY": "^NSEBANK",
    "USDINR":    "USDINR=X",
    "GOLD":      "GC=F",
    "CRUDEOIL":  "CL=F",
}

_cache = {}
_cache_time = 0
CACHE_TTL = 180

def safe_price(ticker_obj):
    try:
        fi = ticker_obj.fast_info
        price = fi.last_price
        prev  = fi.previous_close or price
        if not price or price <= 0:
            return None
        return {
            "p":   round(float(price), 2),
            "c":   round(float(price - prev), 2),
            "pct": round(float((price - prev) / prev * 100), 2) if prev else 0,
        }
    except Exception:
        return None

def fetch_all():
    global _cache, _cache_time
    if time.time() - _cache_time < CACHE_TTL and _cache:
        return _cache

    lib = get_yf()
    prices = {}

    # Fetch indices + FX
    for name, sym in INDICES.items():
        try:
            r = safe_price(lib.Ticker(sym))
            if r:
                prices[name] = r
        except Exception:
            pass

    # NSE stocks — read from file next to server.py
    try:
        with open("symbols.json") as f:
            nse_syms = json.load(f)
    except Exception:
        nse_syms = []

    # Fetch in batches of 40
    for i in range(0, len(nse_syms), 40):
        batch = nse_syms[i:i+40]
        yf_str = " ".join(s + ".NS" for s in batch)
        try:
            tickers = lib.Tickers(yf_str)
            for sym in batch:
                r = safe_price(tickers.tickers.get(sym + ".NS"))
                if r:
                    prices[sym] = r
        except Exception as e:
            print(f"Batch {i} error: {e}")
        time.sleep(0.2)

    _cache = prices
    _cache_time = time.time()
    print(f"Fetched {len(prices)} prices", flush=True)
    return prices

@app.route("/")
def health():
    return jsonify({"status": "ok", "cached": len(_cache), "age": round(time.time() - _cache_time)})

@app.route("/prices")
def get_prices():
    data = fetch_all()
    return jsonify({"prices": data, "ts": int(time.time()), "n": len(data)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
