警察特考備考網站｜完整上傳版

這個 ZIP 已包含完整網站檔案，無須自行合併 app.js 或 questions.js。

GitHub 上傳方式：
1. 先備份目前 GitHub 專案與題庫 JSON。
2. 將這份 ZIP 解壓縮（不要直接把 ZIP 當網站檔上傳）。
3. 開啟 https://github.com/fankiwi881026-jpg/police-exam-app
4. 選 Add file → Upload files。
5. 把解壓後「資料夾內」所有檔案拖曳到上傳區（index.html 必須在儲存庫根目錄，不能多包一層資料夾）。
6. 在 Commit changes 確認更新；等待 GitHub Pages 發布，再重新整理網站。

本版功能：
- 法規查閱：可開啟全國法規資料庫入口，部分法規須自行搜尋。
- 題庫統計：依網站目前載入題目統計年度、等別、科目。
- JSON 匯入：檢查格式、相同 ID、題幹與選項完全重複。

限制：
- 相似題、法規適用性、答案正確性尚未自動 AI 審核。
- 未登入匯入的題庫保存在目前瀏覽器，並非跨裝置同步。
- 若登入使用 Supabase，仍須確認 questions 資料表欄位與權限設定，尤其 year、level 欄位；目前雲端匯入不保留 level。
- 請勿將 Supabase service_role 密鑰放在 config.js 或公開 GitHub。
