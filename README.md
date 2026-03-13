# 股市籌碼儀表板：外資連 5 日買超監測 (家數比例版)

![Stock Dashboard Mockup](https://raw.githubusercontent.com/EasonChang1243/TW_Stock_dashboard/main/preview.png) *(示意圖)*

這是一個自動化的台灣股市籌碼監測工具，專注於追蹤**外資連續 5 個交易日買超**的股票排行與產業分佈。數據邏輯與「玉山證券外資買超排行榜」保持一致。

## 🚀 核心功能
*   **自動化抓取**：使用 FinMind API 每日自動掃描全市場。
*   **精確排行**：鎖定連續 5 日淨買超標的，並依累積買超張數排序 (Top 50)。
*   **產業洞察**：即時呈現前 50 檔個股的產業分佈比例。
*   **響應式面版**：支援手機與電腦瀏覽，現代化深色 UI 設計。
*   **每日更新**：透過 GitHub Actions 於台灣時間每天凌晨 02:00 自動執行並部署。

## 🛠 技術架構
*   **Backend**: Python (FinMind API, Pandas)
*   **Frontend**: HTML5, Vanilla CSS, JavaScript (ES6+)
*   **Visualization**: Apache ECharts
*   **Automation**: GitHub Actions & GitHub Pages

## 快速開始

本專案無需任何 API Key 或複雜設定，直接拉取程式碼即可執行。

### 本地執行
1. 安裝環境：`pip install pandas requests tqdm`
2. 執行抓取：`python fetch_data.py`
3. 開啟網頁：使用 Live Server 或 `python -m http.server` 開啟 `index.html`。

### GitHub 自動化
專案已內建 GitHub Actions，每天下午 2:00（台灣時間）會自動更新資料並部署至 GitHub Pages。

## 📊 資料來源
*   [證交所 (TWSE) 官方數據](https://www.twse.com.tw/)
*   [上櫃中心 (TPEx) 官方數據](https://www.tpex.org.tw/)
*   [玉山證券外資連 5 買超排行](https://www.esunsec.com.tw/tw-rank/b2brwd/page/rank/chip/0003)

---
*本專案數據僅供參考，不構成任何投資建議。*
