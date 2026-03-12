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

## 📦 安裝與設定

### 本地開發
1.  **安裝依賴**：
    ```bash
    pip install -r requirements.txt
    ```
2.  **設定環境變數**：
    在根目錄建立 `.env` 檔案並填入您的 FinMind API Key：
    ```env
    FIND_MY_API=您的_API_KEY
    ```
3.  **執行抓取**：
    ```bash
    python3 fetch_data.py
    ```
4.  **開啟網頁**：
    ```bash
    python3 -m http.server
    # 開啟 http://localhost:8000
    ```

### GitHub 自動化設定
1.  **Repository Secret**：前往 GitHub 設定，新增一個名為 `FIND_MY_API` 的 Secret，內容填入您的 API Key。
2.  **GitHub Pages**：在 Settings -> Pages 中，將 Source 設定為 `GitHub Actions`。
3.  **權限設定**：在 Settings -> Actions -> General 中，確認 `Workflow permissions` 已選取 `Read and write permissions`。

## 📊 資料來源
*   [FinMind 數據服務](https://finmindtrade.com/)
*   [玉山證券外資連 5 買超排行](https://www.esunsec.com.tw/tw-rank/b2brwd/page/rank/chip/0003)

---
*本專案數據僅供參考，不構成任何投資建議。*
