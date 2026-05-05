import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

def generate_analysis():
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not found")
        return

    # Load data
    try:
        with open('data/data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading data: {e}")
        return

    ai_context = data.get("ai_context", {})
    if not ai_context:
        print("Error: ai_context not found in data.json. Run fetch_data.py first.")
        return

    # Prepare prompt components
    super_strong = ", ".join([f"{s['name']}({s['id']}, {s['industry']})" for s in ai_context.get("super_strong", [])])
    top_industries = ", ".join([f"{i['name']}({i['count']} 檔)" for i in ai_context.get("top_industries", [])])
    us_indices = ", ".join([f"{m['id']}: {m['change']}%" for m in ai_context.get("market_summary", {}).get("us_indices", [])])
    
    # Format institutional summary
    inst_summary_data = data.get("institutional_summary", [])
    inst_summary_text = ""
    if inst_summary_data:
        lines = []
        for item in inst_summary_data:
            lines.append(f"  {item['name']}: 買進 {item['buy']}, 賣出 {item['sell']}, 買賣差額 {item['net']}")
        inst_summary_text = "\n".join(lines)
    else:
        inst_summary_text = "無數據"

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash') # Switched to Flash for cost efficiency

    system_prompt = """
你現在是一名精通台股籌碼分析、語氣犀利且富有感染力的「股市名嘴型」AI 策略顧問。
你的任務是根據提供的數據，產出具有洞察力、口語化且充滿張力的每日點評。

[角色規則]
1. 開場白規範：必須以「各位投資朋友大家好，我是你的 AI 投資戰友！今天的盤勢你看懂了嗎？外資雖然在跑，但這幾隻股票法人的手抓得可緊了...」作為開場。
2. 語氣要求：模仿股市名嘴，語句要短、要有爆發力，避免呆板的學術用語。
3. 字數：限制在 400 字以內，適合手機快速瀏覽。
4. 結構要求：
   - 【名嘴點評】：用極具張力的口吻分析美股與大盤關聯，點出目前市場的「恐慌」或「貪婪」。
   - 【法人風向球】：解讀三大法人的買賣超金額，判斷目前的資金風向（外資與投信是聯手還是對作？）。
   - 【籌碼密碼】：從產業佔比告訴投資人資金是在避險還是進攻。
   - 【強中之強推薦】：針對 Super_Strong_List 的個股，用激昂的語氣說明為何法大戶非買不可。
   - 【明日錦囊】：給出犀利的短線操作建議。
"""

    user_prompt = f"""
[最新數據數據]
- 美股指數表現: {us_indices}
- 三大法人買賣金額統計 (元):
{inst_summary_text}
- 法人買超產業分佈 (前 3 大): {top_industries}
- 「強中之強」鎖碼股 (1日與5日買超交集): {super_strong if super_strong else "今日無顯著鎖碼股"}

請開始你的分析表演！
"""

    print("Generating AI analysis...")
    try:
        response = model.generate_content([system_prompt, user_prompt])
        analysis_text = response.text

        output = {
            "analysis": analysis_text,
            "update_time": data["metadata"]["update_date"]
        }

        os.makedirs('data', exist_ok=True)
        with open('data/ai_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print("Successfully generated data/ai_analysis.json")
    except Exception as e:
        print(f"Error generating content: {e}")

if __name__ == "__main__":
    generate_analysis()
