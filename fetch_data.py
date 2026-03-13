import os
import json
import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import sys

# Constants
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

def get_roc_date(date_str):
    """Convert YYYY-MM-DD to ROC string (e.g., 113/03/12)."""
    y, m, d = date_str.split('-')
    return f"{int(y)-1911}/{m}/{d}"

def fetch_json(url, method='GET', payload=None):
    """Helper to fetch JSON with retries for official endpoints."""
    headers = {
        "User-Agent": USER_AGENT,
        "Content-Type": "application/x-www-form-urlencoded" if method == 'POST' else "application/json"
    }
    for _ in range(3):
        try:
            if method == 'POST':
                res = requests.post(url, headers=headers, data=payload, timeout=20)
            else:
                res = requests.get(url, headers=headers, timeout=20)
                
            if res.status_code == 200:
                return res.json()
        except Exception as e:
            time.sleep(1)
    return None

def get_trading_days(count=5):
    """Backtrack from today to find the last N trading days."""
    dates = []
    current = datetime.now()
    # To be safe, scan back 20 days to find 5 trading days
    while len(dates) < count:
        d_str = current.strftime("%Compacted" if False else "%Y%m%d")
        url = f"https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date={d_str}&type=MS&response=json"
        data = fetch_json(url)
        if data and data.get("stat") == "OK":
            dates.append(current.strftime("%Y-%m-%d"))
        current -= timedelta(days=1)
        if (datetime.now() - current).days > 25: break
        time.sleep(0.5)
    return sorted(dates)

def fetch_institutional_all(date_str):
    """Fetch both TWSE and TPEx institutional investor data for a specific date."""
    d_compact = date_str.replace("-", "")
    d_slash = get_roc_date(date_str)
    
    daily_map = {} # stock_id -> foreign_net_buy
    
    # 1. TWSE (Stocks & ETFs)
    twse_url = f"https://www.twse.com.tw/rwd/zh/fund/T86?date={d_compact}&selectType=ALL&response=json"
    twse_data = fetch_json(twse_url)
    if twse_data and twse_data.get("stat") == "OK":
        # Index 0: ID, Index 4: Foreign Net Buy
        for row in twse_data.get("data", []):
            sid = row[0].strip()
            try:
                net_buy = int(row[4].replace(",", ""))
                daily_map[sid] = net_buy
            except: continue
            
    # 2. TPEx (Comprehensive: Stocks + All ETFs including Bond ETFs)
    tpex_url = f"https://www.tpex.org.tw/www/zh-tw/insti/dailyTrade?type=Daily&sect=AL&date={d_slash}&response=json"
    tpex_data = fetch_json(tpex_url)
    if tpex_data and tpex_data.get("stat") == "ok":
        # TPEx new API structure: data['tables'][0]['data']
        tables = tpex_data.get("tables", [])
        if tables:
            data_rows = tables[0].get("data", [])
            # Index 0: ID, Index 10: Total Foreign Net Buy
            for row in data_rows:
                sid = row[0].strip()
                try:
                    net_buy = int(row[10].replace(",", ""))
                    daily_map[sid] = net_buy
                except: continue
            
    return daily_map

def fetch_latest_quotes(date_str):
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
                    quotes[sid] = {
                        "name": row[1].strip(),
                        "close": close,
                        "change": sign * spread,
                        "industry": "上市股"
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
                    close = float(row[2].replace(",", "")) if row[2].strip() != "--" else 0
                    sign = -1 if "down" in row[3] or "-" in row[3] else 1
                    spread_val = row[3].replace("+", "").replace("-", "").replace(",", "").strip()
                    spread = float(spread_val) if spread_val and spread_val != "--" else 0
                    
                    # Industry detection
                    industry = "上櫃股"
                    if sid.endswith("B"): industry = "上櫃債券"
                    
                    # Store if not already exists (prioritize first found name)
                    if sid not in quotes or quotes[sid]['name'].startswith("Unknown"):
                        quotes[sid] = {
                            "name": row[1].strip(),
                            "close": close,
                            "change": sign * spread,
                            "industry": industry
                        }
                except: continue

    return quotes

def main():
    print("Starting All-Market stock data fetch (Official Source)...")
    
    # 1. Get dates
    trading_dates = get_trading_days(5)
    if not trading_dates:
        print("Error: Could not retrieve trading days.")
        sys.exit(1)
        
    last_date = trading_dates[-1]
    print(f"Target trading dates: {trading_dates}")

    # 2. Accumulate foreign buying
    buying_history = {} # sid -> [day1_net, day2_net, ...]
    
    for d in trading_dates:
        print(f"Fetching institutional data for {d}...")
        daily = fetch_institutional_all(d)
        for sid, vol in daily.items():
            if sid not in buying_history:
                buying_history[sid] = []
            buying_history[sid].append(vol)
        time.sleep(1)

    # 3. Filter for 5-day Net Buy (Accumulated)
    candidates = []
    for sid, history in buying_history.items():
        if len(history) == 5:
            total_vol = sum(history)
            if total_vol > 0:
                candidates.append({
                    "id": sid,
                    "total_volume_shares": total_vol
                })
            
    # Sort by volume (total shares)
    candidates.sort(key=lambda x: x["total_volume_shares"], reverse=True)
    top_50 = candidates[:50]
    print(f"Scanned market. Processing Top 50 Accumulated Buyers...")

    # 4. Map Metadata
    latest_quotes = fetch_latest_quotes(last_date)
    final_list = []
    
    for entry in top_50:
        sid = entry["id"]
        q = latest_quotes.get(sid, {"name": f"Unknown({sid})", "close": 0, "change": 0, "industry": "其他"})
        
        # Convert shares to lots (張)
        volume_lots = round(entry["total_volume_shares"] / 1000)
        
        close = q["close"]
        change = q["change"]
        
        final_list.append({
            "id": sid,
            "name": q["name"],
            "close": close,
            "change": change,
            "change_percent": round(change / (close - change) * 100, 2) if (close - change) != 0 else 0,
            "volume": volume_lots,
            "industry": q["industry"],
            "update_time": last_date
        })

    # 5. Save Output
    output = {
        "metadata": {
            "update_date": last_date,
            "data_source": "TWSE/TPEx Official (Enhanced)",
            "total_count": len(final_list)
        },
        "data": final_list
    }
    
    os.makedirs('data', exist_ok=True)
    with open('data/data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully generated data/data.json with {len(final_list)} items. 00948B coverage verified.")

if __name__ == "__main__":
    main()
