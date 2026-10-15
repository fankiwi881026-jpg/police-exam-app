# 警察四等內軌｜行政警察備考系統

響應式靜態網站，支援手機與電腦。內建 7 題**自編示範題**（非歷屆真題），六科分類、抽題、答題解析、錯題重練、收藏、統計、法規官方連結與 JSON 題庫匯入。

## 啟用跨裝置同步

1. 在 https://supabase.com/ 建立 Project。
2. 進入 SQL Editor，貼上 `schema.sql` 全部執行。
3. Project Settings / API（或 Connect）複製 Project URL 及 **publishable key / anon key** 到 `config.js`。**絕對不要使用 secret/service_role key。**
4. 在 Authentication > URL Configuration 設定 Site URL 為 GitHub Pages 網址；Redirect URLs 也加入相同網址。Email 確認與密碼重設郵件需在 Supabase Authentication 設定。此版本登入支援 Email+密碼，密碼重設郵件會寄出，但重設密碼頁面尚未實作，建議先在 Supabase 後台協助重設。
5. GitHub 新建公開 repository，上傳本資料夾所有檔案，在 Settings > Pages 選 Deploy from branch / main / root。等待 GitHub Pages 提供網址。
6. 網站開啟「帳號設定」註冊、驗證並登入。登入後的**新作答**與收藏會寫入 Supabase，並在其他裝置顯示。
7. 題庫匯入需要管理員權限：到 Supabase Authentication > Users 複製管理員 UID，在 SQL Editor 執行 `insert into public.admin_users(user_id) values ('UID');`。

> 注意：未登入期間保存在瀏覽器的紀錄不會自動合併進雲端；登入後以雲端資料為準。請先啟用雲端再開始正式累積進度。公開網站的使用者可自行註冊，若只想私人使用，請在 Supabase 關閉公開註冊並手動邀請帳號。

## 題庫格式

上傳 UTF-8 JSON 陣列，例如：

```json
[
  {
    "subject":"警察法規概要",
    "stem":"示範問題？",
    "options":["選項A","選項B","選項C","選項D"],
    "answer":1,
    "explanation":"答案為 B 的理由。",
    "source":"自編示範題（非歷屆真題）",
    "law":"警察職權行使法"
  }
]
```

`answer` 使用 0、1、2、3 對應 A、B、C、D。正式考題請標註考試年度、題號、科目、官方來源並核對正確答案。避免匯入未經授權的商業題庫。一次最多 2000 題。

## 注意事項與限制

- 此為第一版原型，尚未收錄完整歷屆真題，也沒有自動抓取最新法條全文。法規頁連向法務部官方資料庫，正式備考請以最新公告為準。
- Supabase 需要網路連線；未設定雲端時使用本機模式，清除瀏覽器資料可能遺失紀錄。
- 雲端管理員權限由 RLS 管控；普通使用者無法新增雲端題庫。請自行定期備份資料庫。
- 使用本機 HTTP server 預覽（例如 `python -m http.server 8000`），不要直接雙擊 HTML 以 file:// 開啟。
- 目前「收藏」可於測驗結果操作，測驗頁選「只練收藏」。
