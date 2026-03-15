import os
import json
import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import sys

# Constants
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

# Industry Mapping (Official Codes to Names)
TWSE_INDUSTRY_MAP = {
    "01": "水泥工業", "02": "食品工業", "03": "塑膠工業", "04": "紡織纖維", "05": "電機機械",
    "06": "電器電纜", "07": "化學工業", "21": "化學工業", "08": "生技醫療業", "22": "生技醫療業",
    "09": "玻璃陶瓷", "10": "造紙工業", "11": "鋼鐵工業", "12": "橡膠工業", "13": "汽車工業",
    "24": "半導體業", "25": "電腦及週邊設備業", "26": "光電業", "27": "通信網路業",
    "28": "電子零組件業", "29": "電子通路業", "30": "資訊服務業", "31": "其他電子業",
    "32": "建材營造", "33": "航運業", "34": "觀光事業", "37": "觀光餐旅", "35": "金融保險",
    "36": "貿易百貨", "38": "其他", "39": "數位雲端", "40": "運動休閒", "41": "居家生活",
    "42": "綠能環保", "80": "創新板"
}

TPEX_INDUSTRY_MAP = {
    "01": "食品工業", "02": "塑膠工業", "03": "紡織纖維", "04": "電機機械", "05": "電器電纜",
    "06": "化學工業", "07": "玻璃陶瓷", "08": "鋼鐵工業", "09": "橡膠工業", "10": "建材營造",
    "11": "航運業", "13": "金融業", "14": "貿易百貨", "15": "其他", "21": "生技醫療",
    "22": "電腦及週邊設備業", "23": "網路通信業", "24": "電子零組件業", "25": "電子通路業",
    "26": "資訊服務業", "27": "其他電子業", "28": "光電業", "29": "半導體業",
    "30": "文化創意業", "31": "其他電子業", "32": "電子商務", "33": "居家生活",
    "34": "觀光餐旅", "35": "綠能環保", "36": "數位雲端", "37": "運動休閒", "38": "其他"
}

def fetch_industry_mapping():
    """Fetch StockID to IndustryCode mapping from TWSE/TPEx OpenAPI."""
    mapping = {}
    
    # 1. TWSE (Listed)
    twse_url = "https://openapi.twse.com.tw/v1/opendata/t187ap03_L"
    data = fetch_json(twse_url)
    if data:
        for item in data:
            sid = item.get("公司代號", "").strip()
            code = item.get("產業別", "").strip()
            if sid and code:
                mapping[sid] = TWSE_INDUSTRY_MAP.get(code, "上市其他")
                
    # 2. TPEx (OTC) - Fallback to MOPS CSV for reliability
    import csv
    import io
    tpex_csv_url = "https://mopsfin.twse.com.tw/opendata/t187ap03_O.csv"
    try:
        res = requests.get(tpex_csv_url, timeout=10)
        if res.status_code == 200:
            # Handle UTF-8 with BOM
            content = res.content.decode('utf-8-sig')
            f = io.StringIO(content)
            reader = csv.DictReader(f)
            for row in reader:
                sid = row.get("公司代號", "").strip()
                code = row.get("產業別", "").strip()
                if sid and code:
                    mapping[sid] = TPEX_INDUSTRY_MAP.get(code, "上櫃其他")
    except: pass
    
    return mapping

def get_roc_date(date_str):
    """Convert YYYY-MM-DD to ROC string (e.g., 113/03/12)."""
    y, m, d = date_str.split('-')
    return f"{int(y)-1911}/{m}/{d}"

def fetch_json(url, method='GET', payload=None, referer=None):
    """Helper to fetch JSON with retries for official endpoints."""
    # Robust headers to avoid blocks
    base_headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7",
        "X-Requested-With": "XMLHttpRequest"
    }
    
    headers = base_headers.copy()
    if referer:
        headers["Referer"] = referer
    elif "twse.com.tw" in url:
        headers["Referer"] = "https://www.twse.com.tw/zh/fund/T86"
    elif "tpex.org.tw" in url:
        headers["Referer"] = "https://www.tpex.org.tw/zh-tw/mainboard/trading/major-institutional/detail/day.html"

    if method == 'POST':
        headers["Content-Type"] = "application/x-www-form-urlencoded"

    for attempt in range(5):
        try:
            delay = (attempt + 1) * 3  # Increase initial delay
            time.sleep(delay)
            
            if method == 'POST':
                res = requests.post(url, headers=headers, data=payload, timeout=25)
            else:
                res = requests.get(url, headers=headers, timeout=25)
            
            # Check for redirect/block
            if res.status_code == 307 or (res.status_code == 200 and "<html" in res.text.lower()):
                print(f"Warning: Blocked/Redirected on {url} (Attempt {attempt+1})")
                continue
                
            if res.status_code == 200:
                return res.json()
        except Exception as e:
            print(f"Fetch Error ({url}): {e}")
            time.sleep(3)
    return None

