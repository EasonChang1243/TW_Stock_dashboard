import os
import json
import requests
from dotenv import load_dotenv

def send_line_message():
    load_dotenv()
    
    # 1. Configuration
    line_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    line_user_id = os.getenv("LINE_USER_ID")
    dashboard_url = "https://easonchang1243.github.io/TW_Stock_dashboard/"
    
    if not line_token or not line_user_id:
        print("Error: LINE_CHANNEL_ACCESS_TOKEN or LINE_USER_ID not found in .env")
        return

    # 2. Load AI Analysis
    try:
        with open('data/ai_analysis.json', 'r', encoding='utf-8') as f:
            ai_data = json.load(f)
            analysis_text = ai_data.get("analysis", "今日無分析數據。")
            update_time = ai_data.get("update_time", "N/A")
    except Exception as e:
        print(f"Error loading ai_analysis.json: {e}")
        return

    # 3. Construct Message
    message_content = f"📢 【股市名嘴每日點評】 ({update_time})\n\n"
    message_content += f"🔗 儀表板連結：{dashboard_url}\n\n"
    message_content += "--------------------\n"
    message_content += analysis_text

    # LINE Messaging API has a 2000 character limit per text message.
    # Our AI analysis is max 400 words (~1000-1500 chars), so it should fit.
    if len(message_content) > 2000:
        message_content = message_content[:1997] + "..."

    # 4. Send via LINE Messaging API (Broadcast Message)
    url = "https://api.line.me/v2/bot/message/broadcast"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {line_token}"
    }
    payload = {
        "messages": [
            {
                "type": "text",
                "text": message_content
            }
        ]
    }

    print(f"Sending message to LINE (User: {line_user_id})...")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        if response.status_code == 200:
            print("Successfully sent LINE notification!")
        else:
            print(f"Failed to send LINE message: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error calling LINE API: {e}")

if __name__ == "__main__":
    send_line_message()
