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

def fetch_json(url):
    """Helper to fetch JSON with retries for official endpoints."""
    headers = {"User-Agent": USER_AGENT}
    for _ in range(3):
        try:
            res = requests.get(url, headers=headers, timeout=15)
            if res.status_code == 200:
                data = res.json()
                # TWSE returns 'stat', TPEx returns 'stk_quot_result' or similar
                return data
        except Exception as e:
            time.sleep(1)
    return None

def get_trading_days(count=5):
    """Backtrack from today to find the last N trading days."""
    dates = []
    current = datetime.now()
    # To be safe, scan back 15 days to find 5 trading days (holidays/weekends)
    while len(dates) < count:
        d_str = current.strftime("%Y%m%d")
        url = f"https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date={d_str}&type=MS&response=json"
        data = fetch_json(url)
        if data and data.get("stat") == "OK":
            dates.append(current.strftime("%Y-%m-%d"))
        current -= timedelta(days=1)
        if (datetime.now() - current).days > 20: break # Guard
        time.sleep(0.5) # Avoid rapid fire
    return sorted(dates)

def fetch_institutional_all(date_str):
    """Fetch both TWSE and TPEx institutional investor data for a specific date."""
    d_compact = date_str.replace("-", "")
    d_roc = get_roc_date(date_str)
    
    # 1. TWSE
    twse_url = f"https://www.twse.com.tw/rwd/zh/fund/T86?date={d_compact}&selectType=ALL&response=json"
    twse_data = fetch_json(twse_url)
    
    # 2. TPEx
    tpex_url = f"https://www.tpex.org.tw/web/stock/3profit/3p/3p_result.php?l=zh-tw&d={d_roc}&type=AL&o=json"
    tpex_data = fetch_json(tpex_url)
    
    daily_map = {} # stock_id -> foreign_net_buy
    
    # Process TWSE
    if twse_data and twse_data.get("stat") == "OK":
        # Columns: [證券代號, 證券名稱, 外買進, 外賣出, 外買賣超, ...]
        # Note: Index 4 is "Foreign Investor Net Buy"
        for row in twse_data.get("data", []):
            sid = row[0].strip()
            try:
                # Volume is in string with commas, convert to int
                net_buy = int(row[4].replace(",", ""))
                daily_map[sid] = net_buy
            except: continue
            
    # Process TPEx
    if tpex_data and tpex_data.get("aaData"):
        # Columns: [證券代號, 名稱, 外資買進, 外資賣出, 外資買賣超, ...]
        # Note: Index 10 is typically "Foreign Investor Net Buy" for TPEx JSON
        # Let's check headers for TPEx
        headers = tpex_data.get("iColumns", 15)
        for row in tpex_data.get("aaData", []):
            sid = row[0].strip()
            try:
                # TPEx Index 10 is usually total foreign net buy
                net_buy = int(row[10].replace(",", ""))
                daily_map[sid] = net_buy
            except: continue
            
    return daily_map

def fetch_latest_quotes(date_str):
    """Fetch metadata and price for industry mapping."""
    d_compact = date_str.replace("-", "")
    d_roc = get_roc_date(date_str)
    
    quotes = {} # sid -> {name, close, change, industry}
    
    # 1. TWSE Quotes
    twse_url = f"https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date={d_compact}&type=ALLBUT0999&response=json"
    data = fetch_json(twse_url)
    if data and data.get("tables"):
        # Find the table with stock data (usually index 8 or 9)
        stock_table = next((t for t in data["tables"] if "證券代號" in t.get("fields", [])), None)
        if stock_table:
            # Fields: [代號, 名稱, 成交股數, 成交筆數, 成交金額, 開盤, 最高, 最低, 收盤, 漲跌(+/-), 漲跌價, ...]
            # Change (+/-) is index 9, Spread is index 10
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
                        "industry": "上市股" # We will refine if possible
                    }
                except: continue

    # 2. TPEx Quotes
    tpex_url = f"https://www.tpex.org.tw/web/stock/aftertrading/otc_quotes_no1430/stk_quot_result.php?l=zh-tw&d={d_roc}&o=json"
    data = fetch_json(tpex_url)
    if data and data.get("aaData"):
        for row in data["aaData"]:
            sid = row[0].strip()
            try:
                close = float(row[2].replace(",", "")) if row[2].strip() != "--" else 0
                spread = float(row[3].replace(",", "")) if row[3].strip() != "--" else 0
                quotes[sid] = {
                    "name": row[1].strip(),
                    "close": close,
                    "change": spread, # TPEx JSON already includes sign in spread sometimes
                    "industry": "上櫃股"
                }
            except: continue

    return quotes

def refine_industry(quotes):
    """Optionally fetch industry mapping from TaiwanStockInfo equivalent if needed."""
    # For now, we will use the quotes we have. 
    # To get exact industry categories like "Semicon", we need another official source
    # or a hardcoded map of top stocks.
    return quotes

def main():
    print("Starting automated stock data fetch (Official Source)...")
    
    # 1. Get dates
    trading_dates = get_trading_days(5)
    if not trading_dates:
        print("Error: Could not retrieve trading days.")
        sys.exit(1)
        
    last_date = trading_dates[-1]
    print(f"Target trading dates: {trading_dates}")

    # 2. Accumulate foreign buying
    # stock_id -> [day1_net, day2_net, ...]
    buying_history = {}
    
    for d in trading_dates:
        print(f"Fetching institutional data for {d}...")
        daily = fetch_institutional_all(d)
        for sid, vol in daily.items():
            if sid not in buying_history:
                buying_history[sid] = []
            buying_history[sid].append(vol)
        time.sleep(1) # Be nice to gov servers

    # 3. Filter for 5-day consecutive buy
    candidates = []
    for sid, history in buying_history.items():
        if len(history) == 5 and all(v > 0 for v in history):
            total_vol = sum(history)
            candidates.append({
                "id": sid,
                "total_volume_shares": total_vol
            })
            
    # Sort by volume (total shares)
    candidates.sort(key=lambda x: x["total_volume_shares"], reverse=True)
    top_50 = candidates[:50]
    print(f"Found {len(candidates)} consecutive buyers (All market). Processing Top 50...")

    # 4. Map Metadata
    latest_quotes = fetch_latest_quotes(last_date)
    final_list = []
    
    for entry in top_50:
        sid = entry["id"]
        q = latest_quotes.get(sid, {"name": f"Unknown({sid})", "close": 0, "change": 0, "industry": "其他"})
        
        # Convert shares to lots (張)
        volume_lots = round(entry["id_total_volume_shares" if False else "total_volume_shares"] / 1000)
        
        # Industry mapping helper (Simple fallback)
        industry = q.get("industry", "其他")
        
        close = q["close"]
        change = q["change"]
        
        final_list.append({
            "id": sid,
            "name": q["name"],
            "close": close,
            "change": change,
            "change_percent": round(change / (close - change) * 100, 2) if (close - change) != 0 else 0,
            "volume": volume_lots,
            "industry": industry,
            "update_time": last_date
        })

    # 5. Save Output
    output = {
        "metadata": {
            "update_date": last_date,
            "data_source": "TWSE/TPEx Official",
            "total_count": len(final_list)
        },
        "data": final_list
    }
    
    os.makedirs('data', exist_ok=True)
    with open('data/data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully generated data/data.json with {len(final_list)} stocks. Process complete.")

if __name__ == "__main__":
    main()