def get_trading_days(count=5):
    """Backtrack from today to find the last N trading days that have institutional data."""
    dates = []
    current = datetime.now()
    # To be safe, scan back 35 days to find enough trading days
    while len(dates) < count:
        d_str = current.strftime("%Y%m%d")
        d_dash = current.strftime("%Y-%m-%d")
        
        # Check if T86 (Institutional Data) is available and has data
        url = f"https://www.twse.com.tw/rwd/zh/fund/T86?date={d_str}&selectType=ALL&response=json"
        data = fetch_json(url)
        
        # stat must be OK AND data must be non-empty
        if data and data.get("stat") == "OK" and data.get("data"):
            dates.append(d_dash)
            # Re-fetch both markets to populate cache (this is efficient as it replaces later fetches)
            fetch_institutional_all(d_dash)
            
        current -= timedelta(days=1)
        if (datetime.now() - current).days > 35: break
        time.sleep(0.5)
    return sorted(dates)

# Global Cache to avoid redundant network requests
DATA_CACHE = {}

def fetch_institutional_all(date_str):
    """Fetch both TWSE and TPEx institutional investor data for a specific date."""
    if date_str in DATA_CACHE:
        return DATA_CACHE[date_str]
        
    d_compact = date_str.replace("-", "")
    d_slash = get_roc_date(date_str)
    
    # stock_id -> {"foreign": val, "trust": val}
    daily_map = {}
    
    # 1. TWSE (Stocks & ETFs)
    twse_url = f"https://www.twse.com.tw/rwd/zh/fund/T86?date={d_compact}&selectType=ALL&response=json"
    twse_data = fetch_json(twse_url)
    if twse_data and twse_data.get("stat") == "OK":
        for row in twse_data.get("data", []):
            sid = row[0].strip()
            try:
                foreign = int(row[4].replace(",", ""))
                trust = int(row[10].replace(",", ""))
                daily_map[sid] = {"foreign": foreign, "trust": trust}
            except: continue
            
    # 2. TPEx
    try:
        tpex_url = f"https://www.tpex.org.tw/www/zh-tw/insti/dailyTrade?type=Daily&sect=AL&date={d_slash}&response=json"
        tpex_data = fetch_json(tpex_url)
        if tpex_data and tpex_data.get("stat") == "ok":
            tables = tpex_data.get("tables", [])
            if tables:
                data_rows = tables[0].get("data", [])
                for row in data_rows:
                    sid = row[0].strip()
                    try:
                        foreign = int(row[10].replace(",", ""))
                        trust = int(row[13].replace(",", ""))
                        if sid in daily_map:
                            daily_map[sid]["foreign"] += foreign
                            daily_map[sid]["trust"] += trust
                        else:
                            daily_map[sid] = {"foreign": foreign, "trust": trust}
                    except: continue
    except Exception as e:
        print(f"TPEx Fetch Error for {date_str}: {e}")
    
    DATA_CACHE[date_str] = daily_map
    return daily_map

