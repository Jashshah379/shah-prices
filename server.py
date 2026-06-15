#!/usr/bin/env python3
"""
Shah Family Dashboard - Live Price Server
Free deployment on Render.com
Serves NSE stock prices, indices, FX, commodities
"""
import os, time, json
from flask import Flask, jsonify
from flask_cors import CORS
import yfinance as yf

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

NSE_SYMBOLS = ["360ONE", "3MINDIA", "AADHARHFC", "AARTIIND", "AARTIPHARM", "ABBOTINDIA", "ABCAPITAL", "ABFRL", "ABMKNW", "ABNANSFIN", "ABNU", "ABREL", "ABSLAMC", "ACCELYA", "ACUTAAS", "ADANIPORTS", "ADANIPOWER", "AEGISCHEM", "AJMERA", "ALICON", "ALIVUS", "ALKEM", "ALLCARGOGATI", "ALLTIMEPL", "ALOKINDS", "ALPHAGEO", "AMARAJABAT", "AMBUJACEM", "ANGELONE", "ANJANIPTS", "ANUPAMRASN", "APLAPOLLO", "APOLLOMICRO", "APOLLOTRI", "APOLLOTYRE", "AQUALOGI", "ARCHANCHEM", "AREM", "ARIESAGRO", "ARMANFIN", "ARVIND", "ARVINDFASN", "ARVINDSMAR", "ASHOKLEY", "ASTERDM", "ASTRAMICRO", "ASTRAZEN", "ATGL", "ATUL", "AUBANK", "AUTOAXLES", "AWL", "AXISBANK", "AXISCADES", "BAJAJ-AUTO", "BAJAJFINSV", "BAJAJHFL", "BAJFINANCE", "BALAMINES", "BALASORALL", "BALMLAWRIE", "BALRAMCHIN", "BANDHANBNK", "BANKBARODA", "BANNARIMIL", "BANSALWIRE", "BARTRONICS", "BAYERCROP", "BBOX", "BBTCL", "BCG", "BDL", "BEL", "BELRISE", "BERGEPAINT", "BGRENERGY", "BHARAT22ETF", "BHARATFORG", "BHARTIARTL", "BHEL", "BIKAJI", "BIOCON", "BIRLACABLE", "BIRLANUVO", "BLUEDART", "BOMBAYDYEING", "BOSCHEMC", "BOSCHLTD", "BPCL", "BRANDCONCEPT", "BRIGADE", "BSE", "CALS", "CAMLINFINE", "CAMLINPLAS", "CAMS", "CANBK", "CANFINHOME", "CANTABIL", "CAPACITE", "CAPLIPOINT", "CAREERP", "CARYSIL", "CDSL", "CELLOWORLD", "CEMINDIA", "CENTUM", "CERA", "CEREBRA", "CGPOWER", "CHAMBLFERT", "CHOLAFIN", "CIEINDS", "CLEAN", "COALINDIA", "COCHINSHIP", "COHANCE", "COLPAL", "COMFORTINT", "CONCOR", "CONTROLPR", "COSMOFIRST", "CPCAP", "CPCL", "CPSEETF", "CRAFTSMAN", "CSBBANK", "CUB", "DABUR", "DANLAW", "DBCORP", "DCBBANK", "DCXINDIA", "DECCANCEM", "DEEPAKFERT", "DEEPAKNTR", "DEEPINDS", "DELTACORP", "DEN", "DHANI", "DIAMINESQ", "DISA", "DISHMAN", "DISHTV", "DIVISLAB", "DLINKINDIA", "DOLPHIN", "DREAMFOLKS", "DREDGECORP", "DYNAMATECH", "E2ENETWORKS", "ECOS", "EDELWEISS", "EIDPARRY", "ELGIEQUIP", "ELIN", "EMAMILIT", "EMBDL", "ENTERO", "EPACK", "EPIGRAL", "EQUITASBNK", "ESCORTS", "ETERNAL", "EVEREADY", "EVERREADY", "EXIDEIND", "FACORALL", "FCL", "FEDERALBNK", "FEDERALMOGUL", "FERMENTA", "FINEORG", "FINEOTEX", "FINOLEXIND", "FIVESTAR", "FLUOROCHEM", "FORCEMOT", "FSL", "GAIL", "GANESHBE", "GEE", "GEIIL", "GENESYS", "GFL", "GICHSGFIN", "GINNIFILAM", "GLAND", "GLAXO", "GLOBUSSPR", "GMMPFAUDLR", "GNA", "GNFC", "GODAWARIPOW", "GODFRYPHLP", "GOLDBEES", "GOPAL", "GPPL", "GRANULES", "GRASIM", "GREAVESCOT", "GRINDWELL", "GSPL", "GUJALKALI", "GUJSTATFIN", "HAL", "HARIOMPIPE", "HARSHA", "HATSUN", "HAVELLS", "HCC", "HCLINFOSY", "HCLTECH", "HDFC", "HDFCBANK", "HDFCLIFE", "HEG", "HEMISPROP", "HERCULES", "HERITGFOOD", "HEROMOTOCO", "HEXATRADEX", "HIMATSEIDE", "HINDALCO", "HINDCONS", "HINDCOPPER", "HINDOILEXP", "HINDPETRO", "HMT", "HONAUT", "HPADHES", "HTMEDIA", "ICICIAMC", "ICICIBANK", "ICICIGI", "ICICIPRULI", "IDEA", "IDFCFIRSTB", "IEX", "IFBIND", "IFGLEXPOR", "IGARASHI", "IGL", "IIFL", "INDIABULL", "INDIANB", "INDIASHELTER", "INDIGO", "INDRAPRASTHA", "INDSIL", "INDUSINDBK", "INDUSTOWER", "INFY", "INGERSOLLRAND", "INNOVACAP", "INNOVAT", "INOXGREEN", "INOXWIND", "INTELLECT", "IRCTC", "IRFC", "ISEC", "ISGEC", "ITI", "J&KBANK", "JAIBALAJI", "JAICORPLTD", "JAMNAAUTO", "JBCHEPHARM", "JBMA", "JFindustries", "JINDALDRLL", "JIOFIN", "JKPAPER", "JKUMAR", "JMFINANCIL", "JOHNCOCKERILL", "JPPOWER", "JSL", "JSWENERGY", "JSWINFRA", "JSWSTEEL", "JUBALAGRI", "JUBILANTPHARMO", "JUBLFOOD", "JUBLINGREA", "JUBLINGRV", "JUNIORBEES", "JUSTDIAL", "JYOTIRESNS", "KABRAEXTRU", "KAJARIACER", "KARUTURI", "KEI", "KESORAMIND", "KEWAL", "KEYSTONEREALTY", "KILBURN", "KILITCH", "KOTAKBANK", "KPRMILL", "KRISHNADEF", "KRONOX", "KTKBANK", "KWALITY", "LACTOSE", "LALPATHLAB", "LANDMARK", "LAOPALA", "LAURUSLABS", "LAXMICHEM", "LICHSGFIN", "LICI", "LINDEINDIA", "LLOYDSENGG", "LTF", "LTTS", "LUMAXTECH", "LYKALABS", "MAHINDRAEPCT", "MANAKSIA", "MANGALAM", "MANINFRA", "MANKIND", "MAPMYINDIA", "MARICO", "MARINEELEC", "MARUTI", "MATRAKAU", "MAXIND", "MCX", "MEDANTA", "MEGHMANORG", "MENONBE", "MERCATOR", "MFSL", "MGL", "MIDHANI", "MOLDTKPAC", "MONARCH", "MOSCHIP", "MOTHERSON", "MPHASIS", "MRPL", "MUKANDLTD", "MUTHOOTFIN", "NAKODA", "NALWASONS", "NATPEROX", "NAUKRI", "NAVINFLUOR", "NAYARAENERGY", "NELCO", "NEOGEN", "NESTLEIND", "NEULANDLAB", "NEXTGEN", "NFL", "NH", "NHPC", "NIPPONLIFE", "NITINSPIN", "NLCINDIA", "NUVAMA", "NUVOCO", "OBEROIRLTY", "OLAELECTRIC", "OLECTRA", "ORICONENT", "ORISSAMINE", "PALRED", "PANACHE", "PARADEEP", "PARSVNATH", "PAYTM", "PCJEWELLER", "PDSL", "PEL", "PENINSULA", "PERSISTENT", "PETRONET", "PGIL", "PHANTOMDIG", "PHOENIXLTD", "PIDILITIND", "PIIND", "PILANIENT", "PLASTIBLND", "PNB", "PODARPIG", "POLYMED", "POLYPLEX", "PONDYOX", "POWERGRID", "POWERINDIA", "PPLPHARMA", "PRAJIND", "PRAKASH", "PRECAM", "PREMEXPLOSIVES", "PREMIERENE", "PREMPLAST", "PRESSMAN", "PRICOLLTD", "PROTEAN", "PRSMJOHNSN", "PSUBNKBEES", "QUESS", "QUICKHEAL", "RADICO", "RADIOCITY", "RAILTEL", "RAIN", "RAJPUTANA", "RAJRATAN", "RALLIS", "RAMKY", "RAMRAT", "RANEHOLDIN", "RATNAMANI", "RATNAVEER", "RAYMOND", "RBLBANK", "RBMINFRA", "RCOM", "REDINGTON", "REFEX", "RELCAPITAL", "RELIANCE", "RELIGARE", "RELINFRA", "RENUKA", "RGL", "RICOAUTO", "RKFORGE", "RKSWAMY", "RPOWER", "RTNINDIA", "RUCHIRA", "RVNL", "SAFARI", "SAGILITY", "SAIL", "SAMMAANCAP", "SANDHAR", "SANKHYA", "SANOFI", "SBICARD", "SBILIFE", "SBIN", "SCHAEFFLER", "SCHAND", "SEJAL", "SENCOGOLD", "SHALBY", "SHANKARA", "SHARDACROP", "SHILPAMED", "SHIVACEM", "SHIVALIK", "SHK", "SHREEGANGA", "SHRIRAMPRP", "SHYAMMETL", "SICAL", "SIGACHI", "SIKA", "SILVERLINE", "SOLARA", "SOLARINDS", "SOLVAY", "SOUTHBANK", "SPACENET", "SPICEJET", "STLTECH", "STOVEC", "STOVEKRAFT", "STRTL", "STYLAM", "SUBEX", "SUDARSCHEM", "SUDITIINDS", "SULA", "SUNPHARMA", "SUNTV", "SURATTWALA", "SURATWWALA", "SUVEN", "SUZLON", "SWANCORP", "SWARAJENG", "SWSOLAR", "SYMPHONY", "TATACONSUM", "TATAELXSI", "TATAINVEST", "TATAMET", "TATAMOTORS", "TATAPOWER", "TATASTEEL", "TATATECH", "TBOTEK", "TCIEXP", "TEAMLEASE", "TECHM", "TECHNO", "TECHNOE", "TEXMACO", "THERMAX", "THIRUMALAI", "THOMASCOOK", "THYROCARE", "TIINDIA", "TIMETECHNO", "TIMEXIND", "TITAGARH", "TITAN", "TNPETRO", "TRENT", "TRIGYN", "TSFINVEST", "TVTODAY", "TWAMEV", "UCAL", "UFOMOVIES", "UJJIVAN", "ULTRAMARINEIG", "UNICHEMLAB", "UNIPARTS", "UNITECH", "UNOMINDA", "UTIAMC", "VADILALIND", "VALOR", "VARROC", "VASCON", "VEEDOL", "VENUSPIPES", "VIDEOCON", "VIPIND", "VISHNU", "VLS", "VOLTAS", "VPRL", "WAAREEENER", "WALCHANDIND", "WELSPUNENT", "WELSPUNLIV", "WENDT", "WESTLIFE", "WHIRLPOOL", "WINDMACH", "WIPRO", "WOCKPHARMA", "YATHARTH", "YESBANK", "ZAGGLE", "ZEEL", "ZEELEARN", "ZFCVINDIA", "ZUARI"]

