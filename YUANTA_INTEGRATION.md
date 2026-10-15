# 元大 SPARK API 串接規劃（尚未連線）
目前 StockVision V9 是**可運行的券商風格看盤介面**，但尚未接入元大 SPARK。畫面採用獨立設計，並非元大官方產品。

## 申請
1. 到 https://www.yuanta.com.tw/file-repository/content/API/page/index.html
2. 依官網指引簽署 API 風險預告書。
3. 下載測試程式、完成測試、上傳紀錄。
4. 聯絡元大營業員開通；確認是否需臨櫃。
5. 開通後下載官方 Python 元件，依官方文件配置 .NET 8 等環境。
6. 先在私人 Windows 電腦上驗證**唯讀行情訂閱**，不加入下單指令。

## 未來架構
SPARK 官方元件（本機／受控伺服器） -> 唯讀行情服務 -> StockVision 網頁。
**不要**將帳號密碼、憑證、電子交易密碼寫入 GitHub 或聊天內容。
未經授權，勿公開轉播券商即時行情給其他使用者。
官方說明：https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/index.html
