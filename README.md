# StockVision V5｜中文看盤介面
採用 Streamlit、Plotly、Yahoo Finance，台股快照嘗試證交所公開 MIS 查詢介面。

## 更新已部署網站
把 app.py、engine.py、storage.py、requirements.txt、README.md 和 .streamlit/config.toml 更新到 GitHub 專案根目錄（config.toml 放在 .streamlit 資料夾），Commit changes，Streamlit Cloud 通常自動重新部署。

## 功能
15 個中文分頁：分時圖、價量、K 線、指標、成分股、除權息、折溢價、法人、籌碼、主力、資券、權證、新聞、大戶、基本資料。
分時圖使用 Yahoo Finance 5 分鐘資料；K 線支持滑鼠滾輪縮放；自選股每 5 秒嘗試檢查公開快照。
除權息、基本資料、新聞等使用 Yahoo Finance 提供的資料，可能缺漏。法人、籌碼、主力、資券、大戶、成分股、折溢價、權證是**尚未接入資料來源的預留分頁**，並非完整實作。
**資料並非保證即時**；需獲得合法授權才能提供穩定低延遲報價。頻繁刷新可能受限流影響。
本版不包含券商登入或交易下單功能，不是元大官方產品，也沒有使用其商標或專有設計素材。

## 本機測試
`pip install -r requirements.txt`
`streamlit run app.py`
