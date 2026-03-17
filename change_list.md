# Code Change List

| 修改日期 | 變更版本 | 修改原因 | 對應 GitHub PR / 分段目標 |
| :--- | :--- | :--- | :--- |
| 2026-03-17 | v1.9.9.10 | 更新自動化更新排程為台灣時間 04:30 與 16:30 | `feat: adjust-schedule` |
| 2026-03-17 | v1.9.9.4 | 修正 LINE Bot 發送邏輯：切換至 Broadcast API 並加入測試開關 | `feat: line-broadcast-toggle` |
| 2026-03-16 | v1.9.9.3 | 新增 LINE Bot 自動化推送：整合 Messaging API 每日推送 AI 分析與網頁連結 | `feat: line-bot-notification` |
| 2026-03-16 | v1.9.9.2 | 整合 Gemini 3.1 Pro AI 名嘴分析：新增「強中之強」鎖碼個股比對與專屬 UI | `feat: ai-analyst-module` |
| 2026-03-15 | v1.9.2 | 更新自動化更新排程為台灣時間 05:00 與 17:00 | `feat: update-schedule` |
| 2026-03-13 | v1.7.2 | 全面校正 TWSE/TPEx 指項，修復投信排行個股缺失問題 (如 6223) | `fix: comprehensive-indexing` |
| 2026-03-13 | v1.7.1 | 修正投信連買天數異常問題 (校正 TPEx 數據指項為買賣超淨額) | `fix: streak-calculation-indices` |
| 2026-03-13 | v1.7.0 | 連續買超排行模組支援「投信」數據切換，並統一「顯示更多」按鈕樣式 | `feat: trust-consecutive-buys` |
| 2026-03-13 | v1.6.0 | 新增「外資連續買超排行 (Top 50)」模組，包含產業分析圓餅圖 | `feat: foreign-consecutive-buys` |
| 2026-03-13 | v1.5.1 | 優化數據回溯邏輯，自動跳過官方尚未發布數據的日期，確保 5 日排行穩定性 | `feat: investment-trust-module` |
| 2026-03-13 | v1.5.0 | 修正 UI 選單中文亂碼問題，更新版本標籤，完成投信模組所有介面連動 | `feat: investment-trust-module` |
| 2026-03-13 | v1.4.0 | 新增「投信 (Investment Trust)」買超排行模組，支援法人切換功能 | `feat: investment-trust-module` |
| 2026-03-13 | v1.3.1 | 修正 UI 語系編碼並優化 ETF 產業分類邏輯 (債券/成分股偵測) | `fix: encoding-and-industry` |
| 2026-03-13 | v1.3.0 | 新增 1, 3, 5 日多維度排行切換選單與「顯示更多/收合」功能 | `feat: multi-day-ranking` |
| 2026-03-13 | v1.2.0 | 導入官方直接數據源 (TWSE/TPEx)，解決 API Key 限制並實作詳細產業分類 | `feat: official-data-source` |
| 2026-03-12 | v1.1.0 | 修正除權息數據解析錯誤，加入債券 ETF 支持，實作 5 日累計買超邏輯 | `fix: data-parsing-refinement` |
| 2026-03-12 | v1.0.0 | 專案初始化：建立外資買超排行儀表板、Python 自動抓取腳本與 GitHub Actions | `init: stock-dashboard` |
