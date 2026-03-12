import os
import json
import pandas as pd
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import time

# Load environment variables from .env file
load_dotenv()

def fetch_finmind_raw(dataset, stock_id=None, start_date=None, end_date=None):
    """Direct API call to bypass FinMind package parsing issues."""
    token = os.environ.get("FIND_MY_API", "")
    url = "https://api.finmindtrade.com/api/v4/data"
    params = {
        "dataset": dataset,
        "token": token
    }
    if stock_id: params["data_id"] = stock_id
    if start_date: params["start_date"] = start_date
    if end_date: params["end_date"] = end_date
    
    try:
        res = requests.get(url, params=params)
        data = res.json()
        if data.get("msg") == "success":
            return pd.DataFrame(data.get("data", []))
        else:
            print(f"API Error ({dataset}): {data.get('msg')}")
            return pd.DataFrame()
    except Exception as e:
        print(f"Request Error ({dataset}): {e}")
        return pd.DataFrame()

def fetch_stock_data():
    # 1. Determine the last 5 trading days
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    print(f"Detecting trading dates between {start_date} and {end_date}...")
    sample = fetch_finmind_raw("TaiwanStockInstitutionalInvestorsBuySell", stock_id="2330", start_date=start_date, end_date=end_date)
    
    if sample.empty:
        print("\n[!] 錯誤：無法從 API 獲取資料。原因可能是 API 金鑰次數已達上限。")
        print("[!] 提示：FinMind 免費版每小時有限制次數。請稍後再試，或是直接部署到 GitHub，GitHub Action 有獨立的配額。")
        return
        
    trading_dates = sorted(sample['date'].unique())[-5:]
    print(f"Target trading dates: {trading_dates}")

    if len(trading_dates) < 5:
        print(f"Only found {len(trading_dates)} trading dates.")
        return

    # 2. Daily Batch Fetching
    daily_data = {}
    for date in trading_dates:
        print(f"Fetching institutional data for {date}...")
        df = fetch_finmind_raw("TaiwanStockInstitutionalInvestorsBuySell", start_date=date, end_date=date)
        
        if df.empty:
            continue
            
        # Filter for Foreign Investors
        df_foreign = df[df['name'] == 'Foreign_Investor'].copy()
        if not df_foreign.empty:
            df_foreign['net_buy'] = df_foreign['buy'] - df_foreign['sell']
            daily_data[date] = df_foreign.set_index('stock_id')
        
        time.sleep(1)

    # 3. Process Consecutive Buyers
    if len(daily_data) < 5:
        print("Incomplete daily data.")
        return

    stock_ids_sets = [set(daily_data[d].index) for d in trading_dates]
    qualified_ids = set.intersection(*stock_ids_sets)
    
    consecutive_buyers = []
    for sid in qualified_ids:
        try:
            is_consecutive = True
            total_net_buy = 0
            for date in trading_dates:
                row = daily_data[date].loc[sid]
                net_buy = row['net_buy'] if isinstance(row['net_buy'], (int, float)) else row['net_buy'].sum()
                if net_buy <= 0:
                    is_consecutive = False
                    break
                total_net_buy += net_buy
            
            if is_consecutive:
                consecutive_buyers.append({'id': sid, 'total_volume': int(total_net_buy)})
        except: continue

    consecutive_buyers.sort(key=lambda x: x['total_volume'], reverse=True)
    top_50 = consecutive_buyers[:50]
    print(f"Found {len(consecutive_buyers)} consecutive buyers. Mapping metadata...")

    # 4. Final Metadata Mapping
    stock_info = fetch_finmind_raw("TaiwanStockInfo")
    last_date = trading_dates[-1]
    latest_prices = fetch_finmind_raw("TaiwanStockPrice", start_date=last_date, end_date=last_date)
    
    if not latest_prices.empty:
        latest_prices = latest_prices.set_index('data_id') # TaiwanStockPrice uses data_id for stock_id

    final_results = []
    for entry in top_50:
        sid = entry['id']
        try:
            info = stock_info[stock_info['stock_id'] == sid].iloc[0]
            price = latest_prices.loc[sid] if sid in latest_prices.index else None
            
            if price is not None:
                close = price['close'].iloc[0] if isinstance(price['close'], pd.Series) else price['close']
                spread = price['spread'].iloc[0] if isinstance(price['spread'], pd.Series) else price['spread']
                
                final_results.append({
                    "id": sid,
                    "name": info['stock_name'],
                    "close": float(close),
                    "change": float(spread),
                    "change_percent": round(float(spread) / (float(close) - float(spread)) * 100, 2) if (float(close) - float(spread)) != 0 else 0,
                    "volume": entry['total_volume'],
                    "industry": info['industry_category'],
                    "update_time": last_date
                })
        except: continue

    # 5. Save output
    output = {
        "metadata": {"update_date": last_date, "data_source": "FinMind", "total_count": len(final_results)},
        "data": final_results
    }
    
    os.makedirs('data', exist_ok=True)
    with open('data/data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"Generated data.json with {len(final_results)} stocks.")

if __name__ == "__main__":
    fetch_stock_data()
