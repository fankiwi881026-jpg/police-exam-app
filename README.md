# StockVision 台股／美股技術分析平台

## 安裝（Windows / macOS / Linux）

1. 安裝 Python 3.11 或 3.12。
2. 將 ZIP 解壓縮，在 `stockvision` 資料夾開啟終端機。
3. 建立虛擬環境：

   Windows PowerShell：
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   streamlit run app.py
   ```
   macOS/Linux：
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   streamlit run app.py
   ```
4. 瀏覽器開啟終端機顯示的網址（通常是 http://localhost:8501）。

## 部署成網頁

1. 將 `app.py`、`engine.py`、`storage.py`、`requirements.txt` 上傳到私有 GitHub 儲存庫。
2. 在 Streamlit Community Cloud 建立 App，選擇該儲存庫，主程式設為 `app.py`。
3. 部署完成後可用手機開啟提供的網址。

**重要：** 此範例使用本機 SQLite。雲端部署時檔案可能因重新啟動而遺失，且不具備使用者隔離；正式多人使用前，應改用 PostgreSQL/Supabase、加入登入與每位使用者的資料權限。不要把含個人資料的 SQLite 檔提交 GitHub。

## 資料與限制

- 行情透過 yfinance / Yahoo Finance 公開來源取得；可能延遲、限流、停用或不完整，不保證即時或商業使用授權。
- 台股上市常用 `.TW`，上櫃常用 `.TWO`；美股例如 `AAPL`。
- 自動更新是指載入頁面或按重新抓取時更新，15 分鐘快取；沒有後台排程或推播。
- 支撐壓力使用 120 根 K 線、左右各 3 根的已確認 pivot，依 1.2% 相近價位聚類。不是成交量分布計算。
- 評分：站上 MA20/60/120 各 15；多頭排列 20；放量上漲 15；布林中上軌 10；MA20 上彎且站上 10，滿分 100。屬啟發式規則，不是上漲機率。
- 回測策略：收盤站上 MA20 且 MA20 > MA60 > MA120 時產生訊號，次日開盤換倉，計算開盤至次日開盤報酬。最後一天未平倉部位沒有另計終端平倉成本。未包含滑價、稅務、股息再投入；使用調整後價格。
- SQLite 僅適合單機示範；警示依最新收盤價的門檻狀態觸發，不是跨越事件偵測，僅在警示頁執行檢查。
- 條件選股僅掃描手動輸入的最多 20 檔股票。

## 開發注意

正式實盤前需加上交易所授權行情、可靠背景工作排程、通知服務、登入權限、資料庫備份、交易成本模型及多期間樣本外驗證。

## 不安裝 Python，直接取得網址（手機也可以）
1. 用瀏覽器登入 GitHub，建立一個新的 Repository。
2. 將本資料夾內的 `app.py`、`engine.py`、`storage.py`、`requirements.txt` 上傳到 Repository 根目錄。
3. 前往 https://share.streamlit.io/ 並使用 GitHub 帳號登入，選擇 **Create app**。
4. 選取剛建立的 Repository、分支 `main`，主程式路徑 `app.py`，按 Deploy。
5. 部署成功後平台會提供可分享的 HTTPS 網址；手機直接開啟即可，不必安裝 Python。

**限制：** 本版本沒有自建帳號登入功能；Streamlit Cloud 可用 GitHub 管理部署，但不等於每位訪客有獨立帳號。SQLite 自選股與警示在免費雲端環境可能因重啟遺失且未隔離，不應用於公開多人正式服務。請勿公開含私人資料的資料庫。
**行情：** Yahoo Finance 日 K 並非保證即時；5 分鐘選項只是頁面檢查提示，無背景通知，並不代表每 5 分鐘會取得最新成交價。若要秒級行情與背景警示，需合法授權即時報價 API、伺服器排程與通知服務。

## V3 改善
- 深藍色高對比配色，請連同 `.streamlit/config.toml` 上傳至 GitHub（GitHub 可建立 `.streamlit` 資料夾）。
- 自選股顯示最新收盤價、前一交易日漲跌、漲跌幅、資料日期、MA20、技術評分。
- 點選「更新全部自選股行情」會清除快取再抓取；免費來源並非保證即時。
- 重新上傳 app.py、engine.py、storage.py、requirements.txt、README.md 並提交，雲端通常會自動重新部署。