_cache = {}
_cache_time = 0
CACHE_TTL = 180

def get_ticker_price(sym):
    try:
        t = yf.Ticker(sym)
        fi = t.fast_info
        prev = fi.previous_close or fi.last_price
        price = fi.last_price
        return {
            "p": round(price, 2),
            "c": round(price - prev, 2),
            "pct": round((price - prev) / prev * 100, 2) if prev else 0,
        }
    except:
        return None

def fetch_all():
    global _cache, _cache_time
    if time.time() - _cache_time < CACHE_TTL and _cache:
        return _cache

    prices = {}

    # Indices and FX
    for name, sym in INDICES.items():
        r = get_ticker_price(sym)
        if r:
            prices[name] = r

    # NSE stocks in batches
    for i in range(0, len(NSE_SYMBOLS), 40):
        batch = NSE_SYMBOLS[i:i+40]
        syms_str = " ".join(s + ".NS" for s in batch)
        try:
            tickers = yf.Tickers(syms_str)
            for sym in batch:
                yf_key = sym + ".NS"
                try:
                    fi = tickers.tickers[yf_key].fast_info
                    prev = fi.previous_close or fi.last_price
                    price = fi.last_price
                    if price and price > 0:
                        prices[sym] = {
                            "p": round(price, 2),
                            "c": round(price - prev, 2),
                            "pct": round((price-prev)/prev*100, 2) if prev else 0,
                        }
                except:
                    pass
        except Exception as e:
            print(f"Batch {i} error: {e}")
        time.sleep(0.3)

    _cache = prices
    _cache_time = time.time()
    print(f"Fetched {len(prices)} prices")
    return prices

@app.route("/")
def health():
    return jsonify({"status":"ok","cached":len(_cache),"age":round(time.time()-_cache_time)})

@app.route("/prices")
def get_prices():
    data = fetch_all()
    return jsonify({"prices":data,"ts":int(time.time()),"n":len(data)})

if __name__ == "__main__":
    print("Pre-warming cache...")
    fetch_all()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))
