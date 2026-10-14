# StockVision V7 — 自適應一頁式看盤
## 安裝
`pip install -r requirements.txt`
`streamlit run app.py`
## 更新 GitHub
將 `app.py`、`engine.py`、`symbols.py`、`storage.py`、`requirements.txt`、`header.png` 與 `.streamlit/config.toml` 上傳到原 Repository，Commit 後等待雲端部署。
## 特點
單頁式圖表與動態資料分頁、縮小設定圖示、螢光粉漲／螢光綠跌、中文控制、查詢股票顯示名稱、最新可取得價格與行情時間、分時／日週月 K、自選股分類。
沒有可用資料的成分股、法人、籌碼、主力、資券、權證、大戶等分頁**不會出現**；除權息、基本資料、財務報表、新聞只有資料存在才顯示。
每 5 秒重跑價格面板，但 Yahoo 1 分鐘報價快取最多 5 分鐘，並非逐筆即時行情。要真正逐筆更新需授權行情供應商。長歷史與報表取得可能耗時；手機使用響應式佈局但超長表格仍可能在其區塊內橫向捲動。
目前未在公開網路部署驗證；請先在自己的 Streamlit Cloud 測試。SQLite 自選股資料在免費雲端可能遺失，正式使用需雲端資料庫。
