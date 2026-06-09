import os
import json
import sys
sys.path.append('.')
from fetch_data import fetch_json

url = "https://www.twse.com.tw/rwd/zh/fund/BFI82U?response=json"
data = fetch_json(url)
print(json.dumps(data, ensure_ascii=False, indent=2))