def fetch_latest_quotes(date_str, industry_mapping):
    """Fetch metadata and price for industry mapping."""
    d_compact = date_str.replace("-", "")
    d_slash = get_roc_date(date_str)
    
    quotes = {} # sid -> {name, close, change, industry}
    
    # 1. TWSE Quotes
    twse_url = f"https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date={d_compact}&type=ALLBUT0999&response=json"
    data = fetch_json(twse_url)
    if data and data.get("tables"):
        # Table with stock data
        stock_table = next((t for t in data["tables"] if "證券代號" in t.get("fields", [])), None)
        if stock_table:
            for row in stock_table["data"]:
                sid = row[0].strip()
                try:
                    close = float(row[8].replace(",", "")) if row[8].strip() != "--" else 0
                    sign = -1 if "down" in row[9] or "-" in row[9] else 1
                    spread = float(row[10].replace(",", "")) if row[10].strip() != "--" else 0
                    
                    # Industry lookup
                    sid_clean = sid.strip()
                    industry = industry_mapping.get(sid_clean, "上市股")
                    
                    # Enhanced Detection
                    if sid_clean.endswith("B"):
                        industry = "債券 ETF"
                    elif sid_clean.startswith("00") and industry == "上市股":
                        industry = "成分股 ETF"
                    
                    quotes[sid_clean] = {
                        "name": row[1].strip(),
                        "close": close,
                        "change": sign * spread,
                        "industry": industry
                    }
                except: continue

    # 2. TPEx Quotes (Fetch multiple categories to ensure coverage)
    tpex_url = "https://www.tpex.org.tw/www/zh-tw/afterTrading/otc"
    for type_code in ['AL', '04']:
        payload = f"date={d_slash}&type={type_code}&id=&response=json"
        data = fetch_json(tpex_url, method='POST', payload=payload)
        if data and data.get("tables"):
            table = data["tables"][0]
            # Fields: [代號, 名稱, 收盤, 漲跌, ...]
            for row in table.get("data", []):
                sid = row[0].strip()
                try:
                    close_val = row[2].replace(",", "").strip()
                    close = float(close_val) if close_val and close_val != "--" else 0
                    
                    # Handle non-numeric change like "除息", "除權"
                    change_str = row[3].strip()
                    sign = -1 if "down" in change_str or "-" in change_str else 1
                    
                    # Try to extract numeric part, or default to 0
                    try:
                        spread_val = change_str.replace("+", "").replace("-", "").replace(",", "").strip()
                        spread = float(spread_val) if spread_val and spread_val != "--" else 0
                    except:
                        spread = 0
                    
                    # Industry detection
                    sid_clean = sid.strip()
                    industry = industry_mapping.get(sid_clean, "上櫃股")
                    
                    # Enhanced Detection
                    if sid_clean.endswith("B"):
                        industry = "債券 ETF"
                    elif sid_clean.startswith("00") and industry == "上櫃股":
                        industry = "成分股 ETF"
                    
                    # Store if not already exists (prioritize first found name)
                    if sid_clean not in quotes or quotes[sid_clean]['name'].startswith("Unknown"):
                        quotes[sid_clean] = {
                            "name": row[1].strip(),
                            "close": close,
                            "change": sign * spread,
                            "industry": industry
                        }
                except: continue

    return quotes

def fetch_us_market():
    """Fetch latest quotes for specific US indices and stocks via Stooq."""
    symbols = {
        "^GSPC": "S&P 500",
        "^NDX": "Nasdaq 100",
        "NVDA.US": "NVIDIA",
        "TSM.US": "TSMC"
    }
    results = []
    
    for sym, name in symbols.items():
        # Stooq CSV format: [Symbol, Date, Time, Open, High, Low, Close, Volume]
        url = f"https://stooq.com/q/l/?s={sym}&f=sd2t2ohlcv&h&e=csv"
        try:
            res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
            if res.status_code == 200:
                lines = res.text.strip().split("\n")
                if len(lines) > 1:
                    data = lines[1].split(",")
                    # Data: Symbol, Date, Time, Open, High, Low, Close, Volume
                    close = float(data[6])
                    results.append({
                        "id": sym,
                        "name": name,
                        "close": close,
                        "update_time": data[1]
                    })
            time.sleep(1)
        except: continue
    return results

def calculate_streaks(trading_dates, investor_type):
    """Calculate consecutive net buy days for all stocks."""
    # Fetch data day by day in reverse
    streaks = {} # sid -> days
    active_stocks = set()
    
    # We need a longer history for streaks, let's try 30 days
    history_dates = get_trading_days(30)
    rev_dates = history_dates[::-1]
    
    if not rev_dates: return []

    # Map to store institutional data for each day
    daily_institutional = {}
    for d in rev_dates:
        daily_institutional[d] = fetch_institutional_all(d)
        time.sleep(0.5)

    # Calculate streaks starting from the most recent day
    latest_day = rev_dates[0]
    latest_data = daily_institutional[latest_day]
    
    for sid, data in latest_data.items():
        if data[investor_type] > 0:
            count = 1
            # Check previous days
            for d in rev_dates[1:]:
                prev_data = daily_institutional.get(d, {})
                if prev_data.get(sid, {}).get(investor_type, 0) > 0:
                    count += 1
                else:
                    break
            streaks[sid] = count
            
    # Sort and take Top 20
    sorted_streaks = sorted(streaks.items(), key=lambda x: x[1], reverse=True)
    return [{"id": k, "days": v} for k, v in sorted_streaks[:20]]

