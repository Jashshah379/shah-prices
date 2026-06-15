import os, time, json, traceback
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

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

def fetch_all():
    global _cache, _cache_time
    if time.time() - _cache_time < 180 and _cache:
        return _cache
    try:
        import yfinance as yf
        prices = {}
        # Indices
        for name, sym in INDICES.items():
            try:
                t = yf.Ticker(sym)
                fi = t.fast_info
                p = float(fi.last_price or 0)
                prev = float(fi.previous_close or p)
                if p > 0:
                    prices[name] = {
                        "p": round(p, 2),
                        "c": round(p - prev, 2),
                        "pct": round((p - prev) / prev * 100, 2) if prev else 0
                    }
            except:
                pass
        # Stocks
        try:
            syms = []
            if os.path.exists("symbols.json"):
                with open("symbols.json") as f:
                    syms = json.load(f)
            for i in range(0, len(syms), 40):
                batch = syms[i:i+40]
                try:
                    tks = yf.Tickers(" ".join(s+".NS" for s in batch))
                    for s in batch:
                        try:
                            fi = tks.tickers[s+".NS"].fast_info
                            p = float(fi.last_price or 0)
                            prev = float(fi.previous_close or p)
                            if p > 0:
                                prices[s] = {
                                    "p": round(p,2),
                                    "c": round(p-prev,2),
                                    "pct": round((p-prev)/prev*100,2) if prev else 0
                                }
                        except: pass
                except Exception as e:
                    print(f"Batch {i}: {e}", flush=True)
                time.sleep(0.2)
        except Exception as e:
            print(f"Stock fetch error: {e}", flush=True)
        _cache = prices
        _cache_time = time.time()
        print(f"Done: {len(prices)} prices", flush=True)
    except Exception as e:
        traceback.print_exc()
    return _cache

@app.route("/")
def health():
    return jsonify({"status": "ok", "cached": len(_cache), "age": round(time.time()-_cache_time)})

@app.route("/prices")
def prices():
    return jsonify({"prices": fetch_all(), "ts": int(time.time()), "n": len(_cache)})
