# Code Change List

| 修改日期 | 變更版本 | 修改原因 | 對應 GitHub PR / 分段目標 |
| :--- | :--- | :--- | :--- |
| 2026-03-13 | v1.5.1 | 優化數據回溯邏輯，自動跳過官方尚未發布數據的日期，確保 5 日排行穩定性 | `feat: investment-trust-module` |
| 2026-03-13 | v1.5.0 | 修正 UI 選單中文亂碼問題，更新版本標籤，完成投信模組所有介面連動 | `feat: investment-trust-module` |
| 2026-03-13 | v1.4.0 | 新增「投信 (Investment Trust)」買超排行模組，支援法人切換功能 | `feat: investment-trust-module` |
| 2026-03-13 | v1.3.1 | 修正 UI 語系編碼並優化 ETF 產業分類邏輯 (債券/成分股偵測) | `fix: encoding-and-industry` |
| 2026-03-13 | v1.3.0 | 新增 1, 3, 5 日多維度排行切換選單與「顯示更多/收合」功能 | `feat: multi-day-ranking` |
| 2026-03-13 | v1.2.0 | 導入官方直接數據源 (TWSE/TPEx)，解決 API Key 限制並實作詳細產業分類 | `feat: official-data-source` |
| 2026-03-12 | v1.1.0 | 修正除權息數據解析錯誤，加入債券 ETF 支持，實作 5 日累計買超邏輯 | `fix: data-parsing-refinement` |
| 2026-03-12 | v1.0.0 | 專案初始化：建立外資買超排行儀表板、Python 自動抓取腳本與 GitHub Actions | `init: stock-dashboard` |