def main():
    print("Starting All-Market stock data fetch (Official Source)...")
    
    # 1. Get dates
    trading_dates = get_trading_days(5)
    if not trading_dates:
        print("Error: Could not retrieve trading days.")
        sys.exit(1)
        
    last_date = trading_dates[-1]
    print(f"Target trading dates: {trading_dates}")

    # 2. Get industry mapping
    print("Fetching industry mapping...")
    industry_mapping = fetch_industry_mapping()

    # 3. Accumulate buying history
    # sid -> {"foreign": [day1, ...], "trust": [day1, ...]}
    buying_history = {}
    
    for d in trading_dates:
        print(f"Fetching institutional data for {d}...")
        daily = fetch_institutional_all(d)
        for sid, data in daily.items():
            if sid not in buying_history:
                buying_history[sid] = {"foreign": [], "trust": []}
            buying_history[sid]["foreign"].append(data["foreign"])
            buying_history[sid]["trust"].append(data["trust"])
        time.sleep(1)

    # 4. Map Metadata
    print("Fetching latest quotes...")
    latest_quotes = fetch_latest_quotes(last_date, industry_mapping)

    # 5. Filter for Multi-Day Rankings (1, 3, 5 Day)
    all_rankings = {
        "foreign": {},
        "trust": {}
    }
    
    intervals = [1, 3, 5]
    investor_types = ["foreign", "trust"]
    
    for inv_type in investor_types:
        for days in intervals:
            # Existing cumulative logic... (kept as is for brevity in this tool call, but ensuring it maps correctly)
            pass 

    # 4. Filter for Multi-Day Rankings (Re-implementing carefully to avoid loss)
    for inv_type in investor_types:
        for days in intervals:
            candidates = []
            for sid, history in buying_history.items():
                recent_history = history[inv_type][-days:]
                if not recent_history: continue
                total_vol = sum(recent_history)
                if total_vol > 0:
                    candidates.append({"id": sid, "total_volume_shares": total_vol})
            
            candidates.sort(key=lambda x: x["total_volume_shares"], reverse=True)
            top_50 = candidates[:50]
            
            final_list = []
            for entry in top_50:
                sid = entry["id"]
                q = latest_quotes.get(sid, {"name": f"Unknown({sid})", "close": 0, "change": 0, "industry": "其他"})
                volume_lots = round(entry["total_volume_shares"] / 1000)
                close = q["close"]
                change = q["change"]
                prev_close = close - change
                change_pct = round(change / prev_close * 100, 2) if prev_close != 0 else 0
                
                final_list.append({
                    "id": sid, "name": q["name"], "close": close, "change": change,
                    "change_percent": change_pct, "volume": volume_lots,
                    "industry": q["industry"], "update_time": last_date
                })
            all_rankings[inv_type][str(days)] = final_list

    # 5. Module 2: Consecutive Buys
    print("Calculating consecutive buy streaks...")
    consecutive_buys = {
        "foreign": calculate_streaks(trading_dates, "foreign"),
        "trust": calculate_streaks(trading_dates, "trust")
    }

    # 6. Module 3: US Markets
    print("Fetching US market indices...")
    us_markets = fetch_us_market()

    # 7. Save Output
    output = {
        "metadata": {
            "update_date": last_date,
            "data_source": "TWSE/TPEx Official (Enhanced)",
            "available_intervals": intervals,
            "investor_types": investor_types
        },
        "rankings": all_rankings,
        "consecutive_buys": consecutive_buys,
        "us_markets": us_markets
    }
    
    os.makedirs('data', exist_ok=True)
    with open('data/data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully generated data/data.json with all modules.")

if __name__ == "__main__":
    main()
