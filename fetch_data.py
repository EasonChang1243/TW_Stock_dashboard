import os
import json
import pandas as pd
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import time
import sys

# Load environment variables from .env file
load_dotenv()

def fetch_finmind_raw(dataset, stock_id=None, start_date=None, end_date=None):
    """Direct API call to FinMind."""
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
            # Silent return for per-stock loop to avoid log clutter
            return pd.DataFrame()
    except:
        return pd.DataFrame()

def fetch_stock_data():
    # 1. Determine the last 5 trading days
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    print(f"Detecting trading dates...")
    # Get 2330 as a proxy for trading days
    sample = fetch_finmind_raw("TaiwanStockInstitutionalInvestorsBuySell", stock_id="2330", start_date=start_date, end_date=end_date)
    
    if sample.empty:
        print("\n[!] 錯誤：無法獲取交易日期。請檢查 API Key 是否有效。")
        sys.exit(1)
        
    trading_dates = sorted(sample['date'].unique())[-5:]
    last_date = trading_dates[-1]
    print(f"Target trading dates: {trading_dates}")

    # 2. Get prioritized stock list
    # Free tier cannot batch fetch, so we prioritize the most important stocks
    stock_info = fetch_finmind_raw("TaiwanStockInfo")
    if stock_info.empty:
        print("Failed to fetch stock info.")
        sys.exit(1)
    
    # Prioritize 'twse' (listed) and 'tpex' (OTC)
    # To stay within free limit (roughly 300-600/hr), we scan the first 350 stocks
    # This usually covers major moves and ETFs shown in ESUN rank.
    priority_list = stock_info[stock_info['type'].isin(['twse', 'tpex'])]['stock_id'].tolist()[:350]
    print(f"Scanning top {len(priority_list)} prioritized stocks...")

    results = []
    processed_count = 0

    for sid in priority_list:
        try:
            # Fetch last 5 days institutional buy/sell in ONE call per stock
            df = fetch_finmind_raw("TaiwanStockInstitutionalInvestorsBuySell", stock_id=sid, start_date=trading_dates[0], end_date=last_date)
            
            if df.empty:
                continue
            
            # Filter for foreign investor
            df_foreign = df[df['name'] == 'Foreign_Investor'].copy()
            if len(df_foreign['date'].unique()) < 5:
                continue
            
            # Sort by date and check consecutive net buy
            df_foreign = df_foreign.sort_values('date')
            df_foreign['net_buy'] = df_foreign['buy'] - df_foreign['sell']
            
            # Check if all 5 days are positive
            if (df_foreign['net_buy'] > 0).all():
                total_volume = int(df_foreign['net_buy'].sum())
                results.append({
                    'id': sid,
                    'total_volume': total_volume,
                    'last_df': df_foreign.iloc[-1]
                })

            processed_count += 1
            if processed_count % 50 == 0:
                print(f"Processed {processed_count} stocks...")
            
            # Short sleep to avoid rapid fire blocking
            time.sleep(0.1)
                
        except Exception as e:
            continue

    # 3. Sort and pick Top 50
    results.sort(key=lambda x: x['total_volume'], reverse=True)
    top_50 = results[:50]
    print(f"Found {len(results)} consecutive buyers. Mapping details...")

    # 4. Fetch Price for the winners (if not already fetched)
    # Mapping metadata
    final_output = []
    
    # Helper to mapping stock info quickly
    info_map = stock_info.set_index('stock_id')

    for item in top_50:
        sid = item['id']
        try:
            # Get stock info, ensuring we get scalars even if there are duplicates
            info = info_map.loc[sid]
            name = info['stock_name']
            industry = info['industry_category']
            
            # If multiple entries exist, pandas returns a Series; take the first value
            if isinstance(name, pd.Series): name = name.iloc[0]
            if isinstance(industry, pd.Series): industry = industry.iloc[0]

            # Use TaiwanStockPrice for latest price
            price_df = fetch_finmind_raw("TaiwanStockPrice", stock_id=sid, start_date=last_date, end_date=last_date)
            
            close = 0
            spread = 0
            if not price_df.empty:
                # Use float() to ensure it's not a numpy type
                close = float(price_df.iloc[0]['close'])
                spread = float(price_df.iloc[0]['spread'])

            final_output.append({
                "id": str(sid),
                "name": str(name),
                "close": close,
                "change": spread,
                "change_percent": round(spread / (close - spread) * 100, 2) if (close - spread) != 0 else 0,
                "volume": int(item['total_volume']),
                "industry": str(industry),
                "update_time": str(last_date)
            })
        except:
            continue

    # 5. Save output
    output_json = {
        "metadata": {"update_date": last_date, "data_source": "FinMind (Prioritized)", "total_count": len(final_output)},
        "data": final_output
    }
    
    os.makedirs('data', exist_ok=True)
    with open('data/data.json', 'w', encoding='utf-8') as f:
        json.dump(output_json, f, ensure_ascii=False, indent=2)
    print(f"Generated data.json with {len(final_output)} stocks. Scan complete.")

if __name__ == "__main__":
    fetch_stock_data()
