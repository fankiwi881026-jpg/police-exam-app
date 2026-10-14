# StockVision V4 — 中文看盤

## 特色
- 移除所有均線、布林帶、支撐壓力線及技術評分。
- 日 K 線＋成交量；Plotly 支援滑鼠滾輪縮放、拖曳平移、雙擊重設。
- 自選股行情表，每 5 秒重新執行查詢（僅限頁面開啟期間）。
- 台股優先嘗試 TWSE MIS 公開查詢介面；失敗回退 Yahoo Finance 日 K 收盤價；美股使用 Yahoo Finance 日 K。
- **不保證 5 秒取得新報價**。公開介面可能有延遲、限流、欄位變更或不可用，並非正式授權即時報價。
- SQLite 自選股在 Streamlit 免費雲端重啟後可能遺失；目前不適合多人公開使用。

## GitHub 更新
把 `app.py`、`engine.py`、`storage.py`、`requirements.txt`、`README.md` 更新到原本 GitHub 專案根目錄；並保留 `.streamlit/config.toml`。提交後 Streamlit Cloud 通常會自動重新部署。

## 本機執行
`pip install -r requirements.txt`
`streamlit run app.py`

## 注意
此版本並未進行交易所端點連線實測，需在已部署環境驗證。若要穩定即時行情、逐筆成交、背景警示，應改接正式授權的台美股行情 API，並設計服務端快取與頻率控管。
